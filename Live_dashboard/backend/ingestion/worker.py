import logging
import queue
import threading
from dataclasses import dataclass
from typing import Optional
from config.settings import Settings
from contract.schema import MACHINE_CODE, SCHEMA_VERSION, TelemetryRecord, SourceTimestamp, MEASUREMENT_FIELDS, SETPOINT_FIELDS, CONTROLLER_OUTPUT_FIELDS, STATE_FIELDS, CONFIGURATION_FIELDS
from mqtt.client import MqttClient
logger = logging.getLogger(__name__)

@dataclass
class IngestionStats:
    received: int = 0
    accepted: int = 0
    rejected: int = 0
    last_rejection_reason: Optional[str] = None

class IngestionWorker:

    def __init__(self, settings: Settings, machine_code: str=MACHINE_CODE, queue_maxsize: int=0) -> None:
        self._settings = settings
        self._machine_code = machine_code
        self._queue: queue.Queue[TelemetryRecord] = queue.Queue(maxsize=queue_maxsize)
        self._stop_event = threading.Event()
        self._stats = IngestionStats()
        self._stats_lock = threading.Lock()
        self._client: Optional[MqttClient] = None

    @property
    def stats(self) -> IngestionStats:
        with self._stats_lock:
            return IngestionStats(received=self._stats.received, accepted=self._stats.accepted, rejected=self._stats.rejected, last_rejection_reason=self._stats.last_rejection_reason)

    def stop(self) -> None:
        self._stop_event.set()

    def drain(self, max_items: Optional[int]=None) -> list[TelemetryRecord]:
        items: list[TelemetryRecord] = []
        while max_items is None or len(items) < max_items:
            try:
                items.append(self._queue.get_nowait())
            except queue.Empty:
                break
        return items

    def run(self) -> None:
        self._client = MqttClient(self._settings, self._machine_code, client_suffix='ingestion')
        try:
            self._client.connect()
            self._client.subscribe(self._settings.telemetry_topic(self._machine_code), callback=self._handle_message, qos=1)
            while not self._stop_event.is_set():
                if self._stop_event.wait(0.2):
                    break
        finally:
            self._client.disconnect()
            logger.info('Ingestion worker stopped. received=%d accepted=%d rejected=%d', self._stats.received, self._stats.accepted, self._stats.rejected)

    def _handle_message(self, topic: str, payload: dict) -> None:
        with self._stats_lock:
            self._stats.received += 1
        try:
            record = _payload_to_record(topic, payload)
        except Exception as exc:
            self._reject(f'{type(exc).__name__}: {exc}')
            return
        try:
            self._queue.put_nowait(record)
        except queue.Full:
            self._reject('queue full')
            return
        with self._stats_lock:
            self._stats.accepted += 1

    def _reject(self, reason: str) -> None:
        with self._stats_lock:
            self._stats.rejected += 1
            self._stats.last_rejection_reason = reason
        logger.warning('Rejected telemetry: %s', reason)

def _payload_to_record(topic: str, payload: dict) -> TelemetryRecord:
    if not isinstance(payload, dict):
        raise ValueError(f'Payload is {type(payload).__name__}, expected dict')
    schema_version = payload.get('schema_version')
    if schema_version != SCHEMA_VERSION:
        raise ValueError(f'schema_version {schema_version!r} != expected {SCHEMA_VERSION}')
    machine_code = payload.get('machine_code')
    if machine_code != MACHINE_CODE:
        raise ValueError(f'machine_code {machine_code!r} != {MACHINE_CODE}')
    expected_topic = f'line30/telemetry/{machine_code}'
    if topic != expected_topic:
        raise ValueError(f'Topic {topic!r} does not match machine_code {machine_code!r}')
    for section in ('measurements', 'setpoints', 'controller_outputs', 'states', 'configuration'):
        if not isinstance(payload.get(section), dict):
            raise ValueError(f'Missing or non-dict section: {section}')
    source = payload.get('source') or {}
    if not isinstance(source, dict):
        raise ValueError('source must be a dict')
    record = TelemetryRecord(schema_version=schema_version, machine_code=machine_code, event_timestamp=str(payload['event_timestamp']), source=SourceTimestamp(date=str(source['date']), time=str(source['time']), millitm=int(source['millitm'])), measurements={k: float(payload['measurements'][k]) for k in MEASUREMENT_FIELDS}, setpoints={k: float(payload['setpoints'][k]) for k in SETPOINT_FIELDS}, controller_outputs={k: float(payload['controller_outputs'][k]) for k in CONTROLLER_OUTPUT_FIELDS}, states={k: int(payload['states'][k]) for k in STATE_FIELDS}, configuration={k: float(payload['configuration'][k]) for k in CONFIGURATION_FIELDS}, metadata=payload.get('metadata') or {})
    record.validate()
    return record
