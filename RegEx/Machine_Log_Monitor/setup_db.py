from config import DB_NAME, DB_SCHEMA
from db import get_connection
import psycopg2

TABLE_NAME = "machine_errors"

def create_database():
    connection = get_connection(database="postgres")
    connection.autocommit = True

    try:
        with connection.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE {DB_NAME}")
            print(f"Database '{DB_NAME}' created.")

    except psycopg2.errors.DuplicateDatabase:
        print(f"Database '{DB_NAME}' already exists.")

    finally:
        connection.close()

def create_schema():
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                CREATE SCHEMA IF NOT EXISTS {DB_SCHEMA}
                """
            )

        connection.commit()

        print(
            f"Schema '{DB_SCHEMA}' created/verified."
        )

    except Exception as e:
        connection.rollback()

        print(
            f"Failed to create schema "
            f"'{DB_SCHEMA}': {e}"
        )

    finally:
        connection.close()

def create_table():
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {DB_SCHEMA}.{TABLE_NAME} (
                    id SERIAL PRIMARY KEY,
                    machine_id VARCHAR(50) NOT NULL,
                    timestamp TIMESTAMPTZ NOT NULL,
                    unix_timestamp BIGINT NOT NULL,
                    error_message TEXT NOT NULL,

                    CONSTRAINT unique_machine_error
                    UNIQUE (machine_id,timestamp,error_message)
                )
                """
            )

        connection.commit()

        print(
            f"Table '{DB_SCHEMA}.{TABLE_NAME}' "
            f"created/verified."
        )

    except Exception as e:
        connection.rollback()

        print(
            f"Failed to create table "
            f"'{DB_SCHEMA}.{TABLE_NAME}': {e}"
        )

    finally:
        connection.close()

if __name__ == "__main__":
    create_database()
    create_schema()
    create_table()