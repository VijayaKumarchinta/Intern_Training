"""Phase 1 dataset preprocessing for LINE_30.

Reads the raw workbook, applies the frozen timestamp and precision
policies, validates every row through the telemetry schema, and writes
a normalized Parquet dataset plus a validation report.

Read-only with respect to the source workbook.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
import pandas as pd
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / 'backend'))
from contract.schema import MACHINE_CODE, SCHEMA_VERSION, TelemetryRecord, SourceTimestamp, default_metadata, MEASUREMENT_FIELDS, SETPOINT_FIELDS, CONTROLLER_OUTPUT_FIELDS, STATE_FIELDS, CONFIGURATION_FIELDS
SOURCE_PATH = PROJECT_ROOT / 'data' / 'raw' / 'Line_Speed_30.xlsx'
OUTPUT_DIR = PROJECT_ROOT / 'data' / 'processed'
REPORT_DIR = PROJECT_ROOT / 'data' / 'reports'
SHEET_NAME = 'Line_Speed_30'
COLUMN_MAP = {'measurements': {'Burner Output Load': 'burner_output_load', 'Burner PV': 'burner_pv', 'oil Level PV': 'oil_level_pv', '{[PLC1]Input.Analogue.AT6802.O_Filtered}': 'at6802_filtered', '{[PLC1]Input.Analogue.TT5101.O_Filtered}': 'tt5101_filtered', '{[PLC1]Input.Analogue.TT4401.O_Filtered}': 'tt4401_filtered', 'Air Inlet To Burner': 'air_inlet_to_burner', 'Heat Exchanger Stack Temp': 'heat_exchanger_stack_temp', 'APH Outlet': 'aph_outlet', 'Ambient Air Temp': 'ambient_air_temp', 'Oil Inlet Temperature': 'oil_inlet_temperature', '{[PLC1]Input.Analogue.TT6102.O_Filtered}': 'tt6102_filtered', '{[PLC1]Input.Analogue.TT7101.O_Filtered}': 'tt7101_filtered', '{[PLC1]Input.Analogue.TT7102.O_Filtered}': 'tt7102_filtered', '{[PLC1]Input.Analogue.TT7103.O_Filtered}': 'tt7103_filtered', 'Pump Loading': 'pump_loading', 'Pump Load PV': 'pump_load_pv', 'Moisture PV': 'moisture_pv', '{[PLC1]MoistureControl.O_TempPIDPV}': 'temp_pid_pv', 'Paddle Speed': 'paddle_speed', 'DeltaT': 'delta_t'}, 'setpoints': {'Burner SP': 'burner_sp', 'Pump load SP': 'pump_load_sp', '{[PLC1]MoistureControl.O_SpeedPIDSP}': 'moisture_speed_pid_sp', '{[PLC1]MoistureControl.O_TempPIDSP}': 'moisture_temp_pid_sp'}, 'controller_outputs': {'{[PLC1]MoistureControl.O_SpeedPIDCV}': 'moisture_speed_pid_cv', '{[PLC1]MoistureControl.O_TempPIDCV}': 'moisture_temp_pid_cv'}, 'states': {'{[PLC1]Valve.XV6601.OM_Open}': 'valve_xv6601_open'}, 'configuration': {'{[PLC1]MoistureControl.I_MoistureHighSetpoint1}': 'moisture_high_setpoint_1', '{[PLC1]MoistureControl.I_MoistureHighSetpoint2}': 'moisture_high_setpoint_2', '{[PLC1]MoistureControl.I_MoistureLowSetpoint1}': 'moisture_low_setpoint_1', '{[PLC1]MoistureControl.I_MoistureLowSetpoint2}': 'moisture_low_setpoint_2'}}
ANALOG_DECIMALS = 6
CONFIG_DECIMALS = 2

def build_event_timestamp(df: pd.DataFrame) -> pd.Series:
    base = pd.to_datetime(df[';Date'].astype(str) + ' ' + df['Time'].astype(str))
    return base + pd.to_timedelta(pd.to_numeric(df['Millitm']), unit='ms')

def round_analog(value: float) -> float:
    return round(float(value), ANALOG_DECIMALS)

def round_config(value: float) -> float:
    return round(float(value), CONFIG_DECIMALS)

def build_record(row: pd.Series, ts: pd.Timestamp) -> TelemetryRecord:
    measurements = {target: round_analog(row[source]) for source, target in COLUMN_MAP['measurements'].items()}
    setpoints = {target: round_config(row[source]) if 'PID' in source else round_analog(row[source]) for source, target in COLUMN_MAP['setpoints'].items()}
    controller_outputs = {target: round_analog(row[source]) for source, target in COLUMN_MAP['controller_outputs'].items()}
    states = {target: int(row[source]) for source, target in COLUMN_MAP['states'].items()}
    configuration = {target: round_config(row[source]) for source, target in COLUMN_MAP['configuration'].items()}
    record = TelemetryRecord(schema_version=SCHEMA_VERSION, machine_code=MACHINE_CODE, event_timestamp=ts.isoformat(timespec='milliseconds'), source=SourceTimestamp(date=ts.strftime('%Y-%m-%d'), time=ts.strftime('%H:%M:%S'), millitm=int(row['Millitm'])), measurements=measurements, setpoints=setpoints, controller_outputs=controller_outputs, states=states, configuration=configuration, metadata=default_metadata())
    record.validate()
    return record

def flatten(record: TelemetryRecord, source_sequence: int) -> dict:
    flat = {
        "schema_version": record.schema_version,
        "machine_code": record.machine_code,
        "event_timestamp": record.event_timestamp,
        "source_sequence": source_sequence,
        "source_date": record.source.date,
        "source_time": record.source.time,
        "source_millitm": record.source.millitm,
    }
    for section in (
        "measurements",
        "setpoints",
        "controller_outputs",
        "states",
        "configuration",
    ):
        for key, value in getattr(record, section).items():
            flat[f"{section}.{key}"] = value
    return flat

def main() -> None:
    if not SOURCE_PATH.exists():
        raise FileNotFoundError(f'Source workbook not found: {SOURCE_PATH}')
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_excel(SOURCE_PATH, sheet_name=SHEET_NAME, engine='openpyxl')
    timestamps = build_event_timestamp(df)
    rows = []
    errors = []
    for index, row in df.iterrows():
        try:
            record = build_record(row, timestamps.iloc[index])
            rows.append(flatten(record, source_sequence=int(index) + 1))
        except Exception as exc:
            errors.append({'row': int(index) + 2, 'error': str(exc)})
    normalized = pd.DataFrame(rows)
    expected_fields = list(MEASUREMENT_FIELDS) + list(SETPOINT_FIELDS) + list(CONTROLLER_OUTPUT_FIELDS) + list(STATE_FIELDS) + list(CONFIGURATION_FIELDS)
    missing = [f for f in expected_fields if not any((col.endswith(f'.{f}') or col == f for col in normalized.columns))]
    csv_path = OUTPUT_DIR / 'line_speed_30_normalized.csv'
    parquet_path = OUTPUT_DIR / 'line_speed_30_normalized.parquet'
    normalized.to_csv(csv_path, index=False, encoding='utf-8-sig')
    parquet_written = False
    parquet_error = None
    try:
        normalized.to_parquet(parquet_path, index=False)
        parquet_written = True
    except ImportError as exc:
        parquet_error = str(exc)
    sample_payload = build_record(df.iloc[0], timestamps.iloc[0]).to_dict()
    sample_path = REPORT_DIR / 'sample_telemetry_payload.json'
    sample_path.write_text(json.dumps(sample_payload, indent=2), encoding='utf-8')
    report_lines = ['# Line Speed 30 — Phase 1 Preprocessing Report', '', f'- Source workbook: `{SOURCE_PATH.relative_to(PROJECT_ROOT)}`', f'- Sheet: `{SHEET_NAME}`', f'- Records written: {len(normalized):,}', f'- Records rejected: {len(errors):,}', f'- Parquet written: {parquet_written}', f'- Schema version: {SCHEMA_VERSION}', f"- First event timestamp: {normalized['event_timestamp'].iloc[0]}", f"- Last event timestamp:  {normalized['event_timestamp'].iloc[-1]}", '', '## Precision policy applied', '', f'- Analog measurements, setpoints, CVs: {ANALOG_DECIMALS} decimals', f'- Configuration constants and PID SPs: {CONFIG_DECIMALS} decimals', '- States cast to int (0/1)', '', '## Field coverage', '', f'- Expected contract fields: {len(expected_fields)}', f"- Missing fields in output: {missing or 'none'}", '', '## Rejected rows', '']
    if errors:
        for err in errors[:20]:
            report_lines.append(f"- Row {err['row']}: {err['error']}")
    else:
        report_lines.append('- None')
    report_path = REPORT_DIR / 'preprocessing_report.md'
    report_path.write_text('\n'.join(report_lines), encoding='utf-8')
    print('=' * 70)
    print('PREPROCESSING COMPLETE')
    print('=' * 70)
    print(f'Records written:  {len(normalized):,}')
    print(f'Records rejected: {len(errors):,}')
    print(f'CSV:     {csv_path.relative_to(PROJECT_ROOT)}')
    if parquet_written:
        print(f'Parquet: {parquet_path.relative_to(PROJECT_ROOT)}')
    else:
        print('Parquet: not written (install pyarrow or fastparquet)')
        if parquet_error:
            print(f'         reason: {parquet_error.splitlines()[0]}')
    print(f'Report:  {report_path.relative_to(PROJECT_ROOT)}')
    print(f'Sample:  {sample_path.relative_to(PROJECT_ROOT)}')
    if missing:
        print(f'WARNING: missing contract fields: {missing}')
    if errors:
        print(f'WARNING: {len(errors)} rows rejected; see report.')
if __name__ == '__main__':
    main()
