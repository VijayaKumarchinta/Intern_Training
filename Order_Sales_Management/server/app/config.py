import os
from pathlib import Path

from dotenv import load_dotenv
import psycopg2


_env_path = Path(__file__).resolve().parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path, override=False)


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw.strip())
    except ValueError:
        return default


class Config:
    def __init__(self):
        self.ENV = os.getenv("FLASK_ENV", "production")
        self.DEBUG = _env_bool("FLASK_DEBUG", self.ENV == "development")

        self.DB_HOST = os.getenv("DB_HOST", "localhost")
        self.DB_PORT = _env_int("DB_PORT", 5432)
        self.DB_NAME = os.getenv("DB_NAME", "machine_monitor_db")
        self.DB_USER = os.getenv("DB_USER", "postgres")
        self.DB_PASSWORD = os.getenv("DB_PASSWORD", "")
        self.DB_SCHEMA = os.getenv("DB_SCHEMA", "sales_schema")

        self.ADMIN_API_TOKEN = os.getenv("ADMIN_API_TOKEN", "")
        self.FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

        self._dsn = None
        self._conn = None

    @property
    def dsn(self) -> str:
        if self._dsn is None:
            self._dsn = (
                f"host={self.DB_HOST}"
                f" port={self.DB_PORT}"
                f" dbname={self.DB_NAME}"
                f" user={self.DB_USER}"
                f" password={self.DB_PASSWORD}"
                f" connect_timeout=5"
            )
        return self._dsn

    def connect(self):
        """Return a cached connection (reuse for the life of the config)."""
        if self._conn is None:
            self._conn = psycopg2.connect(self.dsn)
        return self._conn


# Shared config instance used across the app.
config = Config()
