"""
order_service - business rules for orders.

Validation lives in app.validators; the service turns clean input into
persisted orders, applies status transitions, and decides whether a duplicate
submission has to be rejected or allowed (allow_duplicate).
"""

import hashlib
import logging

from app import repositories
from app import validators

logger = logging.getLogger(__name__)


# ---- Order creation ----


def create_order(conn, payload, idempotency_key):
    """
    Create an order inside a transaction with duplicate protection.

    Returns (order, created) where:
      - created=True  -> a brand-new order was inserted
      - created=False -> an existing order was returned for a retry
    """
    clean, error = validators.validate_body(payload, create=True)
    if error:
        return None, None, error

    payload_hash = hashlib.sha256(
        f"{clean['customer_id']}|{clean['product']}|{clean['quantity']}|"
        f"{clean['unit_price']}|{clean['order_date']}".encode("utf-8")
    ).hexdigest()

    existing = repositories.find_by_idempotency_key(conn, idempotency_key)
    if existing is not None:
        # Same key: identical payload -> retry, return original.
        if existing["payload_hash"] == payload_hash:
            return repositories.find_order(conn, existing["order_id"]), False, None
        # Same key: different payload -> key was reused with different data.
        return None, None, "IDEMPOTENCY_KEY_REUSED"

    # New key: only reject true duplicate content if the same tuple
    # already exists under a different key.
    dup_order_id = repositories.find_by_payload_hash(conn, payload_hash)
    if dup_order_id is not None:
        return None, None, "DUPLICATE_SUSPECTED"

    order = {
        "order_id": f"ORD{next_order_id(conn)}",
        "customer_id": clean["customer_id"],
        "product": clean["product"],
        "quantity": clean["quantity"],
        "unit_price": clean["unit_price"],
        "order_date": clean["order_date"],
        "status": "Pending",
    }

    repositories.record_idempotency(conn, idempotency_key, payload_hash, order["order_id"])
    return repositories.insert_order(conn, order), True, None


def next_order_id(conn):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT nextval('" + repositories._get_schema() + ".order_id_seq')"
        )
        return cur.fetchone()[0]


# ---- Partial order edit (Pending only, admin) ----


def edit_order(conn, order_id, payload, admin_token):
    order = repositories.find_order(conn, order_id)
    if order is None:
        return None, "NOT_FOUND"

    if not _admin_ok(admin_token):
        return None, "UNAUTHORIZED"

    if order["status"] != "Pending":
        return None, "ORDER_NOT_EDITABLE"

    clean, error = validators.validate_body(payload, create=False)
    if error:
        return None, "VALIDATION_ERROR"

    updated = repositories.update_order_fields(conn, order_id, clean)
    if updated is None:
        return None, "NOT_FOUND"
    return updated, None


# ---- Status change (admin) ----


def change_status(conn, order_id, status, admin_token):
    if not _admin_ok(admin_token):
        return None, "UNAUTHORIZED"

    allowed = {
        "Pending":   {"Shipped", "Cancelled"},
        "Shipped":   {"Delivered", "Returned"},
        "Delivered": {"Returned"},
        "Cancelled": set(),
        "Returned":  set(),
    }

    current = repositories.find_order(conn, order_id)
    if current is None:
        return None, "NOT_FOUND"
    if status not in allowed.get(current["status"], set()):
        return None, "INVALID_STATUS_TRANSITION"

    updated = repositories.update_order_status(conn, order_id, status)
    if updated is None:
        return None, "NOT_FOUND"
    return updated, None


# ---- Read ----


def get_order(conn, order_id):
    return repositories.find_order(conn, order_id)


def list_orders(conn, status=None, customer_id=None, start_date=None, end_date=None, page=1, page_size=50):
    return repositories.list_orders(conn, status, customer_id, start_date, end_date, page, page_size)


# ---- Helpers ----


def _admin_ok(token):
    return token and token == __import__("app").config.config.ADMIN_API_TOKEN


# ---- Report services ----


def sales_by_product(conn):
    return repositories._product_rows(conn)


def sales_by_date(conn, start_date=None, end_date=None):
    return repositories._date_rows(conn, start_date, end_date)
