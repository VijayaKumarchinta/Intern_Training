"""The 8 global error handlers in app.py ARE the API contract.

One test per branch: unknown URL (404), wrong method (405), malformed JSON
(400), ValidationError (400), ConflictError (409), RelatedResourceNotFoundError
(400), DatabaseError (500 + generic body), unexpected Exception (500 + generic
body). No live database — services raise through the fake seam.
"""
import pytest

from database.connection import (
    ConflictError,
    DatabaseError,
    RelatedResourceNotFoundError,
)


def test_unknown_url_returns_404_json(client):
    resp = client.get("/definitely/not/here")
    assert resp.status_code == 404
    assert resp.get_json() == {"error": "Resource not found"}


def test_wrong_method_returns_405_json(client):
    resp = client.delete("/health")
    assert resp.status_code == 405
    assert resp.get_json() == {"error": "Method not allowed"}


def test_malformed_json_returns_400(client):
    resp = client.post(
        "/machines",
        data="{not json",
        content_type="application/json",
    )
    assert resp.status_code == 400
    body = resp.get_json()
    assert "error" in body


def test_validation_error_returns_400_with_message(client):
    resp = client.post("/machines", json={})
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "Request body is required"


def test_conflict_error_returns_409(client, monkeypatch):
    import routes.machine_routes as mr

    class ExplodingService:
        @staticmethod
        def add_machine(machine_name):
            raise ConflictError("A machine named 'X' already exists.")

    monkeypatch.setattr(mr, "machine_service", ExplodingService())
    resp = client.post("/machines", json={"machine_name": "X"})
    assert resp.status_code == 409
    assert "already exists" in resp.get_json()["error"]


def test_related_resource_missing_returns_400(client, monkeypatch):
    import routes.reading_routes as rr

    class ExplodingService:
        @staticmethod
        def add_reading(**kwargs):
            raise RelatedResourceNotFoundError("Machine with id 9 does not exist.")

    monkeypatch.setattr(rr, "reading_service", ExplodingService())
    resp = client.post(
        "/readings",
        json={
            "machine_id": 9,
            "sensor_tag": "TEMP",
            "sensor_value": 1.0,
            "timestamp": "2026-09-01T00:00:00Z",
        },
    )
    assert resp.status_code == 400
    assert "does not exist" in resp.get_json()["error"]


def test_database_error_returns_500_generic_body(client, monkeypatch):
    import routes.reading_routes as rr

    class ExplodingService:
        @staticmethod
        def get_reading(reading_id):
            raise DatabaseError("select failed: table vanished")

    monkeypatch.setattr(rr, "reading_service", ExplodingService())
    resp = client.get("/readings/5")
    assert resp.status_code == 500
    body = resp.get_json()["error"]
    assert body in (
        "A database error occurred. Please try again later.",
        "An unexpected error occurred.",
    )


def test_unexpected_exception_returns_500_generic_body(client, monkeypatch):
    import routes.reading_routes as rr

    class ExplodingService:
        @staticmethod
        def get_reading(reading_id):
            raise RuntimeError("a bug, not a database problem")

    monkeypatch.setattr(rr, "reading_service", ExplodingService())
    resp = client.get("/readings/5")
    assert resp.status_code == 500
    assert resp.get_json() == {"error": "An unexpected error occurred."}
