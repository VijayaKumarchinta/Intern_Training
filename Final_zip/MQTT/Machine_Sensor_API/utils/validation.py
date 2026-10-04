from datetime import datetime

from flask import request

from config import DEFAULT_PAGE_SIZE
from errors import ValidationError

def validate_machine_id(value):
    try:
        machine_id = int(value)

        if machine_id <= 0:
            raise ValueError

        return machine_id

    except (TypeError, ValueError):
        raise ValidationError(
            "machine_id must be a positive integer"
        ) from None

def validate_sensor_tag(value):
    if not isinstance(value, str) or not value.strip():
        raise ValidationError("sensor_tag must be a non-empty string")

    return value.strip()

def validate_timestamp(value):
    if not isinstance(value, str) or not value.strip():
        raise ValidationError("timestamp must be a non-empty string")

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ValidationError(
            "timestamp must be a valid ISO 8601 timestamp"
        ) from None

def machine_id_from_query():
    value = request.args.get("machine_id")

    if value is None:
        return None

    return validate_machine_id(value)

def timestamp_from_query(name):
    value = request.args.get(name)

    if value is None:
        return None

    return validate_timestamp(value)

def pagination_from_query():
    try:
        limit = int(request.args.get("limit", DEFAULT_PAGE_SIZE))
        offset = int(request.args.get("offset", 0))
    except ValueError:
        raise ValidationError(
            "limit and offset must be integers"
        ) from None

    if limit < 1:
        raise ValidationError("limit must be >= 1")

    if offset < 0:
        raise ValidationError("offset must be >= 0")

    return min(limit, DEFAULT_PAGE_SIZE), offset

def validate_from_to_order(from_time, to_time):
    if (
        from_time is not None
        and to_time is not None
        and from_time > to_time
    ):
        raise ValidationError(
            "'from' timestamp cannot be later than 'to' timestamp"
        )