"""
Customer service - handles all customer-related database operations.
"""
import logging
from contextlib import closing

from ..db import (
    get_connection,
    get_cursor,
    NotFoundError,
    ConflictError,
)
from ..utils.validation import (
    validate_non_empty_string,
    validate_email,
    validate_phone,
    validate_customer_id,
)

logger = logging.getLogger(__name__)
TABLE = "sales.customers"


class CustomerService:
    """Service for managing customers."""

    @staticmethod
    def create_customer(customer_id, name, email, phone=None, address=None):
        """Create a new customer."""
        # Validate inputs
        customer_id = validate_customer_id(customer_id)
        name = validate_non_empty_string(name, "Customer name", max_length=200)
        email = validate_email(email)
        phone = validate_phone(phone)
        address = validate_non_empty_string(address, "Address", max_length=1000) if address else None

        with get_cursor() as cursor:
            try:
                cursor.execute(
                    f"""
                    INSERT INTO {TABLE} (customer_id, name, email, phone, address)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, customer_id, name, email, phone, address, created_at
                    """,
                    (customer_id, name, email, phone, address)
                )
                row = cursor.fetchone()
                logger.info("Created customer: %s (%s)", customer_id, row[0])
                return CustomerService._row_to_dict(row)
            except Exception as e:
                # Check for duplicate
                if "unique" in str(e).lower() or "duplicate" in str(e).lower():
                    raise ConflictError(f"Customer with ID '{customer_id}' or email '{email}' already exists")
                raise

    @staticmethod
    def get_customer_by_id(customer_id_str):
        """Get a customer by their customer_id."""
        customer_id_str = validate_customer_id(customer_id_str)

        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT id, customer_id, name, email, phone, address, created_at, updated_at
                    FROM {TABLE}
                    WHERE customer_id = %s
                    """,
                    (customer_id_str,)
                )
                row = cursor.fetchone()
                if not row:
                    raise NotFoundError(f"Customer '{customer_id_str}' not found")
                return CustomerService._row_to_dict(row)

    @staticmethod
    def get_customer_by_email(email):
        """Get a customer by email."""
        email = validate_email(email)

        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT id, customer_id, name, email, phone, address, created_at, updated_at
                    FROM {TABLE}
                    WHERE email = %s
                    """,
                    (email,)
                )
                row = cursor.fetchone()
                if not row:
                    return None
                return CustomerService._row_to_dict(row)

    @staticmethod
    def get_all_customers(limit=100, offset=0):
        """Get all customers with pagination."""
        limit = max(1, min(int(limit), 500))
        offset = max(0, int(offset))

        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT id, customer_id, name, email, phone, address, created_at, updated_at
                    FROM {TABLE}
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    (limit, offset)
                )
                rows = cursor.fetchall()
                return [CustomerService._row_to_dict(row) for row in rows]

    @staticmethod
    def count_customers():
        """Get total customer count."""
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"SELECT COUNT(*) FROM {TABLE}")
                return cursor.fetchone()[0]

    @staticmethod
    def _row_to_dict(row):
        """Convert a database row to a dictionary."""
        return {
            "id": row[0],
            "customer_id": row[1],
            "name": row[2],
            "email": row[3],
            "phone": row[4],
            "address": row[5],
            "created_at": row[6].isoformat() if row[6] else None,
            "updated_at": row[7].isoformat() if row[7] else None,
        }
