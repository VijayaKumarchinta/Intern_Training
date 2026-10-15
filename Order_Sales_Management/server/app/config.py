import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

load_dotenv(os.path.join(BASE_DIR, ".env"))


def configure_logging(app):
    app.logger.handlers = []

    _log_dir = os.path.join(BASE_DIR, "logs")
    os.makedirs(_log_dir, exist_ok=True)

    _formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    _console = logging.StreamHandler(sys.stdout)
    _console.setFormatter(_formatter)

    _file = RotatingFileHandler(
        os.path.join(_log_dir, "app.log"),
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    _file.setFormatter(_formatter)

    _root = logging.getLogger()
    _root.handlers = [_console, _file]
    _root.setLevel(logging.INFO)

    for _lib in ("sqlalchemy.engine", "werkzeug", "flask_jwt_extended"):
        logging.getLogger(_lib).setLevel(logging.WARNING)

    app.logger.handlers = [_console, _file]
    app.logger.setLevel(logging.INFO)
    app.logger.info("Logging configured: console + logs/app.log")


class Config:
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        raise RuntimeError("Missing required configuration: DATABASE_URL is not set.")

    SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    if not SECRET_KEY:
        raise RuntimeError("Missing required configuration: JWT_SECRET_KEY is not set.")

    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_size": 5,
        "max_overflow": 10,
        "connect_args": {
            "options": f"-c search_path={os.getenv('DB_SCHEMA', 'order_sales')},public"
        },
    }

    JWT_SECRET_KEY = SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_HOURS", "24")) * 3600

    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() == "true"

    DB_SCHEMA = os.getenv("DB_SCHEMA", "order_sales")

    VERIFY_TTL_MINUTES = int(os.getenv("VERIFY_TTL_MINUTES", "2"))
    VERIFY_MAX_ATTEMPTS = int(os.getenv("VERIFY_MAX_ATTEMPTS", "3"))
    RESET_TTL_HOURS = int(os.getenv("RESET_TTL_HOURS", "1"))
