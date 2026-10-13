"""Live ingest parsing and dashboard routes (fake database, no PostgreSQL)."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.live_ingest import LiveIngest
from tests.conftest import FakeCursor


def test_parse_valid_message():
    rows, rejected = LiveIngest.parse(json.dumps({"ID": "1", "ST": "41984", "TS": 1743143035, "VR": [200]}))
    assert rejected == 0
    assert rows == [("41984", 200.0, datetime.fromtimestamp(1743143035, tz=timezone.utc))]


def test_parse_list_and_counts_bad_items():
    payload = json.dumps([
        {"ST": "1", "TS": 1743143035, "VR": [5]},
        {"ST": "2", "TS": "x", "VR": [5]},
        {"ST": "3", "TS": 1743143035, "VR": []},
    ])
    rows, rejected = LiveIngest.parse(payload)
    assert len(rows) == 1 and rejected == 2


def test_parse_garbage_payload():
    assert LiveIngest.parse(b"not json") == ([], 1)


def test_series_requires_machine_id_and_tag(client):
    assert client.get("/dashboard/series?sensor_tag=1").status_code == 400
    assert client.get("/dashboard/series?machine_id=1").status_code == 400
    assert client.get("/dashboard/series?machine_id=1&sensor_tag=1&minutes=0").status_code == 400


def test_overview_status_from_age(client, fake_db):
    now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    fresh = datetime(2026, 1, 1, 11, 59, 50, tzinfo=timezone.utc)
    old = datetime(2026, 1, 1, 11, 0, 0, tzinfo=timezone.utc)
    fake_db.push_cursor(FakeCursor(results=[
        (1, "a", fresh, 10, now), (2, "b", old, 0, now), (3, "c", None, 0, now),
    ]))
    body = client.get("/dashboard/overview").get_json()
    assert [m["status"] for m in body["machines"]] == ["ok", "stale", "no_data"]


def test_stream_sends_hello_then_readings(client, fake_db, monkeypatch):
    from routes import dashboard_routes as dr

    calls = iter([
        [{"reading_id": 7, "machine_id": 1, "machine_name": "a", "sensor_tag": "1",
          "sensor_value": 2.0, "timestamp": "2026-01-01T00:00:00Z"}],
    ])
    monkeypatch.setattr(dr.dashboard_service, "max_reading_id", lambda: 6)
    monkeypatch.setattr(dr.dashboard_service, "readings_after", lambda last_id, limit: next(calls, []))
    monkeypatch.setattr(dr, "SSE_MAX_SECONDS", 0.3)
    monkeypatch.setattr(dr, "SSE_POLL_SECONDS", 0.05)
    resp = client.get("/dashboard/stream")
    text = resp.get_data(as_text=True)
    assert resp.mimetype == "text/event-stream"
    assert "event: hello" in text and "id: 7\nevent: readings" in text
