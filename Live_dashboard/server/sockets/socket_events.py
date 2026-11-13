
from flask_socketio import join_room, leave_room

from server.extensions import socketio


ALLOWED_LINE_IDS = {"line30"}


@socketio.on("join_line")
def handle_join_line(data):
    if not isinstance(data, dict):
        return {
            "status": "error",
            "message": "A line_id is required.",
        }

    line_id = data.get("line_id")

    if not isinstance(line_id, str) or line_id not in ALLOWED_LINE_IDS:
        return {
            "status": "error",
            "message": "Unknown or unauthorized line.",
        }

    room = f"line:{line_id}"
    join_room(room)

    return {
        "status": "joined",
        "line_id": line_id,
        "room": room,
    }


@socketio.on("leave_line")
def handle_leave_line(data):
    if not isinstance(data, dict):
        return {
            "status": "error",
            "message": "A line_id is required.",
        }

    line_id = data.get("line_id")

    if not isinstance(line_id, str) or line_id not in ALLOWED_LINE_IDS:
        return {
            "status": "error",
            "message": "Unknown or unauthorized line.",
        }

    room = f"line:{line_id}"
    leave_room(room)

    return {
        "status": "left",
        "line_id": line_id,
        "room": room,
    }
