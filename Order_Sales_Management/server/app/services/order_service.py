import re
from decimal import Decimal
from sqlalchemy import func
from ..extensions import db
from ..models import Customer, Order, OrderItem, Product
from datetime import date

VALID_STATUSES = {"Pending", "Received", "Shipped", "Delivered", "Cancelled", "Returned"}

ALLOWED_TRANSITIONS = {
    "Pending":   {"Received", "Shipped", "Cancelled"},
    "Received":  {"Shipped", "Cancelled"},
    "Shipped":   {"Delivered", "Returned"},
    "Delivered": {"Returned"},
    "Cancelled": set(),
    "Returned":  set(),
}

def validate_order_payload(payload):
    errors = []

    order_id = payload.get("order_id")
    if not order_id or not re.match(r"^ORD\d{4}$", str(order_id)):
        errors.append("order_id must match ORD####")

    order_date = payload.get("order_date")
    if not order_date:
        errors.append("order_date is required")
    else:
        try:
            date.fromisoformat(str(order_date))
        except (TypeError, ValueError):
            errors.append("order_date must be YYYY-MM-DD")

    customer_id = payload.get("customer_id")
    if not customer_id:
        errors.append("customer_id is required")
    elif not re.match(r"^C\d{4}$", str(customer_id)):
        errors.append("customer_id must match C####")
    elif not Customer.query.filter_by(customer_id=str(customer_id)).first():
        errors.append(f"Unknown customer: {customer_id}")

    items = payload.get("items") or []
    if not items:
        errors.append("At least one item is required")

    seen = set()
    for i, item in enumerate(items):
        pid = item.get("product_id")
        if pid in seen:
            errors.append(f"items[{i}].product_id is duplicated")
        seen.add(pid)

        if pid is None or Product.query.get(pid) is None:
            errors.append(f"items[{i}].product_id does not exist")

        qty = item.get("quantity")
        if qty is None:
            errors.append(f"items[{i}].quantity is required")
        else:
            try:
                qd = Decimal(str(qty))
                if qd < 1 or qd > 1000:
                    errors.append(f"items[{i}].quantity must be 1..1000")
            except Exception:
                errors.append(f"items[{i}].quantity is not a valid number")

        price = item.get("unit_price")
        if price is None:
            errors.append(f"items[{i}].unit_price is required")
        else:
            try:
                pd = Decimal(str(price))
                if pd < 0:
                    errors.append(f"items[{i}].unit_price must be >= 0")
            except Exception:
                errors.append(f"items[{i}].unit_price is not a valid number")

    status = payload.get("order_status", "Pending")
    if status not in VALID_STATUSES:
        errors.append(f"Invalid order_status: {status!r}")

    return errors

def visible_orders_for(user):
    if user is None:
        return Order.query.filter(False)
    if user.role == "admin":
        return Order.query
    return (
        Order.query
        .join(Customer, Customer.customer_id == Order.customer_id)
        .filter(Customer.user_id == user.id)
    )

def can_transition(old_status, new_status):
    if old_status not in VALID_STATUSES or new_status not in VALID_STATUSES:
        return False
    return new_status in ALLOWED_TRANSITIONS.get(old_status, set())

def change_status(order, new_status):
    if not can_transition(order.order_status, new_status):
        return False, f"Cannot move from {order.order_status} to {new_status}"
    order.order_status = new_status
    db.session.commit()
    return True, None

def _sale_statuses():
    return {"Shipped", "Delivered"}

def product_wise_report():
    rows = (
        db.session.query(
            Product.pro_name.label("product"),
            func.count(OrderItem.order_item_id).label("items"),
            func.sum(OrderItem.quantity).label("units"),
            func.sum(OrderItem.quantity * OrderItem.unit_price).label("revenue"),
        )
        .join(OrderItem, OrderItem.product_id == Product.product_id)
        .join(Order, Order.order_id == OrderItem.order_id)
        .filter(Order.order_status.in_(_sale_statuses()))
        .group_by(Product.pro_name)
        .order_by(func.sum(OrderItem.quantity * OrderItem.unit_price).desc())
        .all()
    )
    return [
        {
            "product": r.product,
            "items": int(r.items or 0),
            "units": float(r.units or 0),
            "revenue": float(r.revenue or 0),
        }
        for r in rows
    ]

def date_wise_report(group="day"):
    bucket = func.date_trunc("month", Order.order_date) if group == "month" else Order.order_date

    rows = (
        db.session.query(
            bucket.label("bucket"),
            func.count(func.distinct(Order.order_id)).label("orders"),
            func.sum(OrderItem.quantity).label("units"),
            func.sum(OrderItem.quantity * OrderItem.unit_price).label("revenue"),
        )
        .join(OrderItem, OrderItem.order_id == Order.order_id)
        .filter(Order.order_status.in_(_sale_statuses()))
        .group_by(bucket)
        .order_by(bucket)
        .all()
    )
    return [
        {
            "period": r.bucket.isoformat() if hasattr(r.bucket, "isoformat") else str(r.bucket),
            "orders": int(r.orders or 0),
            "units": float(r.units or 0),
            "revenue": float(r.revenue or 0),
        }
        for r in rows
    ]

def find_duplicates():
    rows = (
        db.session.query(
            Order.customer_id,
            OrderItem.product_id,
            OrderItem.quantity,
            OrderItem.unit_price,
            Order.order_date,
            func.count(OrderItem.order_item_id).label("occurrences"),
            func.array_agg(Order.order_id).label("order_ids"),
        )
        .join(OrderItem, OrderItem.order_id == Order.order_id)
        .group_by(
            Order.customer_id,
            OrderItem.product_id,
            OrderItem.quantity,
            OrderItem.unit_price,
            Order.order_date,
        )
        .having(func.count(OrderItem.order_item_id) > 1)
        .order_by(func.count(OrderItem.order_item_id).desc())
        .all()
    )
    return [
        {
            "customer_id": r.customer_id,
            "product_id": r.product_id,
            "quantity": int(r.quantity) if r.quantity is not None else None,
            "unit_price": float(r.unit_price) if r.unit_price is not None else None,
            "order_date": r.order_date.isoformat() if r.order_date is not None else None,
            "occurrences": int(r.occurrences or 0),
            "order_ids": sorted(r.order_ids or []),
        }
        for r in rows
    ]