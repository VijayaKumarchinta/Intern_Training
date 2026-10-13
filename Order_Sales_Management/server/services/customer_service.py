import logging

from ..db import get_connection, return_connection, NotFoundError, ConflictError, qualified
from ..utils.validation import (
    validate_non_empty_string,
    validate_email,
    validate_customer_id,
)

logger = logging.getLogger(__name__)
TABLE = qualified("customers")


def create_customer(customer_id, name, email, phone=None, address=None):
    customer_id = validate_customer_id(customer_id)
    name = validate_non_empty_string(name, "Customer name")
    email = validate_email(email)

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                INSERT INTO {TABLE} (customer_id, name, email, phone, address)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (customer_id) DO NOTHING
                RETURNING customer_id, name, email, phone, address, created_at
                """,
                (customer_id, name, email, phone, address),
            )
            row = cursor.fetchone()
            if not row:
                raise ConflictError(f"Customer with ID '{customer_id}' already exists")
            conn.commit()
            logger.info("Created customer: %s", customer_id)
            return _row_to_dict(row)
    except Exception as e:
        conn.rollback()
        if isinstance(e, ConflictError):
            raise
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            raise ConflictError(f"Customer with ID '{customer_id}' already exists")
        raise
    finally:
        return_connection(conn)


def get_customer_by_id(customer_id_str):
    customer_id_str = validate_customer_id(customer_id_str)

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT customer_id, name, email, phone, address, created_at
                FROM {TABLE}
                WHERE customer_id = %s
                """,
                (customer_id_str,),
            )
            row = cursor.fetchone()
            if not row:
                raise NotFoundError(f"Customer '{customer_id_str}' not found")
            return _row_to_dict(row)
    finally:
        return_connection(conn)


def get_all_customers():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT customer_id, name, email, phone, address, created_at
                FROM {TABLE}
                ORDER BY created_at DESC
                """
            )
            rows = cursor.fetchall()
            return [_row_to_dict(row) for row in rows]
    finally:
        return_connection(conn)


def count_customers():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM {TABLE}")
            return cursor.fetchone()[0]
    finally:
        return_connection(conn)


def _row_to_dict(row):
    return {
        "customer_id": row[0],
        "name": row[1],
        "email": row[2],
        "phone": row[3],
        "address": row[4],
        "created_at": row[5].isoformat() if row[5] else None,
    }
