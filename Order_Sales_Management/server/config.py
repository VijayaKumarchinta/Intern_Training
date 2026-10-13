import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / '.env')

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "machine_monitor_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_SCHEMA = os.getenv("DB_SCHEMA", "sales_schema")

APP_HOST = "127.0.0.1"
APP_PORT = 8001
DEBUG = False
LOG_LEVEL = "INFO"

BASE_DIR = Path(__file__).parent
CLIENT_DIR = BASE_DIR.parent / "client"
LOGS_DIR = BASE_DIR / "logs"


def validate_config():
    if not DB_PASSWORD:
        raise RuntimeError("DB_PASSWORD is not set in .env file")
    return True
