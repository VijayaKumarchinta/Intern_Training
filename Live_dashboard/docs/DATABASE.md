# Database Documentation

Normalized PostgreSQL schema with 10 tables per README.md Section 8.

## Core Tables

- `lines` - Production line master data
- `machines` - Machine master with line_id foreign key
- `signal_definitions` - Signal catalog (OIL_TEMPERATURE, DELTA_T, BURNER_LOAD, MOISTURE, PADDLE_SPEED, OIL_LEVEL)
- `machine_signal_limits` - Machine-specific warning/critical limits
- `telemetry_samples` - One row per MQTT message (machine_id, ts, seq, status)
- `telemetry_values` - One row per signal measurement (machine_id, ts, signal_id, value)
- `telemetry_latest` - Latest sample pointer per machine
- `alarms` - Alarm occurrences with state and acknowledgement tracking
- `event_log` - Append-only operational event history
- `operator_notes` - Section annotations and notes

## Normalization Rules

1. Machine identity in `machines`, not duplicated in telemetry
2. Signal definitions in `signal_definitions`, not in telemetry rows
3. Machine-specific limits in `machine_signal_limits`, not repeated per record
4. Historical readings in `telemetry_samples` + `telemetry_values`
5. Latest state uses separate pointer table `telemetry_latest`
6. Alarms separate from raw telemetry
7. Event history separate from current alarm state

## Operational Guarantees

- Duplicate protection: Unique sample key + ON CONFLICT DO NOTHING
- Consistent telemetry: Sample and values in one transaction
- Latest-state consistency: Pointer updated in same transaction
- No uncommitted broadcast: WebSocket only after commit
