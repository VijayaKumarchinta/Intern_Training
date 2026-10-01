import logging
import time

import schedule

import logging_config

from config import DB_SCHEMA, TABLE_NAME, TEN_MINUTES
from db import get_connection

logging_config.configure_logging()

scheduler_logger = logging.getLogger("scheduler")
timestamp_logger = logging.getLogger("timestamp")
partition_logger = logging.getLogger("partition")

def insert_current_timestamp():
    start_time = time.perf_counter()
    unix_ts = int(time.time())

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                INSERT INTO {DB_SCHEMA}.{TABLE_NAME} (unix_ts)
                VALUES (%s)
                """,
                (unix_ts,),
            )

        connection.commit()

        timestamp_logger.info(
            "Timestamp inserted | unix_ts=%s",
            unix_ts,
        )

    except Exception:
        connection.rollback()

        timestamp_logger.exception(
            "Failed to insert timestamp | unix_ts=%s",
            unix_ts,
        )

        raise

    finally:
        connection.close()

        duration = time.perf_counter() - start_time

        timestamp_logger.info(
            "Job completed | duration=%.3fs",
            duration,
        )

def create_partition(partition_start):
    start_time = time.perf_counter()

    partition_end = partition_start + TEN_MINUTES
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            partition_name = (
                f"{TABLE_NAME}_{partition_start}"
            )

            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS
                {DB_SCHEMA}.{partition_name}
                PARTITION OF {DB_SCHEMA}.{TABLE_NAME}
                FOR VALUES FROM (%s) TO (%s)
                """,
                (
                    partition_start,
                    partition_end,
                ),
            )

        connection.commit()

        partition_logger.info(
            "Partition verified | partition=%s | from=%s | to=%s",
            partition_name,
            partition_start,
            partition_end,
        )

    except Exception:
        connection.rollback()

        partition_logger.exception(
            "Failed to create partition"
        )

        raise

    finally:
        connection.close()

        duration = time.perf_counter() - start_time

        partition_logger.info(
            "Job completed | duration=%.3fs",
            duration,
        )

def run_timestamp_job():
    scheduler_logger.info(
        "Executing job: insert_timestamp"
    )

    insert_current_timestamp()

def run_scheduler():
    scheduler_logger.info("Scheduler started")

    partition_start = int(time.time())

    create_partition(partition_start)

    def run_partition_job():
        nonlocal partition_start

        partition_start += TEN_MINUTES
        create_partition(partition_start)

    schedule.every(1).minute.do(
        run_timestamp_job
    )

    schedule.every(10).minutes.do(
        run_partition_job
    )

    scheduler_logger.info(
        "Job registered: insert_timestamp | interval=1m"
    )

    scheduler_logger.info(
        "Job registered: create_partition | interval=10m"
    )

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    try:
        run_scheduler()

    except KeyboardInterrupt:
        scheduler_logger.info(
            "Scheduler stopped by user"
        )

    except Exception:
        scheduler_logger.exception(
            "Scheduler stopped because of an unexpected error"
        )
        raise