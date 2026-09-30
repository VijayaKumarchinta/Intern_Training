from config import DB_NAME, DB_SCHEMA
from db import get_connection
import psycopg2

TABLE_NAME = "timestamp_data"

def create_database():
    connection = get_connection(database="postgres")
    connection.autocommit = True

    try:
        with connection.cursor() as cursor:
            try:
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
                f"CREATE SCHEMA IF NOT EXISTS {DB_SCHEMA}"
            )

        connection.commit()

        print(f"Schema '{DB_SCHEMA}' created/verified.")

    finally:
        connection.close()

def create_table():
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {DB_SCHEMA}.{TABLE_NAME} (
                    id BIGSERIAL,
                    unix_ts BIGINT NOT NULL
                )
                PARTITION BY RANGE (unix_ts);
                """
            )

        connection.commit()

        print(
            f"Table '{DB_SCHEMA}.{TABLE_NAME}' "
            "created/verified."
        )

    finally:
        connection.close()

def initialize_database():
    create_database()
    create_schema()
    create_table()

if __name__ == "__main__":
    initialize_database()