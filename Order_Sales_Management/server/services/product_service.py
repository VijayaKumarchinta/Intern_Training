"""
Product service - handles all product-related database operations.
"""
import logging
from decimal import Decimal

from ..db import (
    get_connection,
    get_cursor,
    NotFoundError,
    ConflictError,
    ValidationError,
)
from ..utils.validation import (
    validate_non_empty_string,
    validate_positive_decimal,
    validate_positive_int,
    validate_product_id,
)


logger = logging.getLogger(__name__)
TABLE = "sales.products"


class ProductService:
    """Service for managing products."""

    @staticmethod
    def create_product(product_id, name, description=None, category=None,
                       unit_price=None, stock_quantity=0):
        """Create a new product."""
        product_id = validate_product_id(product_id)
        name = validate_non_empty_string(name, "Product name", max_length=200)
        description = validate_non_empty_string(description, "Description", max_length=1000) if description else None
        category = validate_non_empty_string(category, "Category", max_length=100) if category else None

        if unit_price is not None:
            unit_price = validate_positive_decimal(unit_price, "Unit price", max_value=1000000)
        else:
            raise ValidationError("Unit price is required")

        stock_quantity = validate_positive_int(stock_quantity, "Stock quantity", max_value=1000000) if stock_quantity else 0

        with get_cursor() as cursor:
            try:
                cursor.execute(
                    f"""
                    INSERT INTO {TABLE} (product_id, name, description, category, unit_price, stock_quantity)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id, product_id, name, description, category, unit_price, stock_quantity, created_at
                    """,
                    (product_id, name, description, category, float(unit_price), stock_quantity)
                )
                row = cursor.fetchone()
                logger.info("Created product: %s (%s) - $%s", product_id, name, unit_price)
                return ProductService._row_to_dict(row)
            except Exception as e:
                if "unique" in str(e).lower() or "duplicate" in str(e).lower():
                    raise ConflictError(f"Product with ID '{product_id}' already exists")
                raise

    @staticmethod
    def get_product_by_id(product_id_str):
        """Get a product by product_id."""
        product_id_str = validate_product_id(product_id_str)

        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT id, product_id, name, description, category, unit_price, stock_quantity,
                           created_at, updated_at
                    FROM {TABLE}
                    WHERE product_id = %s
                    """,
                    (product_id_str,)
                )
                row = cursor.fetchone()
                if not row:
                    raise NotFoundError(f"Product '{product_id_str}' not found")
                return ProductService._row_to_dict(row)

    @staticmethod
    def get_product_by_id_internal(product_id_int):
        """Get a product by internal ID (for order processing)."""
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT id, product_id, name, description, category, unit_price, stock_quantity,
                           created_at, updated_at
                    FROM {TABLE}
                    WHERE id = %s
                    """,
                    (product_id_int,)
                )
                row = cursor.fetchone()
                if not row:
                    raise NotFoundError(f"Product with internal ID {product_id_int} not found")
                return ProductService._row_to_dict(row)

    @staticmethod
    def get_all_products(limit=100, offset=0, category=None, search=None):
        """Get all products with optional filtering."""
        limit = max(1, min(int(limit), 500))
        offset = max(0, int(offset))

        conditions = []
        params = []

        if category:
            conditions.append("category = %s")
            params.append(category)
        if search:
            conditions.append("(name ILIKE %s OR description ILIKE %s OR product_id ILIKE %s)")
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param])

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT id, product_id, name, description, category, unit_price, stock_quantity,
                           created_at, updated_at
                    FROM {TABLE}
                    {where_clause}
                    ORDER BY name ASC
                    LIMIT %s OFFSET %s
                    """,
                    (*params, limit, offset)
                )
                rows = cursor.fetchall()
                return [ProductService._row_to_dict(row) for row in rows]

    @staticmethod
    def update_stock(product_id_str, quantity_change):
        """Update product stock (positive for add, negative for reduce)."""
        product_id_str = validate_product_id(product_id_str)
        quantity_change = int(quantity_change)

        with get_cursor() as cursor:
            # Get current stock
            cursor.execute(f"SELECT stock_quantity FROM {TABLE} WHERE product_id = %s", (product_id_str,))
            row = cursor.fetchone()
            if not row:
                raise NotFoundError(f"Product '{product_id_str}' not found")

            current_stock = row[0]
            new_stock = current_stock + quantity_change

            if new_stock < 0:
                raise ValidationError(f"Insufficient stock. Current: {current_stock}, requested change: {quantity_change}")

            cursor.execute(
                f"UPDATE {TABLE} SET stock_quantity = %s, updated_at = CURRENT_TIMESTAMP WHERE product_id = %s",
                (new_stock, product_id_str)
            )

            if cursor.rowcount == 0:
                raise NotFoundError(f"Product '{product_id_str}' not found")

            logger.info("Updated stock for %s: %s -> %s", product_id_str, current_stock, new_stock)
            return new_stock

    @staticmethod
    def count_products():
        """Get total product count."""
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"SELECT COUNT(*) FROM {TABLE}")
                return cursor.fetchone()[0]

    @staticmethod
    def _row_to_dict(row):
        """Convert a database row to a dictionary."""
        return {
            "id": row[0],
            "product_id": row[1],
            "name": row[2],
            "description": row[3],
            "category": row[4],
            "unit_price": float(row[5]) if row[5] is not None else None,
            "stock_quantity": row[6],
            "created_at": row[7].isoformat() if row[7] else None,
            "updated_at": row[8].isoformat() if row[8] else None,
        }
