"""Replays the sample CSV as a live feed (timestamps shifted to 'now').

Use it to demo the dashboard without a broker:
    python simulate_feed.py            # real-time, 1 source-second per second
    python simulate_feed.py --speed 5  # 5x faster
Stop with Ctrl+C.
"""
import argparse
import csv
import json
import time
from collections import defaultdict
from pathlib import Path

from config import DATA_DIR
from database.connection import db
from services.live_ingest import live_ingest

DEFAULT_CSV = DATA_DIR / "csv_files_28_03_2025" / "all_topics_20250328-114500.csv"


def load_seconds(path):
    by_second = defaultdict(lambda: defaultdict(list))
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            from datetime import datetime
            sec = int(datetime.fromisoformat(row["timestamp"]).timestamp())
            by_second[sec][row["machine_name"]].append(
                {"ST": row["sensor_tag"], "TS": sec, "VR": [float(row["sensor_value"])]}
            )
    return by_second


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default=str(DEFAULT_CSV))
    parser.add_argument("--speed", type=float, default=1.0)
    args = parser.parse_args()

    data = load_seconds(Path(args.csv))
    seconds = sorted(data)
    print(f"Replaying {len(seconds)} source seconds at {args.speed}x. Ctrl+C to stop.")
    while True:
        for i, sec in enumerate(seconds):
            started = time.monotonic()
            for machine, items in data[sec].items():
                now = int(time.time())  # stamp with the real clock so any --speed stays 'live'
                shifted = [dict(it, TS=now) for it in items]
                live_ingest.ingest(machine, json.dumps(shifted))
            gap = (seconds[i + 1] - sec) if i + 1 < len(seconds) else 1
            time.sleep(max(0, gap / args.speed - (time.monotonic() - started)))
        print("Sample finished, restarting from the beginning.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        db.close_pool()
