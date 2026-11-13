
import json
import logging

import paho.mqtt.client as mqtt
from sqlalchemy.exc import SQLAlchemyError

from server.repositories.telemetry_repository import save_telemetry
from server.sockets.broadcaster import (
    broadcast_operational_events,
    broadcast_telemetry,
)

logger = logging.getLogger(__name__)


def _ack_message(client, message):
    result = client.ack(message.mid, message.qos)

    if result != mqtt.MQTT_ERR_SUCCESS:
        logger.error(
            "MQTT acknowledgement failed: packet_id=%s result=%s",
            message.mid,
            result,
        )
        return False

    return True


def on_message(client, userdata, message):
    try:
        raw_payload = message.payload.decode("utf-8")
        payload = json.loads(raw_payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        logger.error(
            "Discarding malformed MQTT message: topic=%s error=%s",
            message.topic,
            exc,
        )
        _ack_message(client, message)
        return

    try:
        record = save_telemetry(payload)
    except ValueError as exc:
        logger.error(
            "Discarding invalid telemetry payload: topic=%s error=%s",
            message.topic,
            exc,
        )
        _ack_message(client, message)
        return
    except SQLAlchemyError:
        logger.exception(
            "Database persistence failed. MQTT message remains "
            "unacknowledged: topic=%s packet_id=%s",
            message.topic,
            message.mid,
        )
        return
    except Exception:
        logger.exception(
            "Unexpected telemetry processing failure. MQTT message "
            "remains unacknowledged: topic=%s packet_id=%s",
            message.topic,
            message.mid,
        )
        return

    if record is None:
        logger.info(
            "Duplicate telemetry ignored: message_id=%s",
            payload.get("message_id"),
        )
        _ack_message(client, message)
        return

    logger.info(
        "Telemetry persisted: record_id=%s message_id=%s "
        "generated_events=%s",
        record["id"],
        payload.get("message_id"),
        len(record["events"]),
    )

    acknowledged = _ack_message(client, message)

    if not acknowledged:
        logger.error(
            "Telemetry was persisted but MQTT acknowledgement "
            "failed: record_id=%s",
            record["id"],
        )

    try:
        broadcast_telemetry(record, payload)
    except Exception:
        logger.exception(
            "Telemetry was persisted but Socket.IO broadcast failed: "
            "record_id=%s",
            record["id"],
        )

    try:
        broadcast_operational_events(record)
    except Exception:
        logger.exception(
            "Telemetry was persisted but operational event "
            "broadcast failed: record_id=%s",
            record["id"],
        )
