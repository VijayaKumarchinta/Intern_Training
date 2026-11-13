
from uuid import UUID

from flask import jsonify, request
from sqlalchemy.exc import SQLAlchemyError

from server.api import api
from server.repositories.telemetry_query_repository import get_reading_history
from server.services.telemetry_service import (
    get_latest_telemetry,
    get_telemetry_history,
    get_telemetry_statistics,
    parse_timestamp,
)


@api.get("/telemetry/latest")
def latest_telemetry():
    line_id = request.args.get("line_id", "line30").strip()

    if not line_id:
        return jsonify({"error": "line_id cannot be empty."}), 400

    try:
        return jsonify({
            "line_id": line_id,
            "data": get_latest_telemetry(line_id),
        }), 200
    except SQLAlchemyError:
        return jsonify({
            "error": "Unable to retrieve latest telemetry.",
        }), 500


@api.get("/telemetry/history")
def telemetry_history():
    line_id = request.args.get("line_id", "line30").strip()

    if not line_id:
        return jsonify({"error": "line_id cannot be empty."}), 400

    try:
        limit = int(request.args.get("limit", "100"))

        if not 1 <= limit <= 500:
            raise ValueError("limit must be between 1 and 500.")

        before = parse_timestamp(request.args.get("before"), "before")
        start = parse_timestamp(request.args.get("start"), "start")
        end = parse_timestamp(request.args.get("end"), "end")
        cycle_id = request.args.get("cycle_id") or None
        if start and end and start >= end:
            raise ValueError("start must be earlier than end.")
        if (start or end) and not cycle_id:
            raise ValueError("cycle_id is required for a bounded historical query.")
        if cycle_id:
            UUID(cycle_id)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    try:
        if cycle_id:
            raw_rows = get_reading_history(
                line_id, before, limit, cycle_id=cycle_id, start=start, end=end
            )
            rows = [
                {
                    "id": row["id"],
                    "message_id": row["message_id"],
                    "replay_session_id": row["replay_session_id"],
                    "replay_cycle_id": str(row["replay_cycle_id"]),
                    "replay_cycle_number": row["replay_cycle_number"],
                    "line_id": row["line_id"],
                    "event_ts": row["event_ts"].isoformat(),
                    "received_at": row["received_at"].isoformat(),
                    "payload": row["payload"],
                }
                for row in raw_rows
            ]
        else:
            rows = get_telemetry_history(line_id, before, limit)

        return jsonify({"line_id": line_id, "count": len(rows), "limit": limit, "data": rows}), 200
    except SQLAlchemyError:
        return jsonify({
            "error": "Unable to retrieve telemetry history.",
        }), 500


@api.get("/telemetry/statistics")
def telemetry_statistics():
    line_id = request.args.get("line_id", "line30").strip()
    field = request.args.get("field", "").strip()

    if not line_id:
        return jsonify({"error": "line_id cannot be empty."}), 400

    if not field:
        return jsonify({"error": "field is required."}), 400

    try:
        start = parse_timestamp(
            request.args.get("start"),
            "start",
        )
        end = parse_timestamp(
            request.args.get("end"),
            "end",
        )

        cycle_id = request.args.get("cycle_id") or None

        if start and end and start >= end:
            raise ValueError("start must be earlier than end.")

        if (start or end) and not cycle_id:
            raise ValueError(
                "cycle_id is required for a bounded statistics query."
            )

        if cycle_id:
            UUID(cycle_id)

    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    try:
        result = get_telemetry_statistics(
            line_id,
            field,
            start,
            end,
            cycle_id,
        )

        return jsonify(result), 200
    except SQLAlchemyError:
        return jsonify({
            "error": "Unable to calculate telemetry statistics.",
        }), 500
