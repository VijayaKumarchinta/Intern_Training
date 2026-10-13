"""
Logging configuration for Order & Sales Management Application.
Uses RotatingFileHandler + console output with consistent format.
"""
import logging
import sys
from pathlib import Path

from Order_Sales_Management.server.config import LOG_LEVEL, LOGS_DIR


def configure_logging():
    """Configure application-wide logging."""
    # Ensure logs directory exists
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    log_file = LOGS_DIR / "app.log"
    max_bytes = 10 * 1024 * 1024  # 10 MB
    backup_count = 5

    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(LOG_LEVEL)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(LOG_LEVEL)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(LOG_LEVEL)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Suppress noisy loggers
    logging.getLogger('psycopg2').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.WARNING if not DEBUG else logging.INFO)

    logging.info("Logging configured: level=%s, file=%s", LOG_LEVEL, log_file)
