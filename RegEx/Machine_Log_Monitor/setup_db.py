import logging
import psycopg2
from config import DB_NAME, DB_SCHEMA
from db import get_connection
from logging_config import configure_logging

logger = logging.getLogger(__name__)
TABLE_NAME = "machine_errors"

def create_database():
    connection = get_connection(database="postgres")
    connection.autocommit = True

    try:
        with connection.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE {DB_NAME}")
            logger.info("Database %s created", DB_NAME)
    except psycopg2.errors.DuplicateDatabase:
        logger.info("Database %s already exists", DB_NAME)
    finally:
        connection.close()


def create_schema():
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(f"""
                CREATE SCHEMA IF NOT EXISTS {DB_SCHEMA}
                """)
        connection.commit()
        logger.info("Schema %s created or verified", DB_SCHEMA)
    except Exception:
        connection.rollback()
        logger.exception("Failed to create schema %s", DB_SCHEMA)
        raise
    finally:
        connection.close()


def create_table():
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {DB_SCHEMA}.{TABLE_NAME} (
                    id SERIAL PRIMARY KEY,
                    machine_id VARCHAR(50) NOT NULL,
                    timestamp TIMESTAMPTZ NOT NULL,
                    unix_timestamp BIGINT NOT NULL,
                    error_message TEXT NOT NULL,
                    CONSTRAINT unique_machine_error
                    UNIQUE (machine_id, timestamp, error_message)
                )
                """)
        connection.commit()
        logger.info("Table %s.%s created or verified", DB_SCHEMA, TABLE_NAME)
    except Exception:
        connection.rollback()
        logger.exception("Failed to create table %s.%s", DB_SCHEMA, TABLE_NAME)
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    configure_logging()
    create_database()
    create_schema()
    create_table()
