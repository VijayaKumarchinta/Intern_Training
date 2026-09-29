from datetime import datetime
import logging
import os
import time
from logging.handlers import RotatingFileHandler

class TimeAndSizeRotatingHandler(RotatingFileHandler):
    def __init__(
        self,
        filename,
        max_bytes,
        backup_count,
        interval=1,
        encoding="utf-8",
    ):
        self.interval = interval
        self.next_rollover_time = time.time() + interval

        super().__init__(
            filename=filename,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding=encoding,
        )

    def shouldRollover(self, record):
        if time.time() >= self.next_rollover_time:
            return 1
        
        if self.maxBytes <= 0:
            return 0

        if self.stream is None:
            self.stream = self._open()

        self.stream.seek(0, os.SEEK_END)
        current_size = self.stream.tell()

        message = self.format(record)
        message_size = len(
            (message + self.terminator).encode(
                self.encoding or "utf-8"
            )
        )

        return current_size + message_size >= self.maxBytes

    def doRollover(self):
        super().doRollover()
        self.next_rollover_time = time.time() + self.interval

log_file = (
    f"logs/app_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
)

os.makedirs("logs", exist_ok=True)

handler = TimeAndSizeRotatingHandler(
    filename=log_file,
    max_bytes=1024,
    backup_count=10,
    interval=10,
    encoding="utf-8",
)

formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

handler.setFormatter(formatter)

logger = logging.getLogger("application")
logger.setLevel(logging.INFO)
logger.addHandler(handler)
logger.propagate = False

logger.info("Application started")
logger.info("Processing request")
logger.warning("Something requires attention")

for i in range(100):
    logger.info(f"Testing log rotation - message number {i}")