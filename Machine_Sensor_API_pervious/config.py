import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

load_dotenv()

REQUIRED_ENV_VARS = [
    "DB_HOST",
    "DB_PORT",
    "DB_NAME",
    "DB_USER",
    "DB_PASSWORD",
    "DB_SCHEMA",
]

_missing = [name for name in REQUIRED_ENV_VARS if not os.getenv(name)]

if _missing:
    raise RuntimeError(
        "Missing required environment variables: "
        + ", ".join(_missing)
        + ". Copy .env.example to .env and fill in the values."
    )


def _get_int(name, default=None):
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        raise RuntimeError(
            f"Environment variable {name} must be an integer, got: {raw!r}"
        ) from None


DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT"))
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_SCHEMA = os.getenv("DB_SCHEMA")

DB_POOL_MIN = _get_int("DB_POOL_MIN",2)
DB_POOL_MAX = _get_int("DB_POOL_MAX",10)

if DB_POOL_MIN < 1 or DB_POOL_MAX < DB_POOL_MIN:
    raise RuntimeError(
        f"Invalid pool configuration: DB_POOL_MIN ({DB_POOL_MIN}) must be >= 1 "
        f"and <= DB_POOL_MAX ({DB_POOL_MAX})."
    )

DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data")))
IMPORT_BATCH_SIZE = _get_int("IMPORT_BATCH_SIZE", 5000)
IMPORT_FILE_NAME = os.getenv(
    "IMPORT_FILE_NAME",
    "pickle_files_28_03_2025/all_topics_20250328-114500.pkl",
)
DEFAULT_PAGE_SIZE = _get_int("DEFAULT_PAGE_SIZE", 1000)

GENERIC_DB_ERROR = "A database error occurred. Please try again later."
