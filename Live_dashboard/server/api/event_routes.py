
from uuid import UUID

from flask import jsonify, request
from sqlalchemy.exc import SQLAlchemyError

from server.api import api
from server.services.event_service import get_event_history
from server.services.telemetry_service import parse_timestamp


@api.get("/events")
def event_history():
    line_id = request.args.get("line_id", "line30").strip()

    if not line_id:
        return jsonify({"error": "line_id cannot be empty."}), 400

    try:
        limit = int(request.args.get("limit", "100"))
        if not 1 <= limit <= 50000:
            raise ValueError("limit must be between 1 and 50000.")
        cycle_id = request.args.get("cycle_id") or None
        start = parse_timestamp(request.args.get("start"), "start")
        end = parse_timestamp(request.args.get("end"), "end")
        if start and end and start >= end:
            raise ValueError("start must be earlier than end.")
        if (start or end) and not cycle_id:
            raise ValueError("cycle_id is required for a bounded historical query.")
        if cycle_id:
            UUID(cycle_id)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    try:
        events = get_event_history(line_id, limit, cycle_id, start, end)

        return jsonify({
            "line_id": line_id,
            "count": len(events),
            "limit": limit,
            "data": events,
        }), 200
    except SQLAlchemyError:
        return jsonify({
            "error": "Unable to retrieve event history.",
        }), 500
