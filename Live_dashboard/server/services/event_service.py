
from server.repositories.event_repository import get_events


def _serialize_event(row):
    return {
        "id": row["id"],
        "line_id": row["line_id"],
        "event_type": row["event_type"],
        "event_code": row["event_code"],
        "severity": row["severity"],
        "state": row["state"],
        "title": row["title"],
        "description": row["description"],
        "event_ts": row["event_ts"].isoformat(),
        "recorded_at": row["recorded_at"].isoformat(),
        "reading_id": row["reading_id"],
        "replay_cycle_id": (
            str(row["replay_cycle_id"])
            if row["replay_cycle_id"] is not None
            else None
        ),
        "details": row["details"],
    }


def get_event_history(line_id: str, limit: int = 100, cycle_id=None, start=None, end=None) -> list[dict]:
    rows = get_events(line_id, limit, cycle_id, start, end)
    return [_serialize_event(row) for row in rows]
