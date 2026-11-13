from flask import jsonify, request
from sqlalchemy.exc import SQLAlchemyError
from server.api import api
from server.services.replay_service import get_replay_cycle_history

@api.get("/history/cycles")
def replay_cycle_history():
    line_id = request.args.get("line_id", "line30").strip()

    if not line_id:
        return jsonify({"error": "line_id cannot be empty."}), 400

    try:
        limit = int(request.args.get("limit", "50"))

        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100.")
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    try:
        result = get_replay_cycle_history(line_id, limit)
        return jsonify(result), 200
    except SQLAlchemyError:
        return jsonify({
            "error": "Unable to retrieve replay-cycle history.",
        }), 500
