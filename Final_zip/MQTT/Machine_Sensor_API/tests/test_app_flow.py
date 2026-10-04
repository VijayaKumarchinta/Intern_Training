"""Route-level flows through the real app with the fake database.

Proves the happy paths end-to-end (route → service → fake pool → JSON) and
the health check's failure mode, without PostgreSQL.
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tests.conftest import FakeCursor


def test_create_machine_returns_201(client, fake_db):
    fake_db.push_cursor(FakeCursor(results=[(1, "CNC-01")]))
    resp = client.post("/machines", json={"machine_name": "CNC-01"})
    assert resp.status_code == 201
    assert resp.get_json() == {"machine_id": 1, "machine_name": "CNC-01"}


def test_machine_name_is_validated_before_service(client, fake_db):
    resp = client.post("/machines", json={"machine_name": "   "})
    assert resp.status_code == 400
    assert fake_db.cursor_stack == [], "invalid input must never reach the pool"


def test_list_machines(client, fake_db):
    fake_db.push_cursor(FakeCursor(results=[(1, "CNC-01"), (2, "CNC-02")]))
    resp = client.get("/machines")
    assert resp.status_code == 200
    assert resp.get_json() == [
        {"machine_id": 1, "machine_name": "CNC-01"},
        {"machine_id": 2, "machine_name": "CNC-02"},
    ]


def test_get_missing_machine_returns_404(client, fake_db):
    fake_db.push_cursor(FakeCursor(results=[]))
    resp = client.get("/machines/99")
    assert resp.status_code == 404


def test_create_reading_returns_201(client, fake_db):
    fake_db.push_cursor(
        FakeCursor(
            results=[(1, 5, "TEMP", 72.5, datetime(2026, 9, 1, tzinfo=timezone.utc))]
        )
    )
    resp = client.post(
        "/readings",
        json={
            "machine_id": 5,
            "sensor_tag": "TEMP",
            "sensor_value": 72.5,
            "timestamp": "2026-09-01T00:00:00Z",
        },
    )
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["sensor_tag"] == "TEMP"
    assert body["timestamp"].endswith("Z")


def test_missing_reading_fields_all_reported(client):
    resp = client.post("/readings", json={"sensor_tag": "TEMP"})
    assert resp.status_code == 400
    error = resp.get_json()["error"]
    assert "machine_id" in error and "sensor_value" in error and "timestamp" in error


def test_inverted_from_to_rejected(client):
    resp = client.get(
        "/readings",
        query_string={
            "from": "2026-09-05T00:00:00Z",
            "to": "2026-09-01T00:00:00Z",
        },
    )
    assert resp.status_code == 400
    assert "cannot be later" in resp.get_json()["error"]


def test_health_reports_disconnected_without_db(client):
    resp = client.get("/health")
    assert resp.status_code == 503
    assert resp.get_json()["status"] == "error"


def test_index_lists_endpoints(client):
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "running"
    assert any("readings" in endpoint for endpoint in body["endpoints"])
