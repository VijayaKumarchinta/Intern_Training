import logging
import hashlib
from datetime import datetime

from ..db import get_connection, return_connection, NotFoundError, qualified
from ..utils.validation import (
    validate_order_date,
    validate_order_items,
    validate_id_format,
    ORDER_STATUS_TRANSITIONS,
    VALID_ORDER_STATUSES,
)

logger = logging.getLogger(__name__)

ORDERS_TABLE = qualified("orders")
ORDER_ITEMS_TABLE = qualified("order_items")
CUSTOMERS_TABLE = qualified("customers")
PRODUCTS_TABLE = qualified("products")


def create_order(customer_id, items, order_id=None, order_date=None,
                 shipping_address=None, notes=None):
    from server.services.customer_service import get_customer_by_id
    from server.services.product_service import get_product_by_id

    get_customer_by_id(customer_id)
    validated_items = validate_order_items(items)

    if order_id:
        order_id = validate_id_format(order_id, "order_id")
    else:
        order_id = _generate_order_id()

    parsed_date = validate_order_date(order_date)

    item_details = []
    total = 0.0

    for item in validated_items:
        product_id = item["product_id"]
        quantity = item["quantity"]
        provided_price = item["unit_price"]

        try:
            product = get_product_by_id(product_id)
        except NotFoundError:
            raise ValueError(f"Product '{product_id}' not found")

        if provided_price is not None:
            unit_price = float(provided_price)
        else:
            unit_price = float(product["unit_price"] or 0)

        item_total = round(quantity * unit_price, 2)
        total += item_total

        item_details.append({
            "product_id": product_id,
            "quantity": quantity,
            "unit_price": unit_price,
            "total": item_total,
        })

    total = round(total, 2)

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                INSERT INTO {ORDERS_TABLE}
                    (order_id, customer_id, order_date, status, shipping_address, notes)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (order_id) DO NOTHING
                """,
                (order_id, customer_id, parsed_date, "pending",
                 shipping_address, notes),
            )
            if cursor.rowcount == 0:
                raise ConflictError(f"Order '{order_id}' already exists")

            for item in item_details:
                cursor.execute(
                    f"""
                    INSERT INTO {ORDER_ITEMS_TABLE}
                        (order_id, product_id, quantity, unit_price, total)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (order_id, item["product_id"],
                     item["quantity"], item["unit_price"], item["total"]),
                )

        conn.commit()
        logger.info(
            "Created order: %s for customer %s, total: $%.2f, items: %d",
            order_id, customer_id, total, len(item_details),
        )
    except Exception:
        conn.rollback()
        raise
    finally:
        return_connection(conn)

    return get_order_by_id(order_id)


