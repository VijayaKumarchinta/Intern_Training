import logging
import time

from apscheduler.schedulers.background import BlockingScheduler

import logging_config

from config import DB_SCHEMA, TABLE_NAME, TEN_MINUTES
from db import get_connection


logging_config.configure_logging()

scheduler_logger = logging.getLogger("scheduler")
timestamp_logger = logging.getLogger("timestamp")
partition_logger = logging.getLogger("partition")

def insert_current_timestamp():
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
        timestamp_logger.info("Timestamp inserted | unix_ts=%s",unix_ts,)

    except Exception:
        connection.rollback()
        timestamp_logger.exception("Failed to insert timestamp | unix_ts=%s",unix_ts,)

    finally:
        connection.close()

def create_partition(unix_ts):
    current_partition_start = (unix_ts // TEN_MINUTES) * TEN_MINUTES
    current_partition_end = (current_partition_start + TEN_MINUTES)

    next_partition_start = current_partition_end
    next_partition_end = (next_partition_start + TEN_MINUTES)

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

            next_partition_name = (f"{TABLE_NAME}_{next_partition_start}")

            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS
                {DB_SCHEMA}.{next_partition_name}
                PARTITION OF {DB_SCHEMA}.{TABLE_NAME}
                FOR VALUES FROM (%s) TO (%s)
                """,
                (
                    next_partition_start,
                    next_partition_end,
                ),
            )

        connection.commit()
        partition_logger.info("Partitions verified | current=%s | next=%s",current_partition_name,next_partition_name,)

    except Exception:
        connection.rollback()
        partition_logger.exception("Failed to create partitions")

    finally:
        connection.close()

def run_timestamp_job():
    insert_current_timestamp()

def run_partition_job():
    create_partition(int(time.time()))

def run_scheduler():
    scheduler_logger.info("Scheduler started")

    create_partition(int(time.time()))
    scheduler = BlockingScheduler()

    scheduler.add_job(
        run_timestamp_job,
        "cron",
        minute="*/1",
        id="insert_timestamp",
    )

    scheduler.add_job(
        run_partition_job,
        "cron",
        minute="*/10",
        id="create_partition",
    )

    scheduler_logger.info("Jobs registered")

    scheduler.start()


if __name__ == "__main__":
    try:
        run_scheduler()

    except KeyboardInterrupt:
        scheduler_logger.info("Scheduler stopped by user")

    except Exception:
        scheduler_logger.exception("Scheduler stopped because of an unexpected error")