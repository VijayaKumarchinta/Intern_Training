import csv
import logging
import os
import psycopg2
from config import DB_CONFIG, REPORT_FILE

logger = logging.getLogger(__name__)

SELECT_QUERY = """
SELECT
    machine_id,
    timestamp,
    unix_timestamp,
    error_message
FROM machine_errors
ORDER BY timestamp;
"""

def generate_report():
    connection = None

    try:
        connection = psycopg2.connect(**DB_CONFIG)

        with connection.cursor() as cursor:
            cursor.execute(SELECT_QUERY)
            rows = cursor.fetchall()

        os.makedirs("reports", exist_ok=True)

        with open(REPORT_FILE,"w",newline="",encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([
                "Machine ID",
                "Timestamp",
                "Unix Timestamp",
                "Error Message"
            ])
            writer.writerows(rows)
            
        logger.info("Report generated: %s (%d records)",REPORT_FILE,len(rows))

    except psycopg2.Error as error:
        logger.error("Failed to generate report: %s",error)

    except OSError as error:
        logger.error("Failed to write report: %s",error)

    finally:
        if connection:
            connection.close()