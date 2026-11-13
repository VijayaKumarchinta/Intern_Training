import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy.engine import make_url

PROJECT_ROOT = Path(__file__).resolve().parents[1]

load_dotenv(PROJECT_ROOT / ".env")

def _required_env(key: str) -> str:
    value = os.getenv(key)

    if value is None or not value.strip():
        raise RuntimeError(
            f"Required environment variable is missing: {key}"
        )
    return value.strip()

DATABASE_URL = make_url(_required_env("DATABASE_URL"))

if DATABASE_URL.drivername != "postgresql+psycopg":
    raise RuntimeError(
        "DATABASE_URL must use postgresql+psycopg."
    )

if not all((
    DATABASE_URL.host,
    DATABASE_URL.database,
    DATABASE_URL.username,
    DATABASE_URL.password,
)):
    raise RuntimeError(
        "DATABASE_URL must include host, database, username and password."
    )

DB_POOL_SIZE = 5
DB_MAX_OVERFLOW =2
DB_POOL_TIMEOUT =30

MQTT_HOST = "127.0.0.1"
MQTT_PORT = 1883
MQTT_KEEPALIVE = 60
MQTT_TOPIC = "factory/line30/telemetry"
MQTT_QOS = 1
MQTT_CLIENT_ID = "line30-flask-subscriber"

if not MQTT_HOST:
    raise RuntimeError("MQTT_HOST cannot be empty.")

if not MQTT_TOPIC:
    raise RuntimeError("MQTT_TOPIC cannot be empty.")

if not MQTT_CLIENT_ID:
    raise RuntimeError("MQTT_CLIENT_ID cannot be empty.")

SOCKETIO_CORS_ORIGINS = [
    origin.strip().rstrip("/")
    for origin in os.getenv(
        "SOCKETIO_CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]

if not SOCKETIO_CORS_ORIGINS:
    raise RuntimeError(
        "SOCKETIO_CORS_ORIGINS must contain at least one allowed frontend origin."
    )

