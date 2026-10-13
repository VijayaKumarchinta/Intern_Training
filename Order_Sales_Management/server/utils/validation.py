"""
Shared input validators for Order & Sales Management Application.
Validation happens BEFORE any database call.
"""
import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation


def validate_non_empty_string(value, field_name, max_length=200):
    """Validate a non-empty string field."""
    if value is None:
        raise ValueError(f"{field_name} is required")
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    value = value.strip()
    if not value:
        raise ValueError(f"{field_name} cannot be empty")
    if len(value) > max_length:
        raise ValueError(f"{field_name} exceeds maximum length of {max_length}")
    return value


def validate_email(email):
    """Basic email validation."""
    if not email or not isinstance(email, str):
        raise ValueError("Email is required and must be a string")
    email = email.strip().lower()
    if len(email) > 255:
        raise ValueError("Email exceeds maximum length")
    # Basic email pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValueError("Invalid email format")
    return email


def validate_phone(phone):
    """Optional phone validation if provided."""
    if phone is None:
        return None
    if not isinstance(phone, str):
        raise ValueError("Phone must be a string")
    phone = phone.strip()
    if phone and len(phone) > 50:
        raise ValueError("Phone number exceeds maximum length")
    return phone


def validate_positive_decimal(value, field_name, max_value=None):
    """Validate a positive decimal number."""
    if value is None:
        raise ValueError(f"{field_name} is required")
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f"{field_name} must be a valid number")

    if decimal_value < 0:
        raise ValueError(f"{field_name} must be non-negative")

    if max_value is not None and decimal_value > max_value:
        raise ValueError(f"{field_name} exceeds maximum allowed value")

    return decimal_value


def validate_positive_int(value, field_name, max_value=None):
    """Validate a positive integer."""
    if value is None:
        raise ValueError(f"{field_name} is required")
    try:
        int_value = int(value)
    except (ValueError, TypeError):
        raise ValueError(f"{field_name} must be a valid integer")

    if int_value <= 0:
        raise ValueError(f"{field_name} must be positive")

    if max_value is not None and int_value > max_value:
        raise ValueError(f"{field_name} exceeds maximum allowed value")

    return int_value


def validate_order_id(order_id):
    """Validate order ID format."""
    if not order_id or not isinstance(order_id, str):
        raise ValueError("Order ID is required")
    order_id = order_id.strip().upper()
    if len(order_id) > 50:
        raise ValueError("Order ID exceeds maximum length")
    if not re.match(r'^[A-Z0-9-]+$', order_id):
        raise ValueError("Order ID must contain only letters, numbers, and hyphens")
    return order_id


def validate_product_id(product_id):
    """Validate product ID format."""
    if not product_id or not isinstance(product_id, str):
        raise ValueError("Product ID is required")
    product_id = product_id.strip().upper()
    if len(product_id) > 50:
        raise ValueError("Product ID exceeds maximum length")
    if not re.match(r'^[A-Z0-9-]+$', product_id):
        raise ValueError("Product ID must contain only letters, numbers, and hyphens")
    return product_id


def validate_customer_id(customer_id):
    """Validate customer ID format."""
    if not customer_id or not isinstance(customer_id, str):
        raise ValueError("Customer ID is required")
    customer_id = customer_id.strip().upper()
    if len(customer_id) > 50:
        raise ValueError("Customer ID exceeds maximum length")
    if not re.match(r'^[A-Z0-9-]+$', customer_id):
        raise ValueError("Customer ID must contain only letters, numbers, and hyphens")
    return customer_id


def validate_order_date(date_str):
    """Validate and parse order date."""
    if date_str is None:
        return datetime.now(timezone.utc)

    if not isinstance(date_str, str):
        raise ValueError("Order date must be a string")

    date_str = date_str.strip()
    if not date_str:
        return datetime.now(timezone.utc)

    try:
        # Handle ISO format with timezone
        if date_str.endswith('Z'):
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        else:
            dt = datetime.fromisoformat(date_str)

        # Make timezone-aware if naive
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        # Validate not in the future
        now = datetime.now(timezone.utc)
        if dt > now:
            raise ValueError("Order date cannot be in the future")

        return dt
    except ValueError as e:
        if "Order date cannot be in the future" in str(e):
            raise
        raise ValueError(f"Invalid date format: {date_str}. Use ISO format (YYYY-MM-DDTHH:MM:SS)")


def validate_status_transition(current_status, new_status):
    """Validate that a status transition is allowed."""
    from Order_Sales_Management.server.config import (
        ORDER_STATUS_TRANSITIONS,
        ORDER_STATUS_VALID_STATUSES,
        ValidationError,
    )

    if new_status not in ORDER_STATUS_VALID_STATUSES:
        raise ValueError(f"Invalid status: {new_status}")

    if current_status not in ORDER_STATUS_TRANSITIONS:
        raise ValueError(f"Unknown current status: {current_status}")

    allowed = ORDER_STATUS_TRANSITIONS[current_status]
    if new_status not in allowed:
        raise ValueError(
            f"Cannot transition from '{current_status}' to '{new_status}'. "
            f"Allowed transitions: {', '.join(sorted(allowed)) or 'none (final state)'}"
        )

    return new_status


def validate_order_items(items):
    """Validate a list of order items."""
    if not items or not isinstance(items, list):
        raise ValueError("Order must contain at least one item")

    if len(items) > 100:
        raise ValueError("Order cannot contain more than 100 items")

    validated_items = []
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"Item {i + 1} must be an object")

        # Validate required fields
        product_id = validate_product_id(item.get('product_id'))
        quantity = validate_positive_int(item.get('quantity'), f"Item {i + 1} quantity", max_value=10000)

        # Optional unit_price (if not provided, will be fetched from product catalog)
        unit_price = None
        if 'unit_price' in item and item['unit_price'] is not None:
            unit_price = validate_positive_decimal(item['unit_price'], f"Item {i + 1} unit price", max_value=1000000)

        validated_items.append({
            'product_id': product_id,
            'quantity': quantity,
            'unit_price': unit_price,  # None means use catalog price
        })

    return validated_items


def validate_discount(value, max_discount_percentage=100):
    """Validate discount percentage."""
    if value is None:
        return Decimal('0')

    discount = validate_positive_decimal(value, "Discount", max_value=max_discount_percentage)

    # Convert percentage to decimal if > 1 (handle both 10 and 0.10 formats)
    if discount > 1:
        discount = discount / Decimal('100')

    return discount
