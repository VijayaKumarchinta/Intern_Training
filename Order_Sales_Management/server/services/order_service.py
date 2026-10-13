"""
Order service - handles order processing, validation, calculation, status tracking,
and duplicate detection.
"""
import hashlib
import logging
from datetime import datetime, timezone
from decimal import Decimal
from contextlib import closing

from ..db import (
    get_connection,
    get_cursor,
    NotFoundError,
    ConflictError,
    ValidationError as DbValidationError,
)
from ..config import (
    DEFAULT_TAX_RATE,
    DEFAULT_DISCOUNT_RATE,
    ORDER_STATUS_TRANSITIONS,
)
from ..utils.validation import (
    validate_order_id,
    validate_order_date,
    validate_status_transition,
    validate_order_items,
    validate_discount,
    validate_non_empty_string,
)

logger = logging.getLogger(__name__)
ORDERS_TABLE = "sales.orders"
ORDER_ITEMS_TABLE = "sales.order_items"
SIGNATURES_TABLE = "sales.order_signatures"
CUSTOMERS_TABLE = "sales.customers"
PRODUCTS_TABLE = "sales.products"


class OrderService:
    """Service for managing orders."""

    @staticmethod
    def create_order(customer_id, items, order_id=None, order_date=None,
                     shipping_address=None, notes=None, discount_percent=None):
        """
        Create a new order with full validation and calculation.

        Args:
            customer_id: Customer ID string
            items: List of dicts with product_id, quantity, and optional unit_price
            order_id: Optional custom order ID (auto-generated if not provided)
            order_date: Optional order date (defaults to now)
            shipping_address: Optional shipping address
            notes: Optional order notes
            discount_percent: Optional discount percentage (0-100)

        Returns:
            Created order dict with all items
        """
        # Validate customer exists
        from Order_Sales_Management.server.services.customer_service import CustomerService
        customer = CustomerService.get_customer_by_id(customer_id)
        customer_internal_id = customer['id']

        # Validate and process items
        validated_items = validate_order_items(items)

        # Generate order ID if not provided
        if order_id:
            order_id = validate_order_id(order_id)
        else:
            order_id = OrderService._generate_order_id()

        # Parse order date
        parsed_date = validate_order_date(order_date)

        # Validate and parse discount
        discount_percent = validate_discount(discount_percent, max_discount_percentage=100)

        # Calculate totals
        subtotal, item_details, insufficient_stock = OrderService._calculate_items(
            validated_items, discount_percent
        )

        if insufficient_stock:
            stock_issues = "; ".join(insufficient_stock)
            raise DbValidationError(f"Insufficient stock: {stock_issues}")

        # Calculate tax and total
        tax_amount = subtotal * Decimal(str(DEFAULT_TAX_RATE)) / Decimal('100')
        discount_amount = subtotal * discount_percent
        total = subtotal - discount_amount + tax_amount

        # Check for duplicate order
        order_signature = OrderService._generate_signature(customer_id, items, subtotal)
        if OrderService._signature_exists(order_signature):
            raise ConflictError("A similar order already exists (duplicate detection)")

        # Create order in transaction
        with get_cursor() as cursor:
            # Insert order
            cursor.execute(
                f"""
                INSERT INTO {ORDERS_TABLE}
                    (order_id, customer_id, order_date, status, subtotal, discount, tax, total,
                     shipping_address, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    order_id,
                    customer_internal_id,
                    parsed_date,
                    "pending",
                    float(subtotal),
                    float(discount_amount),
                    float(tax_amount),
                    float(total),
                    shipping_address,
                    notes,
                )
            )
            order_internal_id = cursor.fetchone()[0]

            # Insert order items and update stock
            for item in item_details:
                cursor.execute(
                    f"""
                    INSERT INTO {ORDER_ITEMS_TABLE}
                        (order_id, product_id, quantity, unit_price, subtotal, discount)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        order_internal_id,
                        item['product_internal_id'],
                        item['quantity'],
                        float(item['unit_price']),
                        float(item['subtotal']),
                        float(item['discount']),
                    )
                )

                # Update stock
                new_stock = item['product_stock'] - item['quantity']
                cursor.execute(
                    f"UPDATE {PRODUCTS_TABLE} SET stock_quantity = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                    (new_stock, item['product_internal_id'])
                )

            # Record signature for duplicate detection
            cursor.execute(
                f"""
                INSERT INTO {SIGNATURES_TABLE} (order_signature, order_id)
                VALUES (%s, %s)
                """,
                (order_signature, order_id)
            )

            logger.info("Created order: %s for customer %s, total: $%s",
                       order_id, customer_id, total)

        # Return the created order
        return OrderService.get_order_by_id(order_id)

    @staticmethod
    def get_order_by_id(order_id):
        """Get an order by its order_id."""
        order_id = validate_order_id(order_id)

        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT o.id, o.order_id, o.customer_id, o.order_date, o.status,
                           o.subtotal, o.discount, o.tax, o.total, o.shipping_address,
                           o.notes, o.created_at, o.updated_at,
                           c.customer_id as cust_id, c.name as cust_name, c.email as cust_email
                    FROM {ORDERS_TABLE} o
                    JOIN {CUSTOMERS_TABLE} c ON o.customer_id = c.id
                    WHERE o.order_id = %s
                    """,
                    (order_id,)
                )
                row = cursor.fetchone()
                if not row:
                    raise NotFoundError(f"Order '{order_id}' not found")

                order = OrderService._order_row_to_dict(row)

                # Get order items
                cursor.execute(
                    f"""
                    SELECT oi.id, oi.product_id, oi.quantity, oi.unit_price, oi.subtotal, oi.discount,
                           p.product_id as prod_id, p.name as prod_name, p.category as prod_category
                    FROM {ORDER_ITEMS_TABLE} oi
                    JOIN {PRODUCTS_TABLE} p ON oi.product_id = p.id
                    WHERE oi.order_id = %s
                    ORDER BY oi.id
                    """,
                    (row[0],)  # order internal id
                )
                items = []
                for item_row in cursor.fetchall():
                    items.append({
                        "id": item_row[0],
                        "product_id": item_row[6],
                        "product_name": item_row[7],
                        "category": item_row[8],
                        "quantity": item_row[2],
                        "unit_price": float(item_row[3]) if item_row[3] else None,
                        "subtotal": float(item_row[4]) if item_row[4] else 0,
                        "discount": float(item_row[5]) if item_row[5] else 0,
                    })

                order['items'] = items
                return order

    @staticmethod
    def get_all_orders(limit=100, offset=0, status=None, customer_id=None,
                       from_date=None, to_date=None):
        """Get all orders with optional filtering."""
        limit = max(1, min(int(limit), 500))
        offset = max(0, int(offset))

        conditions = []
        params = []

        if status:
            conditions.append("o.status = %s")
            params.append(status)
        if customer_id:
            conditions.append("c.customer_id = %s")
            params.append(customer_id)
        if from_date:
            conditions.append("o.order_date >= %s")
            params.append(from_date)
        if to_date:
            conditions.append("o.order_date <= %s")
            params.append(to_date)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT o.id, o.order_id, o.customer_id, o.order_date, o.status,
                           o.subtotal, o.discount, o.tax, o.total, o.shipping_address,
                           o.notes, o.created_at, o.updated_at,
                           c.customer_id as cust_id, c.name as cust_name, c.email as cust_email
                    FROM {ORDERS_TABLE} o
                    JOIN {CUSTOMERS_TABLE} c ON o.customer_id = c.id
                    {where_clause}
                    ORDER BY o.order_date DESC, o.id DESC
                    LIMIT %s OFFSET %s
                    """,
                    (*params, limit, offset)
                )
                rows = cursor.fetchall()
                orders = []
                for row in rows:
                    order = OrderService._order_row_to_dict(row)
                    # Get items count
                    cursor.execute(
                        f"SELECT COUNT(*) FROM {ORDER_ITEMS_TABLE} WHERE order_id = %s",
                        (row[0],)
                    )
                    order['items_count'] = cursor.fetchone()[0]
                    order['items'] = []  # Don't fetch full items for list view
                    orders.append(order)
                return orders

    @staticmethod
    def update_order_status(order_id, new_status):
        """Update order status with transition validation."""
        order_id = validate_order_id(order_id)
        new_status = validate_status_transition(None, new_status)  # Basic validation

        with get_connection() as conn:
            with conn.cursor() as cursor:
                # Get current status
                cursor.execute(
                    f"SELECT status FROM {ORDERS_TABLE} WHERE order_id = %s",
                    (order_id,)
                )
                row = cursor.fetchone()
                if not row:
                    raise NotFoundError(f"Order '{order_id}' not found")

                current_status = row[0]

                # Validate transition
                if current_status not in ORDER_STATUS_TRANSITIONS:
                    raise DbValidationError(f"Cannot update status of order in '{current_status}' state")

                allowed = ORDER_STATUS_TRANSITIONS[current_status]
                if new_status not in allowed:
                    raise DbValidationError(
                        f"Cannot transition from '{current_status}' to '{new_status}'. "
                        f"Allowed: {', '.join(sorted(allowed)) or 'none'}"
                    )

                cursor.execute(
                    f"""
                    UPDATE {ORDERS_TABLE}
                    SET status = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE order_id = %s
                    """,
                    (new_status, order_id)
                )

                if cursor.rowcount == 0:
                    raise NotFoundError(f"Order '{order_id}' not found")

                logger.info("Updated order %s status: %s -> %s", order_id, current_status, new_status)

        return OrderService.get_order_by_id(order_id)

    @staticmethod
    def get_product_sales_report(from_date=None, to_date=None, product_id=None):
        """
        Generate product-wise sales report.

        Returns list of products with total quantity sold, revenue, etc.
        """
        conditions = ["oi.order_date IS NOT NULL"]
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

        where_clause = f"WHERE {' AND '.join(conditions)}"

        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT
                        p.id,
                        p.product_id,
                        p.name,
                        p.category,
                        p.unit_price,
                        COALESCE(SUM(oi.quantity), 0) as total_quantity_sold,
                        COALESCE(SUM(oi.subtotal), 0) as total_revenue,
                        COALESCE(SUM(oi.discount), 0) as total_discounts,
                        COUNT(DISTINCT o.id) as order_count,
                        MAX(o.order_date) as last_sold
                    FROM {PRODUCTS_TABLE} p
                    LEFT JOIN {ORDER_ITEMS_TABLE} oi ON p.id = oi.product_id
                    LEFT JOIN {ORDERS_TABLE} o ON oi.order_id = o.id AND o.status NOT IN ('cancelled', 'returned')
                    {where_clause}
                    GROUP BY p.id, p.product_id, p.name, p.category, p.unit_price
                    ORDER BY total_revenue DESC
                    """,
                    params
                )
                rows = cursor.fetchall()
                return [OrderService._product_sales_row_to_dict(row) for row in rows]

    @staticmethod
    def get_date_sales_report(from_date, to_date):
        """
        Generate date-wise sales report.

        Returns daily sales aggregates for the given date range.
        """
        from_date = validate_order_date(from_date)
        to_date = validate_order_date(to_date)

        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT
                        DATE(o.order_date) as sale_date,
                        COUNT(DISTINCT o.id) as order_count,
                        COUNT(oi.id) as item_count,
                        COALESCE(SUM(o.subtotal), 0) as total_subtotal,
                        COALESCE(SUM(o.discount), 0) as total_discounts,
                        COALESCE(SUM(o.tax), 0) as total_tax,
                        COALESCE(SUM(o.total), 0) as total_revenue,
                        COUNT(DISTINCT o.customer_id) as unique_customers
                    FROM {ORDERS_TABLE} o
                    LEFT JOIN {ORDER_ITEMS_TABLE} oi ON o.id = oi.order_id
                    WHERE o.order_date >= %s AND o.order_date <= %s
                      AND o.status NOT IN ('cancelled', 'returned')
                    GROUP BY DATE(o.order_date)
                    ORDER BY sale_date ASC
                    """,
                    (from_date, to_date)
                )
                rows = cursor.fetchall()
                return [OrderService._date_sales_row_to_dict(row) for row in rows]

    @staticmethod
    def check_duplicate_order(customer_id, items, subtotal):
        """
        Check if a similar order already exists (for duplicate detection).

        Compares: customer_id, product mix, and total amount.
        """
        signature = OrderService._generate_signature(customer_id, items, subtotal)
        exists = OrderService._signature_exists(signature)
        return {
            "is_duplicate": exists,
            "signature": signature,
        }

    @staticmethod
    def _generate_order_id():
        """Generate a unique order ID."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        import random
        random_suffix = random.randint(1000, 9999)
        return f"ORD-{timestamp}-{random_suffix}"

    @staticmethod
    def _generate_signature(customer_id, items, subtotal):
        """
        Generate a unique signature for duplicate detection.
        Uses customer_id + sorted product IDs + quantities + rounded subtotal.
        """
        # Create a deterministic representation
        item_signatures = []
        for item in sorted(items, key=lambda x: x.get('product_id', '')):
            product_id = item.get('product_id', '')
            quantity = item.get('quantity', 0)
            item_signatures.append(f"{product_id}:{quantity}")

        items_str = "|".join(item_signatures)
        subtotal_rounded = str(round(float(subtotal), 2))

        signature_string = f"{customer_id.upper()}|{items_str}|{subtotal_rounded}"
        return hashlib.sha256(signature_string.encode()).hexdigest()

    @staticmethod
    def _signature_exists(signature):
        """Check if a signature already exists in the database."""
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"SELECT 1 FROM {SIGNATURES_TABLE} WHERE order_signature = %s",
                    (signature,)
                )
                return cursor.fetchone() is not None

    @staticmethod
    def _calculate_items(validated_items, discount_percent):
        """
        Calculate item totals and validate stock availability.

        Returns: (subtotal, item_details, insufficient_stock_list)
        """
        item_details = []
        insufficient_stock = []
        subtotal = Decimal('0')

        for item in validated_items:
            product_id = item['product_id']
            quantity = item['quantity']
            provided_price = item['unit_price']

            # Get product from database
            from Order_Sales_Management.server.services.product_service import ProductService
            try:
                product = ProductService.get_product_by_id(product_id)
            except NotFoundError:
                insufficient_stock.append(f"Product '{product_id}' not found")
                continue

            # Use provided price or catalog price
            if provided_price is not None:
                unit_price = Decimal(str(provided_price))
            else:
                unit_price = Decimal(str(product['unit_price'] or 0))

            # Check stock
            if quantity > product['stock_quantity']:
                insufficient_stock.append(
                    f"Product '{product_id}' ({product['name']}): "
                    f"requested {quantity}, available {product['stock_quantity']}"
                )
                continue

            # Calculate item totals
            item_subtotal = unit_price * quantity
            item_discount = item_subtotal * discount_percent
            item_total = item_subtotal - item_discount

            subtotal += item_subtotal

            item_details.append({
                'product_internal_id': product['id'],
                'product_id': product_id,
                'product_name': product['name'],
                'product_stock': product['stock_quantity'],
                'quantity': quantity,
                'unit_price': unit_price,
                'subtotal': item_subtotal,
                'discount': item_discount,
                'total': item_total,
            })

        return subtotal, item_details, insufficient_stock

    @staticmethod
    def _order_row_to_dict(row):
        """Convert order database row to dictionary."""
        return {
            "id": row[0],
            "order_id": row[1],
            "customer": {
                "customer_id": row[13],
                "name": row[14],
                "email": row[15],
            },
            "order_date": row[3].isoformat() if row[3] else None,
            "status": row[4],
            "subtotal": float(row[5]) if row[5] else 0,
            "discount": float(row[6]) if row[6] else 0,
            "tax": float(row[7]) if row[7] else 0,
            "total": float(row[8]) if row[8] else 0,
            "shipping_address": row[9],
            "notes": row[10],
            "created_at": row[11].isoformat() if row[11] else None,
            "updated_at": row[12].isoformat() if row[12] else None,
        }

    @staticmethod
    def _product_sales_row_to_dict(row):
        """Convert product sales report row to dictionary."""
        return {
            "product_id": row[1],
            "product_name": row[2],
            "category": row[3],
            "unit_price": float(row[4]) if row[4] else 0,
            "total_quantity_sold": int(row[5]) if row[5] else 0,
            "total_revenue": float(row[6]) if row[6] else 0,
            "total_discounts": float(row[7]) if row[7] else 0,
            "order_count": int(row[8]) if row[8] else 0,
            "last_sold": row[9].isoformat() if row[9] else None,
        }

    @staticmethod
    def _date_sales_row_to_dict(row):
        """Convert date sales report row to dictionary."""
        return {
            "date": row[0].isoformat() if row[0] else None,
            "order_count": int(row[1]) if row[1] else 0,
            "item_count": int(row[2]) if row[2] else 0,
            "total_subtotal": float(row[3]) if row[3] else 0,
            "total_discounts": float(row[4]) if row[4] else 0,
            "total_tax": float(row[5]) if row[5] else 0,
            "total_revenue": float(row[6]) if row[6] else 0,
            "unique_customers": int(row[7]) if row[7] else 0,
        }
