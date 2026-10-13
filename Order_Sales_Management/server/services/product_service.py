import logging

from ..db import get_connection, return_connection, NotFoundError, ConflictError, qualified
from ..utils.validation import (
    validate_non_empty_string,
    validate_id_format,
)

logger = logging.getLogger(__name__)
TABLE = qualified("products")


def create_product(product_id, name, unit_price, description=None, category=None):
    product_id = validate_id_format(product_id, "product_id")
    name = validate_non_empty_string(name, "Product name")

    try:
        price = float(unit_price)
        if price < 0:
            raise ValueError("Unit price must be non-negative")
    except (ValueError, TypeError):
        raise ValueError("Unit price must be a valid number")

    description = (
        validate_non_empty_string(description, "Description", max_length=1000)
        if description else None
    )
    category = (
        validate_non_empty_string(category, "Category", max_length=100)
        if category else None
    )

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                INSERT INTO {TABLE} (product_id, name, description, category, unit_price, stock_quantity)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (product_id) DO NOTHING
                RETURNING product_id, name, description, category, unit_price, stock_quantity, created_at
                """,
                (product_id, name, description, category, price, 100),
            )
            row = cursor.fetchone()
            if not row:
                raise ConflictError(f"Product with ID '{product_id}' already exists")
            conn.commit()
            logger.info("Created product: %s - %s", product_id, name)
            return _row_to_dict(row)
    except Exception as e:
        conn.rollback()
        if isinstance(e, ConflictError):
            raise
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            raise ConflictError(f"Product with ID '{product_id}' already exists")
        raise
    finally:
        return_connection(conn)


def get_product_by_id(product_id_str):
    product_id_str = validate_id_format(product_id_str, "product_id")

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT product_id, name, description, category, unit_price, stock_quantity, created_at
                FROM {TABLE}
                WHERE product_id = %s
                """,
                (product_id_str,),
            )
            row = cursor.fetchone()
            if not row:
                raise NotFoundError(f"Product '{product_id_str}' not found")
            return _row_to_dict(row)
    finally:
        return_connection(conn)


def get_all_products():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT product_id, name, description, category, unit_price, stock_quantity, created_at
                FROM {TABLE}
                ORDER BY name ASC
                """
            )
            rows = cursor.fetchall()
            return [_row_to_dict(row) for row in rows]
    finally:
        return_connection(conn)


def count_products():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM {TABLE}")
            return cursor.fetchone()[0]
    finally:
        return_connection(conn)


def _row_to_dict(row):
    return {
        "product_id": row[0],
        "name": row[1],
        "description": row[2],
        "category": row[3],
        "unit_price": float(row[4]) if row[4] is not None else None,
        "stock_quantity": row[5],
        "created_at": row[6].isoformat() if row[6] else None,
    }
