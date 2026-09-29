import logging
import time

from logging.handlers import RotatingFileHandler
from pathlib import Path

from config import LOG_LEVEL

BASE_DIR = Path(__file__).resolve().parent.parent

LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "machine_sensor_api.log"

LOG_FILE_MAX_BYTES = 10_000_000
LOG_BACKUP_COUNT = 5

logger = logging.getLogger("machine_sensor_api")
logger.setLevel(LOG_LEVEL)
logger.propagate = False

if not logger.handlers:
    formatter = logging.Formatter("%(asctime)sZ | %(levelname)s | %(name)s | %(message)s")
    formatter.converter = time.gmtime

    console_handler = logging.StreamHandler()
    console_handler.setLevel(LOG_LEVEL)
    console_handler.setFormatter(formatter)

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=LOG_FILE_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(LOG_LEVEL)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
