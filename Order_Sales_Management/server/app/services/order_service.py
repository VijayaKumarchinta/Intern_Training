import re
from decimal import Decimal
import re
from decimal import Decimal
from datetime import datetime, timezone


def _today():
    return datetime.now(timezone.utc).date()


def _today():
    return datetime.now(timezone.utc).date()


def _today():
    return datetime.now(timezone.utc).date()


def _today():
    return datetime.now(timezone.utc).date()

from flask import current_app
from sqlalchemy import func, select

from app.extensions import db
from app import models


ORDER_ID_RE = re.compile(r"^ORD\d{4}$")


def validate_order(row: dict) -> list[str]:
    errors: list[str] = []

    order_id = row.get("order_id")
    if not order_id or not isinstance(order_id, str) or not ORDER_ID_RE.match(order_id):
        errors.append("Invalid OrderID format")

    order_date = row.get("order_date")
    if not order_date:
        errors.append("Date is required")
    else:
        parsed = _parse_date(order_date)
        if parsed is None:
            errors.append("Invalid date")
        elif parsed > _today():
            errors.append("Date cannot be in the future")

    customer_id = row.get("customer_id")
    if not customer_id:
        errors.append("CustomerID is required")

    product = row.get("product")
    if not product or not isinstance(product, str) or product not in current_app.config["PRODUCTS"]:
        errors.append("Product must be a valid product")

    quantity = row.get("quantity")
    q = _to_int(quantity)
    if q is None:
        errors.append("Quantity must be an integer")
    elif q <= 0 or q > 1000:
        errors.append("Quantity must be between 1 and 1000")

    unit_price = row.get("unit_price")
    up = _to_decimal(unit_price)
    if up is None:
        errors.append("UnitPrice must be a number")
    elif up < 0:
        errors.append("UnitPrice cannot be negative")

    status = row.get("order_status")
    if not status or not isinstance(status, str) or status not in current_app.config["ORDER_STATUSES"]:
        errors.append("OrderStatus is invalid")

    return errors


def _parse_date(value):
    if isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
            try:
                return datetime.strptime(value.strip(), fmt).date()
            except ValueError:
                continue
    return None


def _to_int(value) -> int | None:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError:
            return None
    if isinstance(value, (Decimal, float)):
        try:
            return int(Decimal(str(value)))
        except Exception:
            return None
    return None


def _to_decimal(value) -> Decimal | None:
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        try:
            return Decimal(str(value))
        except Exception:
            return None
    if isinstance(value, str):
        try:
            return Decimal(value.strip())
        except Exception:
            return None
    return None


def _customer_exists(customer_id: str) -> bool:
    return db.session.execute(
        select(models.Customer).where(models.Customer.customer_id == customer_id)
    ).scalar_one_or_none() is not None


def visible_orders_for(user: models.User):
    if user.role == "admin":
        stmt = db.select(models.Order)
    else:
        stmt = (
            db.select(models.Order)
            .join(models.Customer, models.Order.customer_id == models.Customer.customer_id)
            .where(models.Customer.user_id == user.id)
        )
    return db.session.execute(stmt).scalars().all()


def get_order_by_id(order_id: str, user: models.User | None = None) -> models.Order | None:
    order = db.session.execute(
        db.select(models.Order).where(models.Order.order_id == order_id)
    ).scalar_one_or_none()
    if order is None:
        return None
    if user is not None and user.role != "admin":
        customer = db.session.execute(
            db.select(models.Customer).where(
                models.Customer.customer_id == order.customer_id,
                models.Customer.user_id == user.id,
            )
        ).scalar_one_or_none()
        if customer is None:
            return None
    return order


def change_status(order: models.Order, new_status: str) -> None:
    current_status = order.order_status or "Pending"
    allowed = current_app.config["STATUS_TRANSITIONS"].get(current_status, set())
    if new_status not in allowed:
        raise ValueError(f"Invalid status transition from {current_status} to {new_status}")
    order.order_status = new_status
    order.updated_at = datetime.now(timezone.utc)


def line_total(quantity, unit_price) -> Decimal:
    q = _to_int(quantity) or 0
    up = _to_decimal(unit_price) or Decimal(0)
    return Decimal(q) * up


