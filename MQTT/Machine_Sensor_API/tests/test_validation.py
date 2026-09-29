"""utils/validation.py — one shared set of input rules for every view.

Pure functions over plain values (the core three need no request object),
so these tests need no app at all.
"""
import sys
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from errors import ValidationError
from utils.validation import (
    pagination_from_query,
    validate_from_to_order,
    validate_machine_id,
    validate_sensor_tag,
    validate_timestamp,
)


class TestValidateMachineId:
    def test_accepts_positive_int(self):
        assert validate_machine_id(5) == 5

    def test_accepts_numeric_string(self):
        assert validate_machine_id("12") == 12

    def test_rejects_zero(self):
        with pytest.raises(ValidationError):
            validate_machine_id(0)

    def test_rejects_negative(self):
        with pytest.raises(ValidationError):
            validate_machine_id(-3)

    def test_rejects_non_numeric(self):
        with pytest.raises(ValidationError):
            validate_machine_id("abc")

    def test_rejects_none(self):
        with pytest.raises(ValidationError):
            validate_machine_id(None)


class TestValidateSensorTag:
    def test_accepts_and_strips(self):
        assert validate_sensor_tag("  TEMP ") == "TEMP"

    def test_rejects_blank(self):
        with pytest.raises(ValidationError):
            validate_sensor_tag("   ")

    def test_rejects_non_string(self):
        with pytest.raises(ValidationError):
            validate_sensor_tag(42)


class TestValidateTimestamp:
    def test_accepts_iso_with_z(self):
        parsed = validate_timestamp("2026-09-01T10:00:00Z")
        assert parsed.tzinfo is not None

    def test_accepts_iso_with_offset(self):
        parsed = validate_timestamp("2026-09-01T15:30:00+05:30")
        assert isinstance(parsed, datetime)

    def test_rejects_garbage(self):
        with pytest.raises(ValidationError):
            validate_timestamp("not a timestamp")

    def test_rejects_empty(self):
        with pytest.raises(ValidationError):
            validate_timestamp("")


class TestValidateFromToOrder:
    def test_accepts_ordered_range(self):
        a = datetime(2026, 9, 1)
        b = datetime(2026, 9, 2)
        validate_from_to_order(a, b)

    def test_accepts_equal_bounds(self):
        same = datetime(2026, 9, 1)
        validate_from_to_order(same, same)

    def test_accepts_partial_filters(self):
        validate_from_to_order(None, datetime(2026, 9, 2))
        validate_from_to_order(datetime(2026, 9, 1), None)

    def test_rejects_inverted_range(self):
        with pytest.raises(ValidationError):
            validate_from_to_order(datetime(2026, 9, 2), datetime(2026, 9, 1))


class TestPagination:
    def test_defaults_and_cap(self, monkeypatch):
        from flask import Flask

        app = Flask(__name__)
        with app.test_request_context("/?limit=99999&offset=5"):
            limit, offset = pagination_from_query()
        assert limit == 1000
        assert offset == 5

    def test_rejects_non_integer(self):
        from flask import Flask

        app = Flask(__name__)
        with app.test_request_context("/?limit=abc"):
            with pytest.raises(ValidationError):
                pagination_from_query()

    def test_rejects_negative_offset(self):
        from flask import Flask

        app = Flask(__name__)
        with app.test_request_context("/?offset=-1"):
            with pytest.raises(ValidationError):
                pagination_from_query()
