import argparse
import logging
import signal
import sys
import threading
import time
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_PROJECT_ROOT / "backend"))

from config.settings import load_settings  
from ingestion.worker import IngestionWorker 

def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s :: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest LINE_30 telemetry.")
    parser.add_argument("--limit", type=int, default=None,
                        help="Stop after accepting N messages (default: run until SIGINT)")
    parser.add_argument("--timeout", type=float, default=None,
                        help="Give up after N seconds (default: none)")
    args = parser.parse_args()

    _configure_logging()
    settings = load_settings()
    worker = IngestionWorker(settings=settings)

    thread = threading.Thread(target=worker.run, name="ingestion-worker", daemon=True)
    thread.start()

    started = time.monotonic()
    try:
        while thread.is_alive():
            if args.limit is not None and worker.stats.accepted >= args.limit:
                break
            if args.timeout is not None and time.monotonic() - started >= args.timeout:
                logging.getLogger(__name__).warning("Timeout after %.1fs", args.timeout)
                break
            time.sleep(0.2)
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("SIGINT received")
    finally:
        worker.stop()
        thread.join(timeout=5.0)

    stats = worker.stats
    print(
        f"Ingestion finished. received={stats.received} "
        f"accepted={stats.accepted} rejected={stats.rejected}"
    )
    if stats.last_rejection_reason:
        print(f"Last rejection: {stats.last_rejection_reason}")

    if args.limit is not None and stats.accepted < args.limit:
        print(f"FAIL: expected at least {args.limit} accepted, got {stats.accepted}")
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
