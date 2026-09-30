import logging
import os
import time
from pathlib import Path

import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "sql_python.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

logger = logging.getLogger(__name__)

load_dotenv(BASE_DIR / ".env")

DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_SCHEMA = os.getenv("DB_SCHEMA", "public")

TABLE_NAME = "readings"
WINDOW_SIZE = 600

def get_connection(database):
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=database,
        user=DB_USER,
        password=DB_PASSWORD,
    )

def create_database():
    connection = None
    try:
        connection = get_connection("postgres")
        connection.autocommit = True

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (DB_NAME,),
            )

            if cursor.fetchone():
                logger.info("Database already exists: %s", DB_NAME)
                return

            cursor.execute(
                sql.SQL("CREATE DATABASE {}").format(
                    sql.Identifier(DB_NAME)
                )
            )

            logger.info("Database created: %s", DB_NAME)

    except psycopg2.Error:
        logger.exception("Database creation failed")
        raise

    finally:
        if connection:
            connection.close()

def create_table():
    connection = None

    try:
        connection = get_connection(DB_NAME)

        with connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    sql.SQL(
                        """
                        CREATE SCHEMA IF NOT EXISTS {};

                        CREATE TABLE IF NOT EXISTS {}.{} (
                            id BIGSERIAL,
                            unix_ts BIGINT NOT NULL,
                            PRIMARY KEY (id, unix_ts)
                        )
                        PARTITION BY RANGE (unix_ts);
                        """
                    ).format(
                        sql.Identifier(DB_SCHEMA),
                        sql.Identifier(DB_SCHEMA),
                        sql.Identifier(TABLE_NAME),
                    )
                )

        logger.info(
            "Table verified: %s.%s",
            DB_SCHEMA,
            TABLE_NAME,
        )

    except psycopg2.Error:
        logger.exception("Table creation failed")
        raise

    finally:
        if connection:
            connection.close()


def get_window_bounds(unix_ts):
    start = (unix_ts // WINDOW_SIZE) * WINDOW_SIZE
    end = start + WINDOW_SIZE

    return start, end

def create_partition(unix_ts):
    start, end = get_window_bounds(unix_ts)

    partition_name = f"{TABLE_NAME}_p_{start}"

    connection = None

    try:
        connection = get_connection(DB_NAME)

        with connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    sql.SQL(
                        """
                        CREATE TABLE IF NOT EXISTS {}.{}
                        PARTITION OF {}.{}
                        FOR VALUES FROM (%s) TO (%s)
                        """
                    ).format(
                        sql.Identifier(DB_SCHEMA),
                        sql.Identifier(partition_name),
                        sql.Identifier(DB_SCHEMA),
                        sql.Identifier(TABLE_NAME),
                    ),
                    (start, end),
                )

        logger.info(
            "Partition verified: %s [%s, %s)",
            partition_name,
            start,
            end,
        )

    except psycopg2.Error:
        logger.exception(
            "Partition creation failed: %s",
            partition_name,
        )
        raise

    finally:
        if connection:
            connection.close()


def insert_timestamp():
    unix_ts = int(time.time())

    connection = None

    try:
        connection = get_connection(DB_NAME)

        with connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    sql.SQL(
                        """
                        INSERT INTO {}.{} (unix_ts)
                        VALUES (%s)
                        """
                    ).format(
                        sql.Identifier(DB_SCHEMA),
                        sql.Identifier(TABLE_NAME),
                    ),
                    (unix_ts,),
                )

        logger.info("Inserted unix_ts=%s", unix_ts)

    except psycopg2.Error:
        logger.exception(
            "Insert failed for unix_ts=%s",
            unix_ts,
        )
        raise

    finally:
        if connection:
            connection.close()

def initialize():
    
    create_database()
    create_table()
    now = int(time.time())
    current_start, current_end = get_window_bounds(now)
    create_partition(current_start)
    create_partition(current_end)

    logger.info("Database initialization completed")

if __name__ == "__main__":
    initialize()