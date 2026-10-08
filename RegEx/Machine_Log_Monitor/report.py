import csv
import logging

from config import REPORT_FILE
from db import get_connection

logger = logging.getLogger(__name__)


SELECT_QUERY = """
    SELECT
        machine_id,
        log_timestamp,
        error_message
    FROM machine_errors
    ORDER BY log_timestamp;
"""


def generate_report():

    connection = None

    try:

        connection = get_connection()

        with connection.cursor() as cursor:

            cursor.execute(SELECT_QUERY)

            rows = cursor.fetchall()

        REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)

        with open(REPORT_FILE, "w", newline="", encoding="utf-8") as file:

            writer = csv.writer(file)

            writer.writerow(["Machine ID", "Timestamp", "Error Message"])

            writer.writerows(rows)

        logger.debug("Report generated: %s | Records=%d", REPORT_FILE, len(rows))

    except Exception:

        logger.exception("Failed to generate report")

        raise

    finally:

        if connection:
            connection.close()
