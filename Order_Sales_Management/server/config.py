"""
Configuration for Order & Sales Management Application.
Fail-fast validation ensures the application doesn't start with bad config.
"""
import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).parent
CLIENT_DIR = BASE_DIR.parent / "client"
REPORTS_DIR = BASE_DIR / "reports"
LOGS_DIR = BASE_DIR / "logs"

# Database configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "order_sales_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# Application configuration
APP_HOST = os.getenv("APP_HOST", "127.0.0.1")
APP_PORT = int(os.getenv("APP_PORT", "8001"))
DEBUG = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Order status constants
ORDER_STATUS_PENDING = "pending"
ORDER_STATUS_PROCESSING = "processing"
ORDER_STATUS_SHIPPED = "shipped"
ORDER_STATUS_DELIVERED = "delivered"
ORDER_STATUS_CANCELLED = "cancelled"
ORDER_STATUS_RETURNED = "returned"

VALID_ORDER_STATUSES = {
    ORDER_STATUS_PENDING,
    ORDER_STATUS_PROCESSING,
    ORDER_STATUS_SHIPPED,
    ORDER_STATUS_DELIVERED,
    ORDER_STATUS_CANCELLED,
    ORDER_STATUS_RETURNED,
}

# Valid transitions: status -> set of allowed next statuses
ORDER_STATUS_TRANSITIONS = {
    ORDER_STATUS_PENDING: {ORDER_STATUS_PROCESSING, ORDER_STATUS_CANCELLED},
    ORDER_STATUS_PROCESSING: {ORDER_STATUS_SHIPPED, ORDER_STATUS_CANCELLED},
    ORDER_STATUS_SHIPPED: {ORDER_STATUS_DELIVERED, ORDER_STATUS_RETURNED},
    ORDER_STATUS_DELIVERED: {ORDER_STATUS_RETURNED},
    ORDER_STATUS_CANCELLED: set(),  # Final state
    ORDER_STATUS_RETURNED: set(),    # Final state
}

# Tax rate (configurable percentage)
DEFAULT_TAX_RATE = float(os.getenv("DEFAULT_TAX_RATE", "10.0"))

# Default discount for eligible orders (percentage)
DEFAULT_DISCOUNT_RATE = float(os.getenv("DEFAULT_DISCOUNT_RATE", "0.0"))


def validate_config():
    """Validate required configuration at startup."""
    errors = []

    if not DB_PASSWORD:
        errors.append("DB_PASSWORD is not set")

    if DB_PORT < 1 or DB_PORT > 65535:
        errors.append(f"Invalid DB_PORT: {DB_PORT}")

    if LOG_LEVEL not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
        errors.append(f"Invalid LOG_LEVEL: {LOG_LEVEL}")

    if errors:
        raise RuntimeError("Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors))

    return True
