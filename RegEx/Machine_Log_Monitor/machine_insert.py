import logging

from db import get_connection
from config import DB_SCHEMA

logger = logging.getLogger(__name__)


def store_errors(errors):
    """Store errors, ignoring records with an existing machine, timestamp, and message."""
    connection = get_connection()
    inserted = 0
    ignored_duplicates = 0

    try:

        with connection.cursor() as cursor:

            for error in errors:

                cursor.execute(
                    f"""
                    INSERT INTO {DB_SCHEMA}.machine_errors
                    (
                        machine_id,
                        timestamp,
                        unix_timestamp,
                        error_message
                    )
                    VALUES (%s, %s, %s, %s)

                    ON CONFLICT ON CONSTRAINT unique_machine_error
                    DO NOTHING
                    """,
                    (
                        error["machine_id"],
                        error["timestamp"],
                        error["unix_timestamp"],
                        error["error_message"],
                    ),
                )

                if cursor.rowcount == 1:
                    inserted += 1
                else:
                    ignored_duplicates += 1

        connection.commit()
        logger.info(
            "Stored %d error(s); ignored %d duplicate(s)",
            inserted,
            ignored_duplicates,
        )

    except Exception:
        connection.rollback()
        logger.exception("Failed to store machine errors")
        raise

    finally:
        connection.close()