def get_order_by_id(order_id):
    order_id = validate_id_format(order_id, "order_id")

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT o.order_id, o.customer_id, o.order_date, o.status,
                       o.shipping_address, o.notes, o.payment_method,
                       o.tracking_number, o.items_in_cart, o.coupon_code,
                       o.referral_source, o.created_at, o.updated_at,
                       c.name as cust_name, c.email as cust_email, c.phone as cust_phone
                FROM {ORDERS_TABLE} o
                JOIN {CUSTOMERS_TABLE} c ON o.customer_id = c.customer_id
                WHERE o.order_id = %s
                """,
                (order_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise NotFoundError(f"Order '{order_id}' not found")

            order = {
                "order_id": row[0],
                "customer": {
                    "customer_id": row[1],
                    "name": row[13],
                    "email": row[14],
                    "phone": row[15],
                },
                "order_date": row[2].isoformat() if row[2] else None,
                "status": row[3],
                "shipping_address": row[4],
                "notes": row[5],
                "payment_method": row[6],
                "tracking_number": row[7],
                "items_in_cart": row[8],
                "coupon_code": row[9],
                "referral_source": row[10],
                "created_at": row[11].isoformat() if row[11] else None,
                "updated_at": row[12].isoformat() if row[12] else None,
            }

            cursor.execute(
                f"""
                SELECT oi.id, oi.product_id, oi.quantity, oi.unit_price, oi.total,
                       p.name as prod_name, p.category as prod_category
                FROM {ORDER_ITEMS_TABLE} oi
                JOIN {PRODUCTS_TABLE} p ON oi.product_id = p.product_id
                WHERE oi.order_id = %s
                ORDER BY oi.id
                """,
                (order_id,),
            )
            items = []
            items_total = 0.0
            for item_row in cursor.fetchall():
                t = float(item_row[4]) if item_row[4] else 0
                items_total += t
                items.append({
                    "id": item_row[0],
                    "product_id": item_row[1],
                    "product_name": item_row[5],
                    "category": item_row[6],
                    "quantity": item_row[2],
                    "unit_price": float(item_row[3]) if item_row[3] else None,
                    "total": t,
                })
            order["items"] = items
            order["total"] = round(items_total, 2)
            return order
    finally:
        return_connection(conn)


def get_all_orders(limit=100, offset=0, status=None, customer_id=None,
                   from_date=None, to_date=None):
    try:
        limit = int(limit)
        if limit < 1:
            limit = 1
        if limit > 500:
            limit = 500
    except (ValueError, TypeError):
        limit = 100

    offset = max(0, int(offset or 0))

    conditions = ["1=1"]
    params = []

    if status:
        conditions.append("o.status = %s")
        params.append(status)
    if customer_id:
        conditions.append("o.customer_id = %s")
        params.append(customer_id)
    if from_date:
        conditions.append("o.order_date >= %s")
        params.append(from_date)
    if to_date:
        conditions.append("o.order_date <= %s")
        params.append(to_date)

    where_clause = " AND ".join(conditions)

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT o.order_id, o.customer_id, o.order_date, o.status,
                       o.shipping_address, o.notes, o.created_at, o.updated_at,
                       c.name as cust_name, c.email as cust_email
                FROM {ORDERS_TABLE} o
                JOIN {CUSTOMERS_TABLE} c ON o.customer_id = c.customer_id
                WHERE {where_clause}
                ORDER BY o.order_date DESC, o.order_id DESC
                LIMIT %s OFFSET %s
                """,
                (*params, limit, offset),
            )
            rows = cursor.fetchall()
            orders = []
            for row in rows:
                orders.append({
                    "order_id": row[0],
                    "customer": {
                        "customer_id": row[1],
                        "name": row[8],
                        "email": row[9],
                    },
                    "order_date": row[2].isoformat() if row[2] else None,
                    "status": row[3],
                    "shipping_address": row[4],
                    "notes": row[5],
                    "created_at": row[6].isoformat() if row[6] else None,
                    "updated_at": row[7].isoformat() if row[7] else None,
                })
            return orders
    finally:
        return_connection(conn)


def update_order_status(order_id, new_status):
    order_id = validate_id_format(order_id, "order_id")

    if new_status not in VALID_ORDER_STATUSES:
        raise ValueError(f"Invalid status: {new_status}")

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"SELECT status FROM {ORDERS_TABLE} WHERE order_id = %s",
                (order_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise NotFoundError(f"Order '{order_id}' not found")

            current_status = row[0].lower()
            allowed = ORDER_STATUS_TRANSITIONS.get(current_status, set())
            new_status_lower = new_status.lower()
            if new_status_lower not in allowed:
                raise ValueError(
                    f"Cannot change status from '{row[0]}' to '{new_status}'. "
                    f"Allowed: {', '.join(sorted(allowed)) or 'none'}"
                )

            cursor.execute(
                f"""
                UPDATE {ORDERS_TABLE}
                SET status = %s, updated_at = CURRENT_TIMESTAMP
                WHERE order_id = %s
                """,
                (new_status_lower, order_id),
            )

            if cursor.rowcount == 0:
                raise NotFoundError(f"Order '{order_id}' not found")

            conn.commit()
            logger.info(
                "Updated order %s status: %s -> %s", order_id, current_status, new_status,
            )
    except Exception:
        conn.rollback()
        raise
    finally:
        return_connection(conn)

    return get_order_by_id(order_id)


def order_exists(order_id):
    order_id = validate_id_format(order_id, "order_id")
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"SELECT 1 FROM {ORDERS_TABLE} WHERE order_id = %s", (order_id,),
            )
            return cursor.fetchone() is not None
    finally:
        return_connection(conn)


