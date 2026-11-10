import sys
import threading
import time
from pathlib import Path
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_PROJECT_ROOT / 'backend'))
from config.settings import load_settings
from ingestion.worker import IngestionWorker
from publisher.replay import ReplayPublisher
EXPECTED = 5
TIMEOUT_SECONDS = 10.0

def main() -> int:
    settings = load_settings()
    worker = IngestionWorker(settings=settings)
    worker_thread = threading.Thread(target=worker.run, name='ingestion-worker', daemon=True)
    worker_thread.start()
    time.sleep(0.5)
    publisher = ReplayPublisher(settings=settings, parquet_path=_PROJECT_ROOT / 'data' / 'processed' / 'line_speed_30_normalized.parquet', interval_seconds=0.3, limit=EXPECTED, pacing=True)
    publisher.run()
    started = time.monotonic()
    while time.monotonic() - started < TIMEOUT_SECONDS:
        if worker.stats.accepted >= EXPECTED:
            break
        time.sleep(0.2)
    worker.stop()
    worker_thread.join(timeout=5.0)
    stats = worker.stats
    print(f'OK: received={stats.received} accepted={stats.accepted} rejected={stats.rejected}')
    if stats.accepted != EXPECTED:
        print(f'FAIL: expected {EXPECTED} accepted, got {stats.accepted}')
        if stats.last_rejection_reason:
            print(f'Last rejection: {stats.last_rejection_reason}')
        return 1
    records = worker.drain(max_items=EXPECTED)
    timestamps = [r.event_timestamp for r in records]
    print('First 5 accepted event timestamps:')
    for ts in timestamps[:5]:
        print(f'  {ts}')
    return 0
if __name__ == '__main__':
    raise SystemExit(main())
