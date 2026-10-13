import re
from datetime import datetime, timezone


def validate_non_empty_string(value, field_name, max_length=200):
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
    if not email or not isinstance(email, str):
        raise ValueError("Email is required and must be a string")
    email = email.strip().lower()
    if len(email) > 255:
        raise ValueError("Email exceeds maximum length")
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValueError("Invalid email format")
    return email


def validate_positive_number(value, field_name):
    try:
        num = float(value)
    except (ValueError, TypeError):
        raise ValueError(f"{field_name} must be a valid number")
    if num < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return num


def validate_positive_int(value, field_name):
    try:
        int_value = int(value)
    except (ValueError, TypeError):
        raise ValueError(f"{field_name} must be a valid integer")
    if int_value <= 0:
        raise ValueError(f"{field_name} must be positive")
    return int_value


def validate_id_format(value, field_name):
    if not value or not isinstance(value, str):
        raise ValueError(f"{field_name} is required")
    value = value.strip().upper()
    if len(value) > 50:
        raise ValueError(f"{field_name} exceeds maximum length")
    if not re.match(r'^[A-Z0-9-]+$', value):
        raise ValueError(f"{field_name} must contain only letters, numbers, and hyphens")
    return value


def validate_customer_id(customer_id):
    return validate_id_format(customer_id, "customer_id")


def validate_product_id(product_id):
    return validate_id_format(product_id, "product_id")


def validate_order_id(order_id):
    return validate_id_format(order_id, "order_id")


def validate_order_date(date_str):
    if date_str is None:
        return datetime.now(timezone.utc)

    if not isinstance(date_str, str):
        date_str = str(date_str)

    date_str = date_str.strip()
    if not date_str:
        raise ValueError("Order date cannot be empty")

    try:
        if date_str.endswith('Z'):
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        else:
            dt = datetime.fromisoformat(date_str)

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        if dt > now:
            raise ValueError("Order date cannot be in the future")

        return dt
    except ValueError as e:
        if "Order date cannot be in the future" in str(e):
            raise
        raise ValueError(f"Invalid date format: {date_str}")


VALID_ORDER_STATUSES = {
    "pending",
    "processing",
    "shipped",
    "delivered",
    "cancelled",
}

ORDER_STATUS_TRANSITIONS = {
    "pending": {"processing", "cancelled"},
    "processing": {"shipped", "cancelled"},
    "shipped": {"delivered"},
    "delivered": set(),
    "cancelled": set(),
}


def validate_status_transition(current_status, new_status):
    if new_status not in VALID_ORDER_STATUSES:
        raise ValueError(f"Invalid status: {new_status}")

    if current_status not in ORDER_STATUS_TRANSITIONS:
        raise ValueError(f"Unknown current status: {current_status}")

    allowed = ORDER_STATUS_TRANSITIONS[current_status]
    if new_status not in allowed:
        raise ValueError(
            f"Cannot change status from '{current_status}' to '{new_status}'. "
            f"Allowed: {', '.join(sorted(allowed)) or 'none'}"
        )

    return new_status


def validate_order_items(items):
    if not items or not isinstance(items, list):
        raise ValueError("Order must contain at least one item")

    validated_items = []
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"Item {i + 1} must be an object")

        product_id = validate_id_format(item.get('product_id'), f"Item {i + 1} product_id")
        quantity = validate_positive_int(item.get('quantity'), f"Item {i + 1} quantity")

        unit_price = None
        if 'unit_price' in item and item['unit_price'] is not None:
            unit_price = validate_positive_number(item['unit_price'], f"Item {i + 1} unit_price")

        validated_items.append({
            'product_id': product_id,
            'quantity': quantity,
            'unit_price': unit_price,
        })

    return validated_items
