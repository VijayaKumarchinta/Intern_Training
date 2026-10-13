"""Subscribes to the broker over mTLS and writes every message to PostgreSQL.

Run:  python mqtt_subscriber.py
Topic = machine name (last path segment); payload = JSON, see services/live_ingest.py
"""
import paho.mqtt.client as mqtt

from config import (
    MQTT_CA_CERT, MQTT_CLIENT_CERT, MQTT_CLIENT_ID, MQTT_CLIENT_KEY,
    MQTT_HOST, MQTT_PORT, MQTT_TOPIC,
)
from database.connection import DatabaseError
from services.live_ingest import live_ingest
from utils.logger import logger


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        logger.error("MQTT connect failed: %s", reason_code)
        return
    logger.info("MQTT connected, subscribing to %s", MQTT_TOPIC)
    client.subscribe(MQTT_TOPIC)  # re-subscribes after every auto-reconnect


def on_message(client, userdata, message):
    machine_name = message.topic.rsplit("/", 1)[-1]
    try:
        inserted, rejected = live_ingest.ingest(machine_name, message.payload)
        logger.debug("MQTT %s inserted=%s rejected=%s", message.topic, inserted, rejected)
    except DatabaseError as error:
        logger.error("MQTT message dropped (database): %s", error)
    except Exception:
        logger.exception("MQTT message dropped (unexpected)")


def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
    logger.warning("MQTT disconnected: %s (paho will retry)", reason_code)


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=MQTT_CLIENT_ID)
    client.tls_set(ca_certs=MQTT_CA_CERT, certfile=MQTT_CLIENT_CERT, keyfile=MQTT_CLIENT_KEY)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    client.reconnect_delay_set(min_delay=1, max_delay=30)
    client.connect(MQTT_HOST, MQTT_PORT)
    client.loop_forever()


if __name__ == "__main__":
    main()