def compute_order_signature(customer_id, items):
    from ..utils.validation import validate_order_items as _vio

    validated = _vio(items)
    total = 0.0
    for item in validated:
        product = _get_product_fast(item["product_id"])
        price = float(product["unit_price"] or 0) if product else 0
        total += item["quantity"] * price
    total = round(total, 2)

    pairs = sorted(
        f"{item['product_id']}:{item['quantity']}" for item in validated
    )
    signature_string = (
        f"{customer_id.upper()}|{'|'.join(pairs)}|{total:.2f}"
    )
    return hashlib.sha256(signature_string.encode()).hexdigest()


def _get_product_fast(product_id):
    from server.services.product_service import get_product_by_id
    return get_product_by_id(product_id)


def get_product_sales_report(from_date=None, to_date=None, product_id=None):
    conditions = ["1=1"]
    params = []

    if from_date:
        conditions.append("o.order_date >= %s")
        params.append(from_date)
    if to_date:
        conditions.append("o.order_date <= %s")
        params.append(to_date)
    if product_id:
        conditions.append("p.product_id = %s")
        params.append(product_id)

    where_clause = " AND ".join(conditions)

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    p.product_id,
                    p.name,
                    p.category,
                    COALESCE(SUM(oi.quantity), 0) as total_quantity_sold,
                    COALESCE(SUM(oi.total), 0) as total_revenue,
                    COUNT(DISTINCT o.order_id) as order_count
                FROM {PRODUCTS_TABLE} p
                LEFT JOIN {ORDER_ITEMS_TABLE} oi ON p.product_id = oi.product_id
                LEFT JOIN {ORDERS_TABLE} o ON oi.order_id = o.order_id
                WHERE {where_clause}
                GROUP BY p.product_id, p.name, p.category, p.product_id
                ORDER BY total_revenue DESC
                """,
                params,
            )
            rows = cursor.fetchall()
            return [_product_sales_row_to_dict(row) for row in rows]
    finally:
        return_connection(conn)


def get_date_sales_report(from_date, to_date):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    DATE(o.order_date) as sale_date,
                    COUNT(DISTINCT o.order_id) as order_count,
                    COALESCE(SUM(oi.total), 0) as total_revenue
                FROM {ORDERS_TABLE} o
                LEFT JOIN {ORDER_ITEMS_TABLE} oi ON o.order_id = oi.order_id
                WHERE o.order_date >= %s AND o.order_date <= %s
                GROUP BY DATE(o.order_date)
                ORDER BY sale_date ASC
                """,
                (from_date, to_date),
            )
            rows = cursor.fetchall()
            return [_date_sales_row_to_dict(row) for row in rows]
    finally:
        return_connection(conn)


def _generate_order_id():
    timestamp = datetime.now().strftime("%Y%m%d%H%M")
    import random
    random_suffix = random.randint(1000, 9999)
    return f"ORD-{timestamp}-{random_suffix}"  # 20 chars max: ORD-YYYYMMDDHHMM-SSSS


def _product_sales_row_to_dict(row):
    return {
        "product_id": row[0],
        "product_name": row[1],
        "category": row[2],
        "total_quantity_sold": int(row[3]) if row[3] else 0,
        "total_revenue": float(round(row[4], 2)) if row[4] else 0,
        "order_count": int(row[5]) if row[5] else 0,
    }


def _date_sales_row_to_dict(row):
    return {
        "date": row[0].isoformat() if row[0] else None,
        "order_count": int(row[1]) if row[1] else 0,
        "total_revenue": float(round(row[2], 2)) if row[2] else 0,
    }
