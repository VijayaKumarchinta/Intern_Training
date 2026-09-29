import logging
import time

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "machine_sensor_api.log"

logger = logging.getLogger("machine_sensor_api")
logger.setLevel(logging.INFO)
logger.propagate = False

if not logger.handlers:
    formatter = logging.Formatter("%(asctime)sZ | %(levelname)s | %(name)s | %(message)s")
    formatter.converter = time.gmtime

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
