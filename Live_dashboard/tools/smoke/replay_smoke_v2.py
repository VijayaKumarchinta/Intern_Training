from __future__ import annotations

import sys
import time
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_PROJECT_ROOT / "backend"))

from config.settings import load_settings  # noqa: E402
from replay.worker import ReplayWorker  # noqa: E402


def main() -> int:
    settings = load_settings()
    parquet = (
        _PROJECT_ROOT
        / "data"
        / "processed"
        / "line_speed_30_normalized.parquet"
    )
    worker = ReplayWorker(
        settings=settings,
        parquet_path=parquet,
        interval_override=0.3,
    )
    started = time.monotonic()
    published = worker.run(limit=10)
    elapsed = time.monotonic() - started
    print(
        f"OK: published {published} record(s) in {elapsed:.2f}s "
        f"(session={worker.state.replay_session_id[:8]}..., "
        f"cycle={worker.state.replay_cycle})"
    )
    if published != 10:
        print(f"FAIL: expected 10 records, published {published}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
