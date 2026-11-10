import json
import logging
import uuid
from typing import Any, Callable, Optional
import paho.mqtt.client as mqtt
from config.settings import Settings
logger = logging.getLogger(__name__)
_STATE_ONLINE = 'online'
_STATE_OFFLINE = 'offline'

class MqttClient:

    def __init__(self, settings: Settings, machine_code: str, client_suffix: Optional[str]=None) -> None:
        self._settings = settings
        self._machine_code = machine_code
        suffix = client_suffix or uuid.uuid4().hex[:8]
        self._client_id = f'{settings.mqtt_client_id_prefix}-{machine_code}-{suffix}'
        self._connected = False
        self._client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id=self._client_id, protocol=mqtt.MQTTv311, clean_session=True)
        if settings.mqtt_username:
            self._client.username_pw_set(settings.mqtt_username, settings.mqtt_password or None)
        state_topic = settings.state_topic(machine_code)
        will_payload = json.dumps({'machine_code': machine_code, 'status': _STATE_OFFLINE}, separators=(',', ':'))
        self._client.will_set(state_topic, will_payload, qos=1, retain=True)
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect

    def connect(self, timeout: float=10.0) -> None:
        logger.info('Connecting to MQTT broker %s:%s as %s', self._settings.mqtt_host, self._settings.mqtt_port, self._client_id)
        self._client.connect(self._settings.mqtt_host, self._settings.mqtt_port, keepalive=self._settings.mqtt_keepalive_seconds)
        self._client.loop_start()
        self._publish_state(_STATE_ONLINE)

    def disconnect(self) -> None:
        if self._connected:
            self._publish_state(_STATE_OFFLINE)
        self._client.loop_stop()
        self._client.disconnect()
        logger.info('Disconnected from MQTT broker (client %s)', self._client_id)

    def __enter__(self) -> 'MqttClient':
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.disconnect()

    def publish(self, topic: str, payload: Any, qos: int=1, retain: bool=False) -> None:
        if isinstance(payload, (dict, list)):
            body = json.dumps(payload, separators=(',', ':'), default=str)
        elif isinstance(payload, (bytes, str)):
            body = payload
        else:
            raise TypeError(f'publish() payload must be dict, list, str, or bytes; got {type(payload).__name__}')
        info = self._client.publish(topic, body, qos=qos, retain=retain)
        if info.rc != mqtt.MQTT_ERR_SUCCESS:
            raise RuntimeError(f'Failed to enqueue publish on {topic}: rc={info.rc}')

    def subscribe(self, topic: str, callback: Callable[[str, dict], None], qos: int=1) -> None:

        def _on_message(client, userdata, message) -> None:
            try:
                payload = json.loads(message.payload.decode('utf-8'))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                logger.error('Non-JSON payload on topic %s (%d bytes): %s', message.topic, len(message.payload), exc)
                return
            try:
                callback(message.topic, payload)
            except Exception:
                logger.exception('Subscriber callback raised on topic %s', message.topic)
        self._client.on_message = _on_message
        self._client.subscribe(topic, qos=qos)
        logger.info('Subscribed to %s (QoS %d)', topic, qos)

    def is_connected(self) -> bool:
        return self._connected

    def _publish_state(self, status: str) -> None:
        topic = self._settings.state_topic(self._machine_code)
        payload = {'machine_code': self._machine_code, 'status': status}
        self.publish(topic, payload, qos=1, retain=True)

    def _on_connect(self, client, userdata, flags, reason_code, properties) -> None:
        if reason_code == 0:
            self._connected = True
            logger.info('MQTT connected (client %s)', self._client_id)
        else:
            self._connected = False
            logger.error('MQTT connection failed: %s', reason_code)

    def _on_disconnect(self, client, userdata, flags, reason_code, properties) -> None:
        self._connected = False
        logger.info('MQTT disconnected (client %s, rc=%s)', self._client_id, reason_code)
