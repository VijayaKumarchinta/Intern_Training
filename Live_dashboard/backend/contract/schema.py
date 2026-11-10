from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any
SCHEMA_VERSION = 1
MACHINE_CODE = 'LINE_30'
MEASUREMENT_FIELDS = ('burner_output_load', 'burner_pv', 'oil_level_pv', 'at6802_filtered', 'tt5101_filtered', 'tt4401_filtered', 'air_inlet_to_burner', 'heat_exchanger_stack_temp', 'aph_outlet', 'ambient_air_temp', 'oil_inlet_temperature', 'tt6102_filtered', 'tt7101_filtered', 'tt7102_filtered', 'tt7103_filtered', 'pump_loading', 'pump_load_pv', 'moisture_pv', 'temp_pid_pv', 'paddle_speed', 'delta_t')
SETPOINT_FIELDS = ('burner_sp', 'pump_load_sp', 'moisture_speed_pid_sp', 'moisture_temp_pid_sp')
CONTROLLER_OUTPUT_FIELDS = ('moisture_speed_pid_cv', 'moisture_temp_pid_cv')
STATE_FIELDS = ('valve_xv6601_open',)
CONFIGURATION_FIELDS = ('moisture_high_setpoint_1', 'moisture_high_setpoint_2', 'moisture_low_setpoint_1', 'moisture_low_setpoint_2')
INACTIVE_CHANNELS = ('tt4401_filtered',)
DUPLICATE_PAIRS = (('moisture_pv', 'temp_pid_pv'),)

@dataclass(frozen=True)
class SourceTimestamp:
    date: str
    time: str
    millitm: int

@dataclass(frozen=True)
class TelemetryRecord:
    schema_version: int
    machine_code: str
    event_timestamp: str
    source: SourceTimestamp
    measurements: dict[str, float]
    setpoints: dict[str, float]
    controller_outputs: dict[str, float]
    states: dict[str, int]
    configuration: dict[str, float]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def validate(self) -> None:
        missing = set(MEASUREMENT_FIELDS) - set(self.measurements)
        if missing:
            raise ValueError(f'Missing measurements: {sorted(missing)}')
        missing = set(SETPOINT_FIELDS) - set(self.setpoints)
        if missing:
            raise ValueError(f'Missing setpoints: {sorted(missing)}')
        missing = set(CONTROLLER_OUTPUT_FIELDS) - set(self.controller_outputs)
        if missing:
            raise ValueError(f'Missing controller outputs: {sorted(missing)}')
        missing = set(STATE_FIELDS) - set(self.states)
        if missing:
            raise ValueError(f'Missing states: {sorted(missing)}')
        missing = set(CONFIGURATION_FIELDS) - set(self.configuration)
        if missing:
            raise ValueError(f'Missing configuration: {sorted(missing)}')
        if not all((v in (0, 1) for v in self.states.values())):
            raise ValueError('State values must be 0 or 1')

def default_metadata() -> dict[str, Any]:
    return {'inactive_channels': list(INACTIVE_CHANNELS), 'duplicate_pairs': [list(pair) for pair in DUPLICATE_PAIRS]}
