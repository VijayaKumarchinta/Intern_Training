# Line Speed 30 — Signal Contract (Phase 1)

Frozen 2026-11-10. Source: `data/raw/Line_Speed_30.xlsx`, sheet `Line_Speed_30`.
2,139 records, 2026-04-17 12:09:53.162 to 18:06:21.504, strictly increasing, zero duplicates.

## Timestamp rule

Rationale: combined timestamp is strictly increasing, zero duplicates, and the eight
11-second source-time gaps are explained by millisecond rollovers (e.g.
12:56:13.981 -> 12:56:24.062 = 10.081 s). `DeltaT` is a process signal, not the
record interval.

## Precision policy

| Group | Decimals | Reason |
|---|---:|---|
| Measurements | 6 | Preserves source resolution, kills float32 noise |
| Varying setpoints | 6 | Same |
| PID setpoints (constant) | 2 | Source values are clean 2-decimal floats |
| Controller outputs | 6 | Varying analog |
| Configuration | 2 | Source values clean 2-decimal floats |
| States | int | 0/1 |

## Source column to contract field

| Source column | Section | Contract field |
|---|---|---|
| Burner Output Load | measurements | burner_output_load |
| Burner PV | measurements | burner_pv |
| oil Level PV | measurements | oil_level_pv |
| {[PLC1]Input.Analogue.AT6802.O_Filtered} | measurements | at6802_filtered |
| {[PLC1]Input.Analogue.TT5101.O_Filtered} | measurements | tt5101_filtered |
| {[PLC1]Input.Analogue.TT4401.O_Filtered} | measurements | tt4401_filtered |
| Air Inlet To Burner | measurements | air_inlet_to_burner |
| Heat Exchanger Stack Temp | measurements | heat_exchanger_stack_temp |
| APH Outlet | measurements | aph_outlet |
| Ambient Air Temp | measurements | ambient_air_temp |
| Oil Inlet Temperature | measurements | oil_inlet_temperature |
| {[PLC1]Input.Analogue.TT6102.O_Filtered} | measurements | tt6102_filtered |
| {[PLC1]Input.Analogue.TT7101.O_Filtered} | measurements | tt7101_filtered |
| {[PLC1]Input.Analogue.TT7102.O_Filtered} | measurements | tt7102_filtered |
| {[PLC1]Input.Analogue.TT7103.O_Filtered} | measurements | tt7103_filtered |
| Pump Loading | measurements | pump_loading |
| Pump Load PV | measurements | pump_load_pv |
| Moisture PV | measurements | moisture_pv |
| {[PLC1]MoistureControl.O_TempPIDPV} | measurements | temp_pid_pv |
| Paddle Speed | measurements | paddle_speed |
| DeltaT | measurements | delta_t |
| Burner SP | setpoints | burner_sp |
| Pump load SP | setpoints | pump_load_sp |
| {[PLC1]MoistureControl.O_SpeedPIDSP} | setpoints | moisture_speed_pid_sp |
| {[PLC1]MoistureControl.O_TempPIDSP} | setpoints | moisture_temp_pid_sp |
| {[PLC1]MoistureControl.O_SpeedPIDCV} | controller_outputs | moisture_speed_pid_cv |
| {[PLC1]MoistureControl.O_TempPIDCV} | controller_outputs | moisture_temp_pid_cv |
| {[PLC1]Valve.XV6601.OM_Open} | states | valve_xv6601_open |
| {[PLC1]MoistureControl.I_MoistureHighSetpoint1} | configuration | moisture_high_setpoint_1 |
| {[PLC1]MoistureControl.I_MoistureHighSetpoint2} | configuration | moisture_high_setpoint_2 |
| {[PLC1]MoistureControl.I_MoistureLowSetpoint1} | configuration | moisture_low_setpoint_1 |
| {[PLC1]MoistureControl.I_MoistureLowSetpoint2} | configuration | moisture_low_setpoint_2 |

## Annotations

- **Inactive channel:** `tt4401_filtered` is constant 0 across all 2,139 records.
  Preserved in payload for source parity; tagged in `metadata.inactive_channels`.
- **Duplicate pair:** `moisture_pv` == `temp_pid_pv` bit-exactly.
  Both preserved; tagged in `metadata.duplicate_pairs`.
- **Not duplicates:** `burner_pv` and `oil_inlet_temperature` track closely but
  diverge by up to 0.081 on 1,517 rows. Kept as distinct signals.
- **Valve activity:** `valve_xv6601_open` has 152 transitions and is open on
  117/2,139 records (5.47%). Active signal, not stuck.

## Explicit exclusions

- `DeltaT` is a process signal, not the replay interval. Replay timing is
  configured independently (`REPLAY_INTERVAL_SECONDS`).
- `Sheet1` contains three operational notes, not telemetry. Preserved as
  reference; not loaded into the replay stream.
- No source values are altered beyond the precision rounding described above.