def find_duplicates() -> list[dict]:
    rows = db.session.execute(
        select(
            models.Order.order_id,
            models.Order.customer_id,
            models.Order.product,
            models.Order.order_date,
            models.Order.quantity,
            models.Order.unit_price,
        )
        .where(models.Order.is_valid.is_(True))
        .order_by(models.Order.customer_id, models.Order.product, models.Order.order_date)
    ).all()

    by_key: dict[tuple, list[dict]] = {}
    for row in rows:
        key = (row.customer_id, row.product, row.order_date, row.quantity, row.unit_price)
        by_key.setdefault(key, []).append(
            {"order_id": row.order_id, "customer_id": row.customer_id, "product": row.product}
        )

    duplicates: list[dict] = []
    for group in by_key.values():
        if len(group) > 1:
            for entry in group[1:]:
                duplicates.append({"order_id": entry["order_id"], "duplicate_of": group[0]["order_id"]})

    return duplicates


def product_wise_report(filters: dict | None = None) -> list[dict]:
    stmt = (
        select(
            models.Order.product,
            func.coalesce(func.sum(models.Order.quantity), 0).label("total_quantity"),
            func.coalesce(func.sum(func.cast(models.Order.quantity, db.Float) * func.cast(models.Order.unit_price, db.Float)), 0).label("total_revenue"),
            func.count(models.Order.order_id).label("order_count"),
        )
        .where(models.Order.is_valid.is_(True))
        .group_by(models.Order.product)
    )
    return _apply_filters(stmt, filters)


def date_wise_report(filters: dict | None = None, group: str = "day") -> list[dict]:
    date_expr = _date_group_expr(group)
    stmt = (
        select(
            date_expr.label("period"),
            func.coalesce(func.sum(models.Order.quantity), 0).label("total_quantity"),
            func.coalesce(func.sum(func.cast(models.Order.quantity, db.Float) * func.cast(models.Order.unit_price, db.Float)), 0).label("total_revenue"),
            func.count(models.Order.order_id).label("order_count"),
        )
        .where(models.Order.is_valid.is_(True))
        .group_by(date_expr)
        .order_by(date_expr)
    )
    return _apply_filters(stmt, filters)


def summary_report(filters: dict | None = None) -> dict:
    stmt = (
        select(
            func.count(models.Order.order_id).label("order_count"),
            func.coalesce(func.sum(models.Order.quantity), 0).label("total_quantity"),
            func.coalesce(func.sum(func.cast(models.Order.quantity, db.Float) * func.cast(models.Order.unit_price, db.Float)), 0).label("total_revenue"),
        )
        .where(models.Order.is_valid.is_(True))
    )
    row = db.session.execute(stmt).one()
    return {
        "order_count": int(row.order_count),
        "total_quantity": float(row.total_quantity),
        "total_revenue": float(row.total_revenue),
        **_filter_counts(filters),
    }


def _apply_filters(stmt, filters: dict | None = None) -> list[dict]:
    if not filters:
        rows = db.session.execute(stmt).all()
        return _to_dicts(rows)

    stmt = _add_filters(stmt, filters)
    rows = db.session.execute(stmt).all()
    return _to_dicts(rows)


def _add_filters(stmt, filters: dict):
    if filters.get("status"):
        stmt = stmt.where(models.Order.order_status == filters["status"])
    if filters.get("product"):
        stmt = stmt.where(models.Order.product == filters["product"])
    if filters.get("from_date"):
        parsed = _parse_date(filters["from_date"])
        if parsed is not None:
            stmt = stmt.where(models.Order.order_date >= parsed)
    if filters.get("to_date"):
        parsed = _parse_date(filters["to_date"])
        if parsed is not None:
            stmt = stmt.where(models.Order.order_date <= parsed)
    return stmt


def _filter_counts(filters: dict) -> dict:
    base = db.select(func.count(models.Order.order_id).label("count")).where(models.Order.is_valid.is_(True))
    filtered = _add_filters(base, filters)
    count_row = db.session.execute(filtered).one()
    total_row = db.session.execute(db.select(func.count(models.Order.order_id)).where(models.Order.is_valid.is_(True))).one()
    return {
        "total_orders": int(total_row["count"]),
        "filtered_orders": int(count_row["count"]),
    }


def _to_dicts(rows) -> list[dict]:
    out: list[dict] = []
    for row in rows:
        out.append({key: _serialize(val) for key, val in row._mapping.items()})
    return out


def _serialize(val):
    if isinstance(val, Decimal):
        return float(val)
    if isinstance(val, (datetime, date)):
        return val.isoformat()
    return val


def _date_group_expr(group: str):
    if group == "day":
        return func.cast(models.Order.order_date, db.String).label("period")
    if group == "month":
        return func.cast(func.date_trunc("month", models.Order.order_date), db.String).label("period")
    return func.cast(models.Order.order_date, db.String).label("period")
