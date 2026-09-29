import logging
import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)

class MQTTClient:
    def __init__(self):
        try:
            self.br = "localhost"
            self.port = 8883
            self.topic = "test/topic"
            self.msg = "Hello, MQTT!"

            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="P1")

            self.client.enable_logger()

            self.client.tls_set(
                ca_certs="C:/Program Files/Mosquitto/ca.crt",
                certfile="C:/Program Files/Mosquitto/client.crt",
                keyfile="C:/Program Files/Mosquitto/client.key"
            )

            self.client.username_pw_set("user", "userpass")

            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            self.client.on_publish = self.on_publish
            self.client.on_subscribe = self.on_subscribe
            self.client.on_disconnect = self.on_disconnect

        except Exception as e:
            logger.exception("Error occurred during initialization: %s", e)

    def connect(self):
        try:
            logger.info("Connecting to MQTT broker...")
            self.client.connect(self.br, self.port)

        except Exception as e:
            logger.exception("Error occurred while connecting: %s", e)

    def subscribe(self):
        try:
            logger.info("Subscribing to topic: %s", self.topic)

            res, mid = self.client.subscribe(self.topic)
            if res != mqtt.MQTT_ERR_SUCCESS:
                raise RuntimeError(f"Subscribe request failed: {res}, with message ID: {mid}")

        except Exception as e:
            logger.exception("Error occurred while subscribing: %s", e)

    def publish(self):
        try:
            logger.info("Publishing message: %s", self.msg)

            res = self.client.publish(self.topic, self.msg)
            if res.rc != mqtt.MQTT_ERR_SUCCESS:
                raise RuntimeError(f"Publish request failed: {res}")

        except Exception as e:
            logger.exception("Error occurred while publishing: %s", e)

    def disconnect(self):
        try:
            logger.info("Disconnecting from MQTT broker...")
            if self.client.is_connected():
                self.client.disconnect()

        except Exception as e:
            logger.exception("Error occurred while disconnecting: %s", e)

    def start_loop(self):
        try:
            logger.info("Starting MQTT network loop...")
            self.client.loop_forever()

        except KeyboardInterrupt:
            logger.info("Application stopped by user.")

        except Exception as e:
            logger.exception("Error occurred in MQTT network loop: %s", e)

    def on_connect(self, client, userdata, flags, reason_code, properties):
        try:
            if reason_code.is_failure:
                logger.error("MQTT connection failed: %s", reason_code)
                return

            logger.info("Connected to MQTT broker at %s:%d", self.br, self.port)
            self.subscribe()

        except Exception as e:
            logger.exception("Error occurred in on_connect: %s", e)

    def on_subscribe(self, client, userdata, mid, reason_codes, properties):
        try:
            logger.info("Successfully subscribed to topic: %s", self.topic)
            self.publish()

        except Exception as e:
            logger.exception("Error occurred in on_subscribe: %s", e)

    def on_publish(self, client, userdata, mid, reason_code, properties):
        try:
            logger.info("Successfully published message to topic: %s", self.topic)

        except Exception as e:
            logger.exception("Error occurred in on_publish: %s", e)

    def on_message(self, client, userdata, message):
        try:
            try:
                payload = message.payload.decode("utf-8")

            except UnicodeDecodeError:
                payload = repr(message.payload)

            logger.info("Received message on topic %s: '%s'",message.topic, payload)

        except Exception as e:
            logger.exception("Error occurred while processing message: %s", e)

    def on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties):
        try:
            logger.info("Disconnected from MQTT broker")

        except Exception as e:
            logger.exception("Error occurred in on_disconnect: %s", e)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

    mqtt_cl = MQTTClient()

    try:
        mqtt_cl.connect()
        mqtt_cl.start_loop()

    except Exception as e:
        logger.exception("An error occurred in the main loop: %s", e)
    finally:

        mqtt_cl.disconnect()