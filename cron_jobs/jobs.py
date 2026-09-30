import time

from config import DB_SCHEMA
from db import get_connection

TABLE_NAME = "timestamp_data"
TEN_MINUTES = 600

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

        print(f"Inserted Unix timestamp: {unix_ts}")

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def create_partition():
    current_ts = int(time.time())

    partition_start = (current_ts // TEN_MINUTES) * TEN_MINUTES
    partition_end = partition_start + TEN_MINUTES

    partition_name = f"{TABLE_NAME}_{partition_start}"

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS
                {DB_SCHEMA}.{partition_name}
                PARTITION OF {DB_SCHEMA}.{TABLE_NAME}
                FOR VALUES FROM (%s) TO (%s)
                """,
                (partition_start, partition_end),
            )

        connection.commit()

        print(
            f"Partition '{partition_name}' "
            f"created/verified."
        )

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()