import logging
import sys
import time
from pathlib import Path

import db

BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "cron_jobs.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

logger = logging.getLogger(__name__)

def insert_job():
    try:
        db.insert_timestamp()
        logger.info("Insert job completed successfully")

    except Exception:
        logger.exception("Insert job failed")
        raise

def partition_job():
    try:
        now = int(time.time())

        _, current_end = db.get_window_bounds(now)

        db.create_partition(current_end)

        logger.info("Partition job completed successfully")

    except Exception:
        logger.exception("Partition job failed")
        raise

def main():
    if len(sys.argv) != 2:
        logger.error(
            "Invalid usage. Use: "
            "python cron_jobs.py insert "
            "or python cron_jobs.py partition"
        )
        sys.exit(1)

    job = sys.argv[1]

    if job == "insert":
        insert_job()

    elif job == "partition":
        partition_job()

    else:
        logger.error("Unknown job: %s", job)
        sys.exit(1)

if __name__ == "__main__":
    main()