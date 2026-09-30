import json
import logging
import pathlib
import sys
from logging.handlers import RotatingFileHandler

BASE_DIR = pathlib.Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "app.log"
class JsonFormatter(logging.Formatter):

    def format(self, record):
        log_data = {
            "timestamp": record.created, 
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(
                record.exc_info
            )

        return json.dumps(log_data)

def configure_logging():

    logger = logging.getLogger("application")
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    formatter = JsonFormatter()

    file_handler = RotatingFileHandler(
        filename=LOG_FILE,
        maxBytes=2 * 1024,    
        backupCount=10,      
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.propagate = False

    return logger

logger = configure_logging()

logger.info("Application started")
logger.info("Processing request")
logger.warning("Something requires attention")

for i in range(100):
    logger.info(
        "Testing centralized logging - message number %s",i,
    )