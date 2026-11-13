
import logging

import paho.mqtt.client as mqtt

from server.config import (
    MQTT_CLIENT_ID,
    MQTT_HOST,
    MQTT_KEEPALIVE,
    MQTT_PORT,
    MQTT_QOS,
    MQTT_TOPIC,
)
from server.mqtt.message_handler import on_message

logger = logging.getLogger(__name__)
_mqtt_client = None


def is_mqtt_connected() -> bool:
    return (
        _mqtt_client is not None
        and _mqtt_client.is_connected()
    )


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        logger.error(
            "MQTT connection rejected: %s",
            reason_code,
        )
        return

    logger.info(
        "Connected to MQTT broker: %s:%s",
        MQTT_HOST,
        MQTT_PORT,
    )

    result, message_id = client.subscribe(
        MQTT_TOPIC,
        qos=MQTT_QOS,
    )

    if result != mqtt.MQTT_ERR_SUCCESS:
        logger.error(
            "MQTT subscription failed: return_code=%s",
            result,
        )
        return

    logger.info(
        "Subscribed to topic '%s' at QoS %s",
        MQTT_TOPIC,
        MQTT_QOS,
    )


def create_mqtt_client():
    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id=MQTT_CLIENT_ID,
        protocol=mqtt.MQTTv311,
        clean_session=False,
        manual_ack=True,
    )

    client.on_connect = on_connect
    client.on_message = on_message

    client.reconnect_delay_set(
        min_delay=1,
        max_delay=30,
    )

    return client


def start_mqtt_subscriber():
    global _mqtt_client

    client = create_mqtt_client()

    logger.info(
        "Starting MQTT subscriber: client_id=%s",
        MQTT_CLIENT_ID,
    )

    client.connect(
        MQTT_HOST,
        MQTT_PORT,
        MQTT_KEEPALIVE,
    )

    _mqtt_client = client
    client.loop_start()

    return client


def stop_mqtt_subscriber(client):
    global _mqtt_client

    if client is None:
        return

    logger.info("Stopping MQTT subscriber")

    client.disconnect()
    client.loop_stop()

    if _mqtt_client is client:
        _mqtt_client = None
