
import logging

from server.extensions import socketio

logger = logging.getLogger(__name__)


def broadcast_telemetry(record, payload):
    line_id = payload["line_id"]

    event_data = {
        "id": record["id"],
        "message_id": payload["message_id"],
        "replay_session_id": payload["replay_session_id"],
        "replay_cycle_id": payload["replay_cycle_id"],
        "replay_cycle_number": payload["replay_cycle_number"],
        "line_id": line_id,
        "event_ts": payload["event_ts"],
        "received_at": record["received_at"],
        "payload": payload,
    }

    socketio.emit(
        "telemetry_update",
        event_data,
        to=f"line:{line_id}",
    )

    logger.debug(
        "Telemetry broadcast: record_id=%s line_id=%s",
        record["id"],
        line_id,
    )


def broadcast_operational_events(record):
    for event in record["events"]:
        socketio.emit(
            "operational_event",
            event,
            to=f"line:{event['line_id']}",
        )

        logger.info(
            "Operational event broadcast: "
            "event_id=%s code=%s state=%s",
            event["id"],
            event["event_code"],
            event["state"],
        )
