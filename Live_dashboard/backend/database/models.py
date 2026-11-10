from datetime import datetime
from typing import Any
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import expression

class Base(DeclarativeBase):
    pass

_N12_6 = Numeric(12, 6)
_N6_2 = Numeric(6, 2)
_TS = DateTime(timezone=True)

class Line(Base):
    __tablename__ = "lines"

    line_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        _TS, nullable=False, server_default=func.now()
    )

class Machine(Base):
    __tablename__ = "machines"

    machine_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    line_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("lines.line_id"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        _TS, nullable=False, server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("line_id", "code", name="uq_machines_line_code"),
    )

class SignalDefinition(Base):
    __tablename__ = "signal_definitions"

    signal_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    unit: Mapped[str | None] = mapped_column(String(16), nullable=True)
    section: Mapped[str] = mapped_column(String(32), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

class MachineSignalLimit(Base):
    __tablename__ = "machine_signal_limits"

    limit_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    machine_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("machines.machine_id"), nullable=False
    )
    signal_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("signal_definitions.signal_id"), nullable=False
    )
    warning_low: Mapped[float | None] = mapped_column(_N12_6, nullable=True)
    warning_high: Mapped[float | None] = mapped_column(_N12_6, nullable=True)
    critical_low: Mapped[float | None] = mapped_column(_N12_6, nullable=True)
    critical_high: Mapped[float | None] = mapped_column(_N12_6, nullable=True)
    enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=expression.true()
    )
    created_at: Mapped[datetime] = mapped_column(
        _TS, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        _TS, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint("machine_id", "signal_id", name="uq_limits_machine_signal"),
        CheckConstraint(
            "warning_low IS NULL OR critical_low IS NULL OR warning_low >= critical_low",
            name="ck_limits_warning_ge_critical_low",
        ),
        CheckConstraint(
            "warning_high IS NULL OR critical_high IS NULL OR warning_high <= critical_high",
            name="ck_limits_warning_le_critical_high",
        ),
    )

class Dataset(Base):
    __tablename__ = "datasets"

    dataset_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_filename: Mapped[str] = mapped_column(String(256), nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False)
    source_timezone: Mapped[str] = mapped_column(
        String(64), nullable=False, server_default="UTC"
    )
    timezone_assumed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=expression.true()
    )
    imported_at: Mapped[datetime] = mapped_column(
        _TS, nullable=False, server_default=func.now()
    )
    imported_by: Mapped[str] = mapped_column(String(64), nullable=False)

class ReplaySession(Base):
    __tablename__ = "replay_sessions"

    replay_session_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True
    )
    dataset_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("datasets.dataset_id"), nullable=False
    )
    requested_state: Mapped[str] = mapped_column(String(16), nullable=False)
    applied_state: Mapped[str] = mapped_column(String(16), nullable=False)
    replay_cycle: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="1"
    )
    replay_speed: Mapped[float] = mapped_column(
        _N6_2, nullable=False, server_default="1.0"
    )
    current_window_start: Mapped[datetime | None] = mapped_column(
        _TS, nullable=True
    )
    current_window_end: Mapped[datetime | None] = mapped_column(
        _TS, nullable=True
    )
    last_published_sequence: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    started_at: Mapped[datetime] = mapped_column(
        _TS, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        _TS, nullable=False, server_default=func.now(), onupdate=func.now()
    )
    stopped_at: Mapped[datetime | None] = mapped_column(_TS, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "requested_state IN ('stopped','running','paused')",
            name="ck_sessions_requested_state",
        ),
        CheckConstraint(
            "applied_state IN ('stopped','running','paused')",
            name="ck_sessions_applied_state",
        ),
    )

class StreamState(Base):
    __tablename__ = "stream_state"

    singleton: Mapped[bool] = mapped_column(Boolean, primary_key=True, default=True)
    last_reading_offset: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default="0"
    )
    last_event_offset: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default="0"
    )

    __table_args__ = (
        CheckConstraint("singleton = true", name="ck_stream_state_singleton"),
    )

