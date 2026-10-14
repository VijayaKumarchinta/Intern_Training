"""
Public API for the repository layer.
"""

from app.repositories import order_repository as order_repository
from app.repositories import report_repository as report_repository

# Re-export the functions names from the order repo so they can be imported
# as app.repositories.find_by_idempotency_key(...), etc.
from app.repositories.order_repository import (
    find_by_idempotency_key,
    find_by_payload_hash,
    record_idempotency,
    insert_order,
    find_order,
    list_orders,
    update_order_fields,
    update_order_status,
)
from app.repositories.report_repository import (
    _product_rows,
    _date_rows,
)

__all__ = [
    "order_repository",
    "report_repository",
    "find_by_idempotency_key",
    "find_by_payload_hash",
    "record_idempotency",
    "insert_order",
    "find_order",
    "list_orders",
    "update_order_fields",
    "update_order_status",
    "_product_rows",
    "_date_rows",
]
