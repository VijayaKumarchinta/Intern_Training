import logging
from config import MACHINE_LOG_FILE

logger = logging.getLogger(__name__)

def read_machine_logs():
    try:
        with open(MACHINE_LOG_FILE, "r", encoding="utf-8") as file:
            lines = file.readlines()

        logger.info("Read %d lines from machine log",len(lines))
        return lines

    except FileNotFoundError:
        logger.error("Machine log file not found: %s",MACHINE_LOG_FILE)
        return []

    except OSError as error:
        logger.error("Failed to read machine log: %s",error)
        return []