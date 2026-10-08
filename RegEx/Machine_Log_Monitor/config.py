import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

DB_SCHEMA = os.getenv("DB_SCHEMA")

MACHINE_LOG_FILE = BASE_DIR / "logs" / "machine.log"
REPORT_FILE = BASE_DIR / "reports" / "machine_error_report.csv"
