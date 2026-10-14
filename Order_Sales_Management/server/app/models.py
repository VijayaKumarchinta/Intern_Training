from datetime import datetime, timezone


def _today():
    return date.today()

from app.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(255), nullable=True)
    role = db.Column(db.String(20), nullable=False, default="customer")
    is_verified = db.Column(db.Boolean, nullable=False, default=False)
    verification_token = db.Column(db.String(255), nullable=True)
    reset_token = db.Column(db.String(255), nullable=True)
    reset_token_expires = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class Customer(db.Model):
    __tablename__ = "customers"

    customer_id = db.Column(db.String(20), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    name = db.Column(db.String(255), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class Order(db.Model):
    __tablename__ = "orders"

    order_id = db.Column(db.String(20), primary_key=True)
    order_date = db.Column(db.Date, nullable=True)
    customer_id = db.Column(db.String(20), nullable=True)
    product = db.Column(db.String(100), nullable=True)
    quantity = db.Column(db.Numeric(10, 2), nullable=True)
    unit_price = db.Column(db.Numeric(12, 2), nullable=True)
    order_status = db.Column(db.String(20), nullable=True)
    is_valid = db.Column(db.Boolean, nullable=False, default=False)
    validation_errors = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
