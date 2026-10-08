from db import get_connection

def store_errors(errors):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            for error in errors:
                cursor.execute(
                    """
                    INSERT INTO machine_errors
                    (machine_id, timestamp, unix_timestamp, error_message)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (machine_id, timestamp, error_message)
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