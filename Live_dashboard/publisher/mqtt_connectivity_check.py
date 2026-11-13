import json
import threading
import paho.mqtt.client as mqtt

BROKER_HOST = "127.0.0.1"
BROKER_PORT = 1883
TOPIC = "factory/line30/telemetry"

connected = threading.Event()

def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected to MQTT broker. Result: {reason_code}")
    if reason_code == 0:
        connected.set()

client = mqtt.Client(
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    client_id="line30-python-connectivity-test",
    protocol=mqtt.MQTTv311,
)

client.on_connect = on_connect
try:
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    client.loop_start()

    if not connected.wait(timeout=5):
        raise TimeoutError("MQTT connection was not established.")

    payload = {
        "message_id": "python-mqtt-connectivity-test",
        "line": "line30",
        "status": "test",
    }

    info = client.publish(
        TOPIC,
        json.dumps(payload),
        qos=1,
        retain=False,
    )

    info.wait_for_publish(timeout=5)

    if not info.is_published():
        raise TimeoutError("MQTT message was not published.")

    print(f"Published successfully: {TOPIC}")
    print(f"Payload: {json.dumps(payload)}")

finally:
    client.loop_stop()
    client.disconnect()
