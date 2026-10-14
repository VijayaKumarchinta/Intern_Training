import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask
from sqlalchemy import event
from sqlalchemy.engine import Engine

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Config:
    SQLALCHEMY_DATABASE_URI = os.environ["DATABASE_URL"]
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.environ["JWT_SECRET_KEY"]
    JWT_ACCESS_TOKEN_EXPIRES_SECONDS = int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRES_SECONDS", "900"))
    JWT_REFRESH_TOKEN_EXPIRES_SECONDS = int(os.environ.get("JWT_REFRESH_TOKEN_EXPIRES_SECONDS", "86400"))

    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() in ("true", "1", "yes")
    MAIL_USERNAME = os.environ["MAIL_USERNAME"]
    MAIL_PASSWORD = os.environ["MAIL_PASSWORD"]

    SECRET_KEY = os.environ["JWT_SECRET_KEY"]

    PRODUCTS = [
        "Monitor",
        "Phone",
        "Tablet",
        "Chair",
        "Printer",
        "Laptop",
        "Desk",
    ]

    ORDER_STATUSES = [
        "Pending",
        "Shipped",
        "Delivered",
        "Cancelled",
        "Returned",
    ]

    STATUS_TRANSITIONS = {
        "Pending": {"Shipped", "Cancelled"},
        "Shipped": {"Delivered", "Returned"},
        "Delivered": {"Returned"},
        "Cancelled": set(),
        "Returned": set(),
        "Received": set(),
    }


@event.listens_for(Engine, "connect")
def set_search_path(dbapi_conn, _):
    with dbapi_conn.cursor() as cur:
        cur.execute("SET search_path TO order_sales, public")
