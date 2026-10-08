from db import get_connection
from config import DB_SCHEMA

def store_errors(errors):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            for error in errors:
                cursor.execute(
                    f"""
                    INSERT INTO {DB_SCHEMA}.machine_errors(machine_id, timestamp, unix_timestamp, error_message)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT ON CONSTRAINT unique_machine_error
                    DO NOTHING
                    """,
                    (
                        error["machine_id"],
                        error["timestamp"],
                        error["unix_timestamp"],
                        error["error_message"],
                    )
                )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()