"""v1 — Size-only baseline.

The standard-library starting point: RotatingFileHandler with no time
logic at all. This is the "either/or" handler from §0 of
code_explanation.md — the blind spot here is that a quiet app can keep
a stale app.log forever, because nothing ever rotates on time.

Backups: app.log -> app.log.1 -> ... -> app.log.<N>  (sequence-numbered)
"""

import logging
import os

from logging.handlers import RotatingFileHandler

os.makedirs("logs", exist_ok=True)

handler = RotatingFileHandler(
    filename="logs/app.log",
    maxBytes=1024,
    backupCount=10,
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
