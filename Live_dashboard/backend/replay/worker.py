import json
import logging
import queue
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import pandas as pd
from config.settings import Settings
from contract.schema import (
    MACHINE_CODE,
    SCHEMA_VERSION,
    TelemetryRecord,
    SourceTimestamp,
    default_metadata,
    MEASUREMENT_FIELDS,
    SETPOINT_FIELDS,
    CONTROLLER_OUTPUT_FIELDS,
    STATE_FIELDS,
    CONFIGURATION_FIELDS,
)
from mqtt.client import MqttClient
from replay.identity import compute_message_id
from replay.window import list_windows, load_dataset, select_window

logger = logging.getLogger(__name__)

_DATASET_ID = "line-speed-30-2026-04-17"
_WINDOW_MINUTES = 10

@dataclass
class ReplayState:
    replay_session_id: str = field(
        default_factory=lambda: str(uuid.uuid4())
    )
    replay_cycle: int = 1
    current_window_index: int = 0
    last_published_sequence: int = 0
    requested_state: str = "stopped"
    applied_state: str = "stopped"
    paused: bool = False
    stop_requested: bool = False
    speed_multiplier: float = 1.0

class ReplayWorker:
    def __init__(
        self,
        settings: Settings,
        parquet_path: Path,
        machine_code: str = MACHINE_CODE,
        interval_override: Optional[float] = None,
    ) -> None:
        self._settings = settings
        self._parquet_path = parquet_path
        self._machine_code = machine_code
        self._interval_override = interval_override
        self._command_queue: queue.Queue[dict] = queue.Queue()
        self._state = ReplayState()
        self._published_count = 0
        self._df: Optional[pd.DataFrame] = None

    @property
    def state(self) -> ReplayState:
        return self._state

    @property
    def published_count(self) -> int:
        return self._published_count

    def enqueue_command(self, command: dict) -> None:
        self._command_queue.put(command)

    def _drain_commands(self) -> None:
        while True:
            try:
                command = self._command_queue.get_nowait()
            except queue.Empty:
                return
            kind = command.get("type")
            if kind == "pause":
                self._state.paused = True
                self._state.applied_state = "paused"
                logger.info("Replay paused")
            elif kind == "resume":
                self._state.paused = False
                self._state.applied_state = "running"
                logger.info("Replay resumed")
            elif kind == "speed":
                multiplier = float(command.get("speed_multiplier", 1.0))
                self._state.speed_multiplier = max(multiplier, 0.01)
                logger.info("Replay speed set to %.2fx", self._state.speed_multiplier)
            elif kind == "stop":
                self._state.stop_requested = True
                logger.info("Replay stop requested")
            else:
                logger.warning("Unknown replay command: %s", kind)

    def _wait_with_command_check(self, seconds: float) -> bool:
        if seconds <= 0:
            self._drain_commands()
            return False
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            self._drain_commands()
            if self._state.stop_requested:
                return True
            if self._state.paused:
                time.sleep(0.1)
                continue
            remaining = deadline - time.monotonic()
            time.sleep(min(remaining, 0.1))
        return self._state.stop_requested

    def _row_to_payload(
        self, row: pd.Series, message_id: str, playback_ts: str
    ) -> dict:
        measurements = {
            name: float(row[f"measurements.{name}"])
            for name in MEASUREMENT_FIELDS
        }
        setpoints = {
            name: float(row[f"setpoints.{name}"])
            for name in SETPOINT_FIELDS
        }
        controller_outputs = {
            name: float(row[f"controller_outputs.{name}"])
            for name in CONTROLLER_OUTPUT_FIELDS
        }
        states = {
            name: int(row[f"states.{name}"])
            for name in STATE_FIELDS
        }
        configuration = {
            name: float(row[f"configuration.{name}"])
            for name in CONFIGURATION_FIELDS
        }
        return {
            "schema_version": SCHEMA_VERSION,
            "message_id": message_id,
            "dataset_id": _DATASET_ID,
            "replay_session_id": self._state.replay_session_id,
            "replay_cycle": self._state.replay_cycle,
            "source_sequence": int(row["source_sequence"]),
            "machine_code": self._machine_code,
            "event_timestamp": str(row["event_timestamp"]),
            "playback_timestamp": playback_ts,
            "source": {
                "date": str(row["source_date"]),
                "time": str(row["source_time"]),
                "millitm": int(row["source_millitm"]),
            },
            "measurements": measurements,
            "setpoints": setpoints,
            "controller_outputs": controller_outputs,
            "states": states,
            "configuration": configuration,
            "metadata": default_metadata(),
        }

    def _compute_gap(
        self, previous_ts: Optional[pd.Timestamp], current_ts: pd.Timestamp
    ) -> float:
        if self._interval_override is not None:
            return self._interval_override
        if previous_ts is None:
            return 0.0
        delta = (current_ts - previous_ts).total_seconds()
        return max(delta, 0.0)

    def run(self, limit: Optional[int] = None) -> int:
        self._df = load_dataset(self._parquet_path)
        if self._df.empty:
            logger.warning("Dataset is empty")
            return 0

        windows = list_windows(self._df, window_minutes=_WINDOW_MINUTES)
        self._state.requested_state = "running"
        self._state.applied_state = "running"
        logger.info(
            "Replay session %s, %d window(s), limit=%s",
            self._state.replay_session_id,
            len(windows),
            limit,
        )

        client = MqttClient(
            self._settings, self._machine_code, client_suffix="replay"
        )
        client.connect()
        time.sleep(0.2)

        try:
            while not self._state.stop_requested:
                if limit is not None and self._published_count >= limit:
                    break

                if self._state.current_window_index >= len(windows):
                    self._state.replay_cycle += 1
                    self._state.current_window_index = 0
                    logger.info(
                        "Cycle complete, starting cycle %d",
                        self._state.replay_cycle,
                    )

                window_start, window_end = windows[
                    self._state.current_window_index
                ]
                window_df = select_window(self._df, window_start, window_end)

                previous_ts: Optional[pd.Timestamp] = None
                for _, row in window_df.iterrows():
                    if self._state.stop_requested:
                        break
                    if limit is not None and self._published_count >= limit:
                        break
                    if self._state.paused:
                        while self._state.paused and not self._state.stop_requested:
                            self._drain_commands()
                            time.sleep(0.1)
                        if self._state.stop_requested:
                            break

                    current_ts = pd.to_datetime(row["event_timestamp"])
                    gap = self._compute_gap(previous_ts, current_ts)
                    if self._state.speed_multiplier > 0:
                        gap = gap / self._state.speed_multiplier
                    if self._wait_with_command_check(gap):
                        break

                    message_id = compute_message_id(
                        _DATASET_ID,
                        self._state.replay_session_id,
                        self._state.replay_cycle,
                        int(row["source_sequence"]),
                    )
                    playback_ts = pd.Timestamp.utcnow().isoformat()
                    payload = self._row_to_payload(row, message_id, playback_ts)
                    client.publish(
                        self._settings.telemetry_topic(self._machine_code),
                        payload,
                        qos=1,
                        retain=False,
                    )
                    self._published_count += 1
                    self._state.last_published_sequence = int(
                        row["source_sequence"]
                    )
                    previous_ts = current_ts

                if self._state.stop_requested:
                    break

                self._state.current_window_index += 1
        finally:
            client.disconnect()
            self._state.applied_state = "stopped"
            self._state.requested_state = "stopped"
            logger.info(
                "Replay finished, %d record(s) published",
                self._published_count,
            )

        return self._published_count
