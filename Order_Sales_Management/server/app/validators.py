"""
Validators.

Every user-supplied field is checked here before it reaches the service layer.
Each validator returns (value, error); at least one must be clean.
"""

import re
from datetime import date

# customer_id like C0001 (letter C plus 4 or more digits)
CUSTOMER_ID_RE = re.compile(r"^C\d{4,}$")

VALID_STATUSES = {"Pending", "Shipped", "Delivered", "Returned", "Cancelled"}


def validate_customer_id(value) -> tuple:
    if value is None or not isinstance(value, str) or not CUSTOMER_ID_RE.match(value.strip()):
        return None, "customer_id must look like C0001 (letter C plus 4 or more digits)."
    return value.strip(), None


def validate_product(value) -> tuple:
    if value is None or not isinstance(value, str) or not value.strip():
        return None, "product is required and must be a non-empty text."
    return value.strip(), None


def validate_quantity(value) -> tuple:
    if isinstance(value, bool):
        return None, "quantity must be a positive whole number."
    if isinstance(value, int):
        if value <= 0:
            return None, "quantity must be a positive integer."
        return value, None
    if isinstance(value, float):
        if not value.is_integer():
            return None, "quantity must be a positive integer."
        if value <= 0:
            return None, "quantity must be a positive integer."
        return int(value), None
    return None, "quantity must be a positive integer."


def validate_unit_price(value) -> tuple:
    if isinstance(value, bool):
        return None, "unit_price must be a non-negative number with up to 2 decimals."
    if isinstance(value, (int, float)):
        if isinstance(value, float) and not value.is_integer():
            # 500.989 should be invalid; 500.98 valid
            if round(value, 2) != value:
                return None, "unit_price must be a non-negative number with up to 2 decimals."
        if value < 0:
            return None, "unit_price must be a non-negative number with up to 2 decimals."
        return round(value, 2), None
    text = str(value).strip()
    if not re.match(r"^\d+(\.\d{1,2})?$", text):
        return None, "unit_price must be a non-negative number with up to 2 decimals."
    return round(float(text), 2), None


def validate_date_string(value) -> tuple:
    if value is None or not isinstance(value, str) or not value.strip():
        return None, "order_date is required (YYYY-MM-DD)."
    text = value.strip()
    try:
        parsed = date.fromisoformat(text)
    except ValueError:
        return None, "order_date must be a real date in YYYY-MM-DD format."
    if parsed > date.today():
        return None, "order_date cannot be in the future."
    return text, None


def validate_status(value) -> tuple:
    if value is None or not isinstance(value, str) or value.strip() not in VALID_STATUSES:
        return None, f"status must be one of {sorted(VALID_STATUSES)}."
    return value.strip(), None


def validate_body(data: dict, create: bool = True) -> tuple:
    """
    Validate the whole request body and return (clean_data, error).
    create=True  -> full fields (including required order_date).
    create=False -> partial for PATCH (only the fields being changed).
    """
    if not isinstance(data, dict):
        return None, "Request body must be a JSON object."

    if create:
        required = ["customer_id", "product", "quantity", "unit_price", "order_date"]
        missing = [f for f in required if f not in data]
        if missing:
            return None, f"Missing required fields: {', '.join(missing)}."

    errors = []
    clean = {}

    customer_id, err = validate_customer_id(data.get("customer_id") if create else data.get("customer_id"))
    if err:
        errors.append(err)
    else:
        clean["customer_id"] = customer_id

    product, err = validate_product(data.get("product"))
    if err:
        errors.append(err)
    else:
        clean["product"] = product

    quantity, err = validate_quantity(data.get("quantity"))
    if err:
        errors.append(err)
    else:
        clean["quantity"] = quantity

    unit_price, err = validate_unit_price(data.get("unit_price"))
    if err:
        errors.append(err)
    else:
        clean["unit_price"] = unit_price

    if create:
        order_date, err = validate_date_string(data.get("order_date"))
        if err:
            errors.append(err)
        else:
            clean["order_date"] = order_date
    else:
        # PATCH: date is not editable.
        clean["order_date"] = None

    if data.get("status") is not None:
        status, err = validate_status(data.get("status"))
        if err:
            errors.append(err)
        else:
            clean["status"] = status

    if errors:
        return None, errors

    return clean, None
