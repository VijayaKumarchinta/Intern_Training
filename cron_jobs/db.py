import psycopg2

import logging

from config import (
        DB_HOST,
        DB_PORT,
        DB_NAME,
        DB_USER,
        DB_PASSWORD
)

def get_connection(self, database=None):
        try:
            return psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                database=database or DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
            )
        except psycopg2.Error as error:
            logging.exception("Database connection failed")
            raise psycopg2.DatabaseError(f"Database connection failed: {error}") from error