class TelemetryReading(Base):
    __tablename__ = "telemetry_readings"

    reading_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    message_id: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    stream_offset: Mapped[int] = mapped_column(
        BigInteger, nullable=False, unique=True
    )
    dataset_id: Mapped[str] = mapped_column(String(64), nullable=False)
    replay_session_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    replay_cycle: Mapped[int] = mapped_column(Integer, nullable=False)
    source_sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    machine_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("machines.machine_id"), nullable=False
    )
    event_timestamp: Mapped[datetime] = mapped_column(_TS, nullable=False)
    playback_timestamp: Mapped[datetime] = mapped_column(_TS, nullable=False)
    source_date: Mapped[str] = mapped_column(String(10), nullable=False)
    source_time: Mapped[str] = mapped_column(String(8), nullable=False)
    source_millitm: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=expression.text("'{}'::jsonb")
    )
    inserted_at: Mapped[datetime] = mapped_column(
        _TS, nullable=False, server_default=func.now()
    )

    measurement_burner_output_load: Mapped[float] = mapped_column(_N12_6, nullable=False)
    measurement_burner_pv: Mapped[float] = mapped_column(_N12_6, nullable=False)
    measurement_oil_level_pv: Mapped[float] = mapped_column(_N12_6, nullable=False)
    measurement_at6802_filtered: Mapped[float] = mapped_column(_N12_6, nullable=False)
    measurement_tt5101_filtered: Mapped[float] = mapped_column(_N12_6, nullable=False)
    measurement_tt4401_filtered: Mapped[float] = mapped_column(_N12_6, nullable=False)
    measurement_air_inlet_to_burner: Mapped[float] = mapped_column(_N12_6, nullable=False)
    measurement_heat_exchanger_stack_temp: Mapped[float] = mapped_column(_N12_6, nullable=False)
    measurement_aph_outlet: Mapped[float] = mapped_column(_N12_6, nullable=False)
    measurement_ambient_air_temp: Mapped[float] = mapped_column(_N12_6, nullable=False)
    measurement_oil_inlet_temperature: Mapped[float] = mapped_column(_N12_6, nullable=False)
    measurement_tt6102_filtered: Mapped[float] = mapped_column(_N12_6, nullable=False)
    measurement_tt7101_filtered: Mapped[float] = mapped_column(_N12_6, nullable=False)
    measurement_tt7102_filtered: Mapped[float] = mapped_column(_N12_6, nullable=False)
    measurement_tt7103_filtered: Mapped[float] = mapped_column(_N12_6, nullable=False)
    measurement_pump_loading: Mapped[float] = mapped_column(_N12_6, nullable=False)
    measurement_pump_load_pv: Mapped[float] = mapped_column(_N12_6, nullable=False)
    measurement_moisture_pv: Mapped[float] = mapped_column(_N12_6, nullable=False)
    measurement_temp_pid_pv: Mapped[float] = mapped_column(_N12_6, nullable=False)
    measurement_paddle_speed: Mapped[float] = mapped_column(_N12_6, nullable=False)
    measurement_delta_t: Mapped[float] = mapped_column(_N12_6, nullable=False)

    setpoint_burner_sp: Mapped[float] = mapped_column(_N12_6, nullable=False)
    setpoint_pump_load_sp: Mapped[float] = mapped_column(_N12_6, nullable=False)
    setpoint_moisture_speed_pid_sp: Mapped[float] = mapped_column(_N12_6, nullable=False)
    setpoint_moisture_temp_pid_sp: Mapped[float] = mapped_column(_N12_6, nullable=False)

    controller_output_moisture_speed_pid_cv: Mapped[float] = mapped_column(_N12_6, nullable=False)
    controller_output_moisture_temp_pid_cv: Mapped[float] = mapped_column(_N12_6, nullable=False)

    valve_xv6601_open: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    config_moisture_high_setpoint_1: Mapped[float] = mapped_column(_N6_2, nullable=False)
    config_moisture_high_setpoint_2: Mapped[float] = mapped_column(_N6_2, nullable=False)
    config_moisture_low_setpoint_1: Mapped[float] = mapped_column(_N6_2, nullable=False)
    config_moisture_low_setpoint_2: Mapped[float] = mapped_column(_N6_2, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "machine_id",
            "replay_session_id",
            "replay_cycle",
            "source_sequence",
            name="uq_readings_replay_identity",
        ),
        Index("ix_readings_machine_ts", "machine_id", "event_timestamp", "reading_id"),
        CheckConstraint(
            "source_millitm BETWEEN 0 AND 999",
            name="ck_readings_millitm_range",
        ),
        CheckConstraint(
            "valve_xv6601_open IN (0, 1)",
            name="ck_readings_valve_binary",
        ),
    )

class Alarm(Base):
    __tablename__ = "alarms"

    alarm_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    machine_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("machines.machine_id"), nullable=False
    )
    signal_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("signal_definitions.signal_id"), nullable=False
    )
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    raised_at: Mapped[datetime] = mapped_column(
        _TS, nullable=False, server_default=func.now()
    )
    raised_by_reading_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("telemetry_readings.reading_id"), nullable=True
    )
    cleared_at: Mapped[datetime | None] = mapped_column(_TS, nullable=True)
    cleared_by_reading_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("telemetry_readings.reading_id"), nullable=True
    )
    acknowledged_at: Mapped[datetime | None] = mapped_column(_TS, nullable=True)
    acknowledged_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        _TS, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        _TS, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "severity IN ('warning','critical')", name="ck_alarms_severity"
        ),
        CheckConstraint(
            "status IN ('active','acknowledged','cleared')",
            name="ck_alarms_status",
        ),
        Index("ix_alarms_machine_status", "machine_id", "status", "raised_at"),
        Index(
            "ix_alarms_active",
            "status",
            "raised_at",
            postgresql_where=expression.text("status = 'active'"),
        ),
    )

class EventLog(Base):
    __tablename__ = "event_log"

    event_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    machine_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("machines.machine_id"), nullable=True
    )
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=expression.text("'{}'::jsonb")
    )
    occurred_at: Mapped[datetime] = mapped_column(
        _TS, nullable=False, server_default=func.now()
    )
    created_by: Mapped[str | None] = mapped_column(String(64), nullable=True)

    __table_args__ = (
        Index("ix_events_occurred", "occurred_at", "event_id"),
        Index("ix_events_machine_occurred", "machine_id", "occurred_at", "event_id"),
    )

class OperatorNote(Base):
    __tablename__ = "operator_notes"

    note_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    machine_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("machines.machine_id"), nullable=True
    )
    alarm_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("alarms.alarm_id"), nullable=True
    )
    note: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        _TS, nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("ix_notes_machine_created", "machine_id", "created_at"),
        Index("ix_notes_alarm_created", "alarm_id", "created_at"),
    )
