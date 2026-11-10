import logging
from sqlalchemy import select, text
from sqlalchemy.engine import Engine
from database.engine import session_scope
from database.models import (
    Base,
    Dataset,
    Line,
    Machine,
    SignalDefinition,
    StreamState,
)
from contract.schema import (
    CONFIGURATION_FIELDS,
    CONTROLLER_OUTPUT_FIELDS,
    MEASUREMENT_FIELDS,
    SETPOINT_FIELDS,
    STATE_FIELDS,
)

logger = logging.getLogger(__name__)

_DATASET_ID = "line-speed-30-2026-04-17"
_DATASET_FILENAME = "Line_Speed_30.xlsx"
_DATASET_ROWS = 2139
_DATASET_IMPORTED_BY = "phase-3b-seed"
_MACHINE_CODE = "LINE_30"
_LINE_CODE = "LINE_30"

def create_schema(engine: Engine) -> None:
    Base.metadata.create_all(engine)

def _signal_display_name(field: str) -> str:
    return field.replace("_", " ").title()

def _seed_line_and_machine() -> None:
    with session_scope() as session:
        existing_line = session.execute(
            select(Line).where(Line.code == _LINE_CODE)
        ).scalar_one_or_none()
        if existing_line is None:
            line = Line(code=_LINE_CODE, name="Line Speed 30", description=None)
            session.add(line)
            session.flush()
        else:
            line = existing_line

        existing_machine = session.execute(
            select(Machine).where(
                Machine.line_id == line.line_id, Machine.code == _MACHINE_CODE
            )
        ).scalar_one_or_none()
        if existing_machine is None:
            session.add(
                Machine(
                    line_id=line.line_id,
                    code=_MACHINE_CODE,
                    name="Line 30 Machine",
                    description=None,
                )
            )

def _seed_signals() -> None:
    sections = (
        ("measurement", MEASUREMENT_FIELDS),
        ("setpoint", SETPOINT_FIELDS),
        ("controller_output", CONTROLLER_OUTPUT_FIELDS),
        ("state", STATE_FIELDS),
        ("configuration", CONFIGURATION_FIELDS),
    )
    with session_scope() as session:
        existing = set(
            session.execute(select(SignalDefinition.code)).scalars().all()
        )
        added = 0
        for section, fields in sections:
            for field in fields:
                if field in existing:
                    continue
                session.add(
                    SignalDefinition(
                        code=field,
                        name=_signal_display_name(field),
                        unit=None,
                        section=section,
                        description=None,
                    )
                )
                added += 1
        if added:
            logger.info("Seeded %d signal definitions", added)

def _seed_dataset() -> None:
    with session_scope() as session:
        existing = session.execute(
            select(Dataset).where(Dataset.dataset_id == _DATASET_ID)
        ).scalar_one_or_none()
        if existing is None:
            session.add(
                Dataset(
                    dataset_id=_DATASET_ID,
                    source_filename=_DATASET_FILENAME,
                    row_count=_DATASET_ROWS,
                    source_timezone="UTC",
                    timezone_assumed=True,
                    imported_by=_DATASET_IMPORTED_BY,
                )
            )
            logger.info("Seeded dataset %s", _DATASET_ID)

def _seed_stream_state() -> None:
    with session_scope() as session:
        existing = session.execute(select(StreamState)).scalar_one_or_none()
        if existing is None:
            session.add(StreamState(last_reading_offset=0, last_event_offset=0))
            logger.info("Seeded stream_state singleton")

def seed_all() -> None:
    _seed_line_and_machine()
    _seed_signals()
    _seed_dataset()
    _seed_stream_state()

def reset_tables(engine: Engine) -> None:
    Base.metadata.drop_all(engine)
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
