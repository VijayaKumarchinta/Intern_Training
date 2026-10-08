import csv
import logging
from pathlib import Path

from config import DB_SCHEMA, REPORT_FILE
from db import get_connection

logger = logging.getLogger(__name__)


SELECT_QUERY = """
    SELECT
        machine_id,
        timestamp,
        error_message
    FROM {schema}.machine_errors
    ORDER BY timestamp;
"""
SELECT_QUERY = SELECT_QUERY.format(schema=DB_SCHEMA)


def generate_report():

    connection = None

    try:

        connection = get_connection()

        with connection.cursor() as cursor:

            cursor.execute(SELECT_QUERY)

            rows = cursor.fetchall()

        report_file = Path(REPORT_FILE)
        report_file.parent.mkdir(parents=True, exist_ok=True)

        with report_file.open("w", newline="", encoding="utf-8") as file:

            writer = csv.writer(file)

            writer.writerow(["Machine ID", "Timestamp", "Error Message"])

            writer.writerows(rows)

        logger.info("Report generated: %s | Records=%d", report_file, len(rows))

    except Exception:

        logger.exception("Failed to generate report")

        raise

    finally:

        if connection:
            connection.close()
