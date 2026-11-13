
from uuid import UUID

from flask import jsonify, request
from sqlalchemy.exc import SQLAlchemyError

from server.api import api
from server.services.summary_service import get_hourly_summary
from server.services.telemetry_service import parse_timestamp


@api.get("/summary/hourly")
def hourly_summary():
    line_id = request.args.get("line_id", "line30").strip()
    if not line_id:
        return jsonify({"error": "line_id cannot be empty."}), 400

    cycle_id = request.args.get("cycle_id") or None
    hour_start = None
    try:
        hour_start = parse_timestamp(request.args.get("hour_start"), "hour_start")
        hours_value = request.args.get("hours")
        hours = int(hours_value) if hours_value is not None else None
        if hours is not None and not 1 <= hours <= 24:
            raise ValueError("hours must be between 1 and 24.")
        if hour_start and not cycle_id:
            raise ValueError("cycle_id is required when hour_start is supplied.")
        if cycle_id:
            UUID(cycle_id)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    try:
        result = get_hourly_summary(line_id, hours, cycle_id, hour_start)
        return jsonify({"line_id": line_id, **result}), 200
    except SQLAlchemyError:
        return jsonify({"error": "Unable to calculate hourly summary."}), 500
