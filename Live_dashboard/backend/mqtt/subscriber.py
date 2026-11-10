from __future__ import annotations

import logging
import queue
from typing import Optional

from config.settings import Settings
from mqtt.client import MqttClient


logger = logging.getLogger(__name__)


class Subscriber:
    def __init__(
        self,
        settings: Settings,
        machine_code: str,
        maxsize: int = 100,
    ) -> None:
        self._settings = settings
        self._machine_code = machine_code
        self._queue: queue.Queue = queue.Queue(maxsize=maxsize)
        self._client: Optional[MqttClient] = None
        self._rejected_count = 0

    @property
    def queue(self) -> queue.Queue:
        return self._queue

    @property
    def rejected_count(self) -> int:
        return self._rejected_count

    def _on_message(self, topic: str, payload: dict) -> None:
        try:
            self._queue.put_nowait((topic, payload))
        except queue.Full:
            self._rejected_count += 1
            logger.warning(
                "Queue full, disconnecting for backpressure (rejected=%d)",
                self._rejected_count,
            )
            if self._client is not None:
                self._client.disconnect()

    def start(self) -> None:
        self._client = MqttClient(
            self._settings, self._machine_code, client_suffix="subscriber"
        )
        self._client.connect()
        self._client.subscribe(
            self._settings.telemetry_topic(self._machine_code),
            callback=self._on_message,
            qos=1,
        )
        logger.info(
            "Subscriber listening on %s (maxsize=%d)",
            self._settings.telemetry_topic(self._machine_code),
            self._queue.maxsize,
        )

    def stop(self) -> None:
        if self._client is not None:
            self._client.disconnect()
            self._client = None
