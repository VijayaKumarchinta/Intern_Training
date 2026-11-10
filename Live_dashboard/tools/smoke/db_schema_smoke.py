from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_PROJECT_ROOT / "backend"))

from sqlalchemy import inspect, text  # noqa: E402

from config.settings import load_settings  # noqa: E402
from database.engine import dispose_engine, init_engine  # noqa: E402
from database.init_db import create_schema, seed_all  # noqa: E402


EXPECTED_TABLES = {
    "datasets",
    "lines",
    "machines",
    "signal_definitions",
    "machine_signal_limits",
    "replay_sessions",
    "stream_state",
    "telemetry_readings",
    "alarms",
    "event_log",
    "operator_notes",
}

EXPECTED_SIGNAL_COUNT = 32
EXPECTED_LINES = 1
EXPECTED_MACHINES = 1
EXPECTED_DATASETS = 1


def main() -> int:
    settings = load_settings()
    engine = init_engine(settings)

    try:
        create_schema(engine)
        seed_all()

        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        missing = EXPECTED_TABLES - tables
        extra = tables - EXPECTED_TABLES
        if missing:
            print(f"FAIL: missing tables: {sorted(missing)}")
            return 1
        if extra:
            print(f"WARN: extra tables: {sorted(extra)}")

        with engine.connect() as conn:
            lines = conn.execute(text("SELECT COUNT(*) FROM lines")).scalar()
            machines = conn.execute(text("SELECT COUNT(*) FROM machines")).scalar()
            signals = conn.execute(
                text("SELECT COUNT(*) FROM signal_definitions")
            ).scalar()
            datasets = conn.execute(text("SELECT COUNT(*) FROM datasets")).scalar()
            stream_rows = conn.execute(
                text("SELECT COUNT(*) FROM stream_state")
            ).scalar()

        print(f"lines: {lines}")
        print(f"machines: {machines}")
        print(f"signal_definitions: {signals}")
        print(f"datasets: {datasets}")
        print(f"stream_state rows: {stream_rows}")

        if lines != EXPECTED_LINES:
            print(f"FAIL: expected {EXPECTED_LINES} line(s), got {lines}")
            return 1
        if machines != EXPECTED_MACHINES:
            print(f"FAIL: expected {EXPECTED_MACHINES} machine(s), got {machines}")
            return 1
        if signals != EXPECTED_SIGNAL_COUNT:
            print(
                f"FAIL: expected {EXPECTED_SIGNAL_COUNT} signals, got {signals}"
            )
            return 1
        if datasets != EXPECTED_DATASETS:
            print(f"FAIL: expected {EXPECTED_DATASETS} dataset, got {datasets}")
            return 1
        if stream_rows != 1:
            print(f"FAIL: expected 1 stream_state row, got {stream_rows}")
            return 1

        telemetry_columns = [
            c["name"] for c in inspector.get_columns("telemetry_readings")
        ]
        measurement_cols = [
            c for c in telemetry_columns if c.startswith("measurement_")
        ]
        setpoint_cols = [c for c in telemetry_columns if c.startswith("setpoint_")]
        controller_cols = [
            c for c in telemetry_columns if c.startswith("controller_output_")
        ]
        config_cols = [c for c in telemetry_columns if c.startswith("config_")]

        print(
            f"telemetry_readings contract columns: "
            f"{len(measurement_cols)} measurement, "
            f"{len(setpoint_cols)} setpoint, "
            f"{len(controller_cols)} controller_output, "
            f"{len(config_cols)} config, "
            f"1 state"
        )

        if len(measurement_cols) != 21:
            print(f"FAIL: expected 21 measurement columns, got {len(measurement_cols)}")
            return 1
        if len(setpoint_cols) != 4:
            print(f"FAIL: expected 4 setpoint columns, got {len(setpoint_cols)}")
            return 1
        if len(controller_cols) != 2:
            print(
                f"FAIL: expected 2 controller_output columns, "
                f"got {len(controller_cols)}"
            )
            return 1
        if len(config_cols) != 4:
            print(f"FAIL: expected 4 config columns, got {len(config_cols)}")
            return 1

        with engine.connect() as conn:
            unique_constraints = conn.execute(
                text(
                    "SELECT conname FROM pg_constraint "
                    "WHERE conrelid = 'telemetry_readings'::regclass "
                    "AND contype = 'u'"
                )
            ).scalars().all()
        if "uq_readings_replay_identity" not in unique_constraints:
            print(
                f"FAIL: replay identity constraint missing. Found: {unique_constraints}"
            )
            return 1
        if "telemetry_readings_message_id_key" not in unique_constraints:
            print(
                f"FAIL: message_id unique missing. Found: {unique_constraints}"
            )
            return 1

        print(f"unique constraints: {sorted(unique_constraints)}")

    finally:
        dispose_engine()

    print("OK: 11 tables created and seeded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
