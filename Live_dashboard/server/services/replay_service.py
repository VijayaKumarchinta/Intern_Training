from server.repositories.replay_repository import get_replay_cycles

def _isoformat(value):
    return value.isoformat() if value is not None else None

def get_replay_cycle_history(line_id: str, limit: int = 50) -> dict:
    rows = get_replay_cycles(line_id, limit)
    cycles = []
    for row in rows:
        cycles.append({
            "replay_cycle_id": str(row["replay_cycle_id"]),
            "replay_session_id": row["replay_session_id"],
            "replay_cycle_number": (
                int(row["replay_cycle_number"])
                if row["replay_cycle_number"] is not None
                else None
            ),
            "status": row["status"],
            "status_reason": row["status_reason"],
            "persisted_records": row["persisted_records"],
            "expected_records": row["expected_records"],
            "distinct_source_rows": row["distinct_source_rows"],
            "min_source_row": row["min_source_row"],
            "max_source_row": row["max_source_row"],
            "source_file_sha256": row["source_file_sha256"],
            "first_event_ts": _isoformat(row["first_event_ts"]),
            "last_event_ts": _isoformat(row["last_event_ts"]),
            "first_received_at": _isoformat(row["first_received_at"]),
            "last_received_at": _isoformat(row["last_received_at"]),
        })

    return {
        "line_id": line_id,
        "count": len(cycles),
        "cycles": cycles,
    }
