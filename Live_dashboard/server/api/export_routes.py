from uuid import UUID

from flask import Response, jsonify, request
from sqlalchemy.exc import SQLAlchemyError
from server.api import api
from server.services.export_service import build_events_csv, build_hourly_summary_csv, build_readings_csv
from server.services.telemetry_service import parse_timestamp


def _csv_response(filename: str, content: str):
    response = Response(content, mimetype="text/csv; charset=utf-8")
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.headers["Cache-Control"] = "no-store"
    return response


def _scope_parameters():
    cycle_id = request.args.get("cycle_id") or None
    start = parse_timestamp(request.args.get("start"), "start")
    end = parse_timestamp(request.args.get("end"), "end")
    if start and end and start >= end:
        raise ValueError("start must be earlier than end.")
    if (start or end) and not cycle_id:
        raise ValueError("cycle_id is required for a bounded historical export.")
    if cycle_id:
        UUID(cycle_id)
    return cycle_id, start, end


@api.get("/exports/hourly-summary.csv")
def export_hourly_summary():
    line_id = request.args.get("line_id", "line30").strip()
    if not line_id:
        return jsonify({"error": "line_id cannot be empty."}), 400
    try:
        hours_arg = request.args.get("hours")
        hours = int(hours_arg) if hours_arg is not None else None
        if hours is not None and not 1 <= hours <= 24:
            raise ValueError("hours must be between 1 and 24.")
        cycle_id = request.args.get("cycle_id") or None
        hour_start = parse_timestamp(request.args.get("hour_start"), "hour_start")
        if hour_start and not cycle_id:
            raise ValueError("cycle_id is required when hour_start is supplied.")
        if cycle_id:
            UUID(cycle_id)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    try:
        return _csv_response("line30-hourly-summary.csv", build_hourly_summary_csv(line_id, hours, cycle_id, hour_start))
    except SQLAlchemyError:
        return jsonify({"error": "Unable to export hourly summary."}), 500


@api.get("/exports/readings.csv")
def export_readings():
    line_id = request.args.get("line_id", "line30").strip()
    if not line_id:
        return jsonify({"error": "line_id cannot be empty."}), 400
    try:
        limit = int(request.args.get("limit", "100000"))
        if not 1 <= limit <= 100000:
            raise ValueError("limit must be between 1 and 100000.")
        cycle_id, start, end = _scope_parameters()
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    try:
        return _csv_response("line30-historical-readings.csv", build_readings_csv(line_id, limit, cycle_id, start, end))
    except SQLAlchemyError:
        return jsonify({"error": "Unable to export telemetry readings."}), 500


@api.get("/exports/events.csv")
def export_events():
    line_id = request.args.get("line_id", "line30").strip()
    if not line_id:
        return jsonify({"error": "line_id cannot be empty."}), 400
    try:
        limit = int(request.args.get("limit", "100000"))
        if not 1 <= limit <= 100000:
            raise ValueError("limit must be between 1 and 100000.")
        cycle_id, start, end = _scope_parameters()
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    try:
        return _csv_response("line30-event-history.csv", build_events_csv(line_id, limit, cycle_id, start, end))
    except SQLAlchemyError:
        return jsonify({"error": "Unable to export event history."}), 500
