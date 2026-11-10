import argparse
import logging
import signal
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_PROJECT_ROOT / "backend"))

from config.settings import load_settings  # noqa: E402
from replay.worker import ReplayWorker  # noqa: E402

def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s :: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--interval", type=float, default=None)
    parser.add_argument(
        "--parquet",
        type=Path,
        default=_PROJECT_ROOT
        / "data"
        / "processed"
        / "line_speed_30_normalized.parquet",
    )
    args = parser.parse_args()

    _configure_logging()
    settings = load_settings()
    worker = ReplayWorker(
        settings=settings,
        parquet_path=args.parquet,
        interval_override=args.interval,
    )

    def _handle_signal(signum, frame):
        logging.getLogger(__name__).info("Signal %s received, stopping", signum)
        worker.enqueue_command({"type": "stop"})

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    published = worker.run(limit=args.limit)
    print(f"Replay finished. Published {published} record(s).")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
