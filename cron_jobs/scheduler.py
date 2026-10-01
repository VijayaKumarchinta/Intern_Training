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

    create_partition(unix_ts)

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

def create_partition(unix_ts):
    start_time = time.perf_counter()

    current_partition_start = (
        unix_ts // TEN_MINUTES
    ) * TEN_MINUTES

    current_partition_end = (
        current_partition_start + TEN_MINUTES
    )

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            current_partition_name = (
                f"{TABLE_NAME}_{current_partition_start}"
            )

            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS
                {DB_SCHEMA}.{current_partition_name}
                PARTITION OF {DB_SCHEMA}.{TABLE_NAME}
                FOR VALUES FROM (%s) TO (%s)
                """,
                (
                    current_partition_start,
                    current_partition_end,
                ),
            )

        connection.commit()

        partition_logger.info(
            "Partition verified | current=%s",
            current_partition_name,
        )

    except Exception:
        connection.rollback()

        partition_logger.exception(
            "Failed to create partitions"
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

    schedule.every(1).minute.do(
        run_timestamp_job
    )

    scheduler_logger.info(
        "Job registered: insert_timestamp | interval=1m"
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