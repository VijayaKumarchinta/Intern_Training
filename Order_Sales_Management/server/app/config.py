import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

_env_name = os.getenv("FLASK_ENV", "development")
_env_file = ".env.test" if _env_name == "test" else ".env"
load_dotenv(os.path.join(BASE_DIR, _env_file))


def configure_logging(app):
    log_dir = os.path.join(BASE_DIR, "logs")
    os.makedirs(log_dir, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        os.path.join(log_dir, "app.log"),
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers = [console, file_handler]
    root.setLevel(logging.INFO)

    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("flask_jwt_extended").setLevel(logging.WARNING)
    logging.getLogger("werkzeug").setLevel(logging.INFO)

    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        app.logger.info("Server ready")


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
            "options": f"-c search_path={os.getenv('DB_SCHEMA') or 'order_sales'}"
        },
    }

    JWT_SECRET_KEY = SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_HOURS", "24")) * 3600

    MAIL_SERVER = os.getenv("MAIL_SERVER", "localhost")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "no-reply@example.com")

    DB_SCHEMA = os.getenv("DB_SCHEMA", "order_sales")

    VERIFY_TTL_MINUTES = int(os.getenv("VERIFY_TTL_MINUTES", "2"))
    VERIFY_MAX_ATTEMPTS = int(os.getenv("VERIFY_MAX_ATTEMPTS", "3"))
    RESET_TTL_HOURS = int(os.getenv("RESET_TTL_HOURS", "1"))