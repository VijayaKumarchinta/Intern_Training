"""Service layer: SQL assembly, filter builder, and error translation.

These run against the FakeDB seam from conftest — real service code, fake
pool — proving the SQL text and the exception mapping without PostgreSQL.
The service modules' `db` binding is patched via the `patched_services`
fixture so no test ever touches the live pool.
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.connection import (
    ConflictError,
    DatabaseError,
    RelatedResourceNotFoundError,
)
from services.reading_service import ReadingService, utc_z
from tests.conftest import FakeCursor


@pytest.fixture()
def fake_db():
    from tests.conftest import FakeDB

    return FakeDB()


@pytest.fixture()
def patched_services(fake_db, monkeypatch):
    """Swap the pool inside the service modules themselves — the seam that
    `from database.connection import db` freezes at import time."""
    from services import machine_service, pickle_importer, reading_service

    for module in (machine_service, reading_service, pickle_importer):
        monkeypatch.setattr(module, "db", fake_db)


@pytest.fixture()
def service(patched_services):
    return ReadingService()


class TestBuildReadingFilters:
    def test_no_filters_appends_no_where(self, service):
        query, values = service._build_reading_filters("SELECT * FROM t")
        assert "WHERE" not in query
        assert values == []

    def test_single_filter(self, service):
        query, values = service._build_reading_filters(
            "SELECT * FROM t", machine_id=5
        )
        assert query.endswith("WHERE machine_id = %s")
        assert values == [5]

    def test_all_filters_joined_with_and(self, service):
        query, values = service._build_reading_filters(
            "SELECT * FROM t",
            machine_id=5,
            sensor_tag="TEMP",
            from_time="a",
            to_time="b",
        )
        assert (
            "machine_id = %s AND sensor_tag = %s"
            " AND timestamp >= %s AND timestamp <= %s" in query
        )
        assert values == [5, "TEMP", "a", "b"]

    def test_get_readings_and_statistics_share_one_builder(self, service, fake_db):
        fake_db.push_cursor(
            FakeCursor(
                results=[[1, 5, "TEMP", 1.0, datetime(2026, 9, 1, tzinfo=timezone.utc)]]
            )
        )
        service.get_readings(machine_id=5)

        fake_db.push_cursor(FakeCursor(results=[(10.0, 20.0, 15.0)]))
        service.get_statistics(machine_id=5)

        assert fake_db.all_queries[0].count("machine_id = %s") >= 1
        assert fake_db.all_queries[-1].count("machine_id = %s") >= 1
        assert fake_db.all_queries[0] != fake_db.all_queries[-1], (
            "list and statistics build different SQL from the same helper"
        )


class TestErrorTranslation:
    def test_foreign_key_violation_becomes_400(self, service, fake_db):
        from psycopg2.errors import ForeignKeyViolation

        fake_db.fail_on_execute = ForeignKeyViolation("fk")
        with pytest.raises(RelatedResourceNotFoundError):
            service.add_reading(999, "TEMP", 1.0, datetime(2026, 9, 1))

    def test_unique_violation_in_machine_service_becomes_409(self, fake_db, patched_services):
        from psycopg2.errors import UniqueViolation

        from services.machine_service import MachineService

        fake_db.fail_on_execute = UniqueViolation("dup")
        with pytest.raises(ConflictError):
            MachineService().add_machine("CNC-01")

    def test_generic_exception_becomes_database_error(self, service, fake_db):
        fake_db.fail_on_execute = RuntimeError("boom")
        with pytest.raises(DatabaseError):
            service.get_reading(1)


class TestFormatting:
    def test_utc_z_renders_z_suffix(self):
        aware = datetime(2026, 9, 1, 10, 0, 0, tzinfo=timezone.utc)
        assert utc_z(aware) == "2026-09-01T10:00:00Z"

    def test_utc_z_converts_other_offsets(self):
        from datetime import timedelta

        ist = timezone(timedelta(hours=5, minutes=30))
        assert utc_z(datetime(2026, 9, 1, 15, 30, 0, tzinfo=ist)) == "2026-09-01T10:00:00Z"

    def test_format_reading_shape(self, service):
        row = (1, 5, "TEMP", 72.5, datetime(2026, 9, 1, tzinfo=timezone.utc))
        reading = service._format_reading(row)
        assert reading == {
            "reading_id": 1,
            "machine_id": 5,
            "sensor_tag": "TEMP",
            "sensor_value": 72.5,
            "timestamp": "2026-09-01T00:00:00Z",
        }
