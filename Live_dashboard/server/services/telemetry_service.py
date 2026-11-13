
from datetime import datetime

from server.repositories.telemetry_query_repository import (
    get_latest_reading,
    get_reading_history,
    get_reading_statistics,
)


def parse_timestamp(value, parameter_name):
    if not value:
        return None

    try:
        timestamp = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValueError(
            f"{parameter_name} must be a valid ISO 8601 timestamp."
        ) from None

    if timestamp.tzinfo is not None:
        raise ValueError(
            f"{parameter_name} must be timezone-naive."
        )

    return timestamp


def serialize_reading(row):
    if row is None:
        return None

    return {
        "id": row["id"],
        "message_id": row["message_id"],
        "replay_session_id": str(row["replay_session_id"]),
        "replay_cycle_id": str(row["replay_cycle_id"]),
        "replay_cycle_number": row["replay_cycle_number"],
        "line_id": row["line_id"],
        "event_ts": row["event_ts"].isoformat(),
        "received_at": row["received_at"].isoformat(),
        "payload": row["payload"],
    }


def get_latest_telemetry(line_id: str):
    row = get_latest_reading(line_id)
    return serialize_reading(row)


def get_telemetry_history(line_id: str, before, limit: int):
    rows = get_reading_history(line_id, before, limit)

    return [
        serialize_reading(row)
        for row in rows
    ]


def get_telemetry_statistics(
    line_id: str,
    field: str,
    start,
    end,
    cycle_id=None,
):
    result = get_reading_statistics(
        line_id,
        field,
        start,
        end,
        cycle_id,
    )

    return {
        "line_id": line_id,
        "field": field,
        "cycle_id": (
            str(result["cycle_id"])
            if result["cycle_id"] is not None
            else None
        ),
        "sample_count": result["sample_count"],
        "average": (
            float(result["average"])
            if result["average"] is not None else None
        ),
        "minimum": (
            float(result["minimum"])
            if result["minimum"] is not None else None
        ),
        "maximum": (
            float(result["maximum"])
            if result["maximum"] is not None else None
        ),
        "start": start.isoformat() if start else None,
        "end": end.isoformat() if end else None,
    }