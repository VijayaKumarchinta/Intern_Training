from datetime import datetime, timezone
from .extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(255)) 
    role = db.Column(db.String(20), nullable=False, default="customer")
    is_verified = db.Column(db.Boolean, nullable=False, default=False)
    verification_token = db.Column(db.String(255))
    reset_token = db.Column(db.String(255))
    reset_token_expires = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role,
            "is_verified": self.is_verified,
        }


class Customer(db.Model):
    __tablename__ = "customers"

    customer_id = db.Column(db.String(20), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"))
    name = db.Column(db.String(255))
    email = db.Column(db.String(255))
    created_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "customer_id": self.customer_id,
            "user_id": self.user_id,
            "name": self.name,
            "email": self.email,
        }


class Order(db.Model):
    __tablename__ = "orders"

    order_id = db.Column(db.String(20), primary_key=True)
    order_date = db.Column(db.Date)
    customer_id = db.Column(db.String(20))
    product = db.Column(db.String(100))
    quantity = db.Column(db.Numeric(10, 2))
    unit_price = db.Column(db.Numeric(12, 2))
    order_status = db.Column(db.String(20))
    is_valid = db.Column(db.Boolean, nullable=False, default=False)
    validation_errors = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "order_id": self.order_id,
            "order_date": self.order_date.isoformat() if self.order_date else None,
            "customer_id": self.customer_id,
            "product": self.product,
            "quantity": float(self.quantity) if self.quantity is not None else None,
            "unit_price": float(self.unit_price) if self.unit_price is not None else None,
            "order_status": self.order_status,
            "is_valid": self.is_valid,
            "validation_errors": self.validation_errors,
        }