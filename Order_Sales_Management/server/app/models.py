from datetime import datetime, timezone
from .extensions import db

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(255))
    role = db.Column(db.String(20), nullable=False, default="customer")
    is_verified = db.Column(db.Boolean, nullable=False, default=False)
    verification_token_hash = db.Column(db.String(255))
    verification_expires_at = db.Column(db.DateTime(timezone=True))
    reset_token_hash = db.Column(db.String(255))
    reset_token_expires_at = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    customer = db.relationship("Customer", backref="user", uselist=False)

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
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        unique=True,
    )
    cust_name = db.Column(db.String(255))
    email = db.Column(db.String(255))
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    orders = db.relationship("Order", backref="customer", lazy="select")

    def to_dict(self):
        return {
            "customer_id": self.customer_id,
            "user_id": self.user_id,
            "cust_name": self.cust_name,
            "email": self.email,
        }


class Product(db.Model):
    __tablename__ = "products"

    product_id = db.Column(db.Integer, primary_key=True)
    pro_name = db.Column(db.String(100), unique=True, nullable=False)
    current_price = db.Column(db.Numeric(12, 2))

    order_items = db.relationship("OrderItem", backref="product", lazy="select")

    def to_dict(self):
        return {
            "product_id": self.product_id,
            "pro_name": self.pro_name,
            "current_price": (
                float(self.current_price) if self.current_price is not None else None
            ),
        }


class Order(db.Model):
    __tablename__ = "orders"

    order_id = db.Column(db.String(20), primary_key=True)
    customer_id = db.Column(
        db.String(20),
        db.ForeignKey("customers.customer_id"),
        nullable=False,
    )
    order_date = db.Column(db.Date)
    order_status = db.Column(
        db.String(20),
        nullable=False,
        default="Pending",
    )
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    items = db.relationship(
        "OrderItem",
        backref="order",
        lazy="select",
        cascade="all, delete-orphan",
        order_by="OrderItem.order_item_id",
    )

    def to_dict(self, include_items=False):
        data = {
            "order_id": self.order_id,
            "customer_id": self.customer_id,
            "order_date": self.order_date.isoformat() if self.order_date else None,
            "order_status": self.order_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_items:
            data["items"] = [item.to_dict() for item in self.items]
        return data


class OrderItem(db.Model):
    __tablename__ = "order_items"

    order_item_id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(
        db.String(20),
        db.ForeignKey("orders.order_id", ondelete="CASCADE"),
        nullable=False,
    )
    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.product_id"),
        nullable=False,
    )
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(12, 2), nullable=False)

    __table_args__ = (
        db.UniqueConstraint("order_id", "product_id", name="uq_order_product"),
    )

    def to_dict(self):
        return {
            "order_item_id": self.order_item_id,
            "order_id": self.order_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "unit_price": float(self.unit_price) if self.unit_price is not None else None,
            "line_total": (
                float(self.quantity * self.unit_price)
                if self.quantity is not None and self.unit_price is not None
                else None
            ),
        }
