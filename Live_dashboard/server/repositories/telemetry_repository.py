import json
import math
import re
from datetime import datetime
from uuid import UUID as PythonUUID
from sqlalchemy import bindparam, text
from sqlalchemy.dialects.postgresql import UUID
from server.database import engine

RULE_KEY = "moisture_operating_range"
MOISTURE_LOW_LIMIT = 1.10
MOISTURE_HIGH_LIMIT = 1.30

INSERT_TELEMETRY_SQL = text("""
    INSERT INTO telemetry.readings (
        message_id,
        replay_session_id,
        replay_cycle_id,
        replay_cycle_number,
        line_id,
        event_ts,
        payload
    )
    VALUES (
        :message_id,
        :replay_session_id,
        :replay_cycle_id,
        :replay_cycle_number,
        :line_id,
        :event_ts,
        CAST(:payload AS JSONB)
    )
    ON CONFLICT (replay_cycle_id, message_id)
    DO NOTHING
    RETURNING id, received_at
    """).bindparams(
        bindparam("replay_session_id", type_=UUID(as_uuid=False)),
        bindparam("replay_cycle_id", type_=UUID(as_uuid=False)),
    )

INSERT_ALARM_STATE_SQL = text("""
    INSERT INTO telemetry.alarm_state (
        line_id,
        rule_key,
        replay_cycle_id,
        state
    )
    VALUES (
        :line_id,
        :rule_key,
        :replay_cycle_id,
        'NORMAL'
    )
    ON CONFLICT (line_id, rule_key, replay_cycle_id)
    DO NOTHING
    """).bindparams(
        bindparam("replay_cycle_id", type_=UUID(as_uuid=False))
    )

LOCK_ALARM_STATE_SQL = text("""
    SELECT
        state,
        active_event_code
    FROM telemetry.alarm_state
    WHERE line_id = :line_id
      AND rule_key = :rule_key
      AND replay_cycle_id = :replay_cycle_id
    FOR UPDATE
    """).bindparams(
        bindparam("replay_cycle_id", type_=UUID(as_uuid=False))
    )

UPDATE_ALARM_STATE_SQL = text("""
    UPDATE telemetry.alarm_state
    SET
        state = :state,
        severity = :severity,
        active_event_code = :active_event_code,
        last_reading_id = :reading_id,
        last_event_ts = CASE
            WHEN :transitioned THEN :event_ts
            ELSE last_event_ts
        END,
        updated_at = clock_timestamp()
    WHERE line_id = :line_id
      AND rule_key = :rule_key
      AND replay_cycle_id = :replay_cycle_id
    """).bindparams(
        bindparam("replay_cycle_id", type_=UUID(as_uuid=False))
    )

INSERT_EVENT_SQL = text("""
    INSERT INTO telemetry.events (
        line_id,
        event_type,
        event_code,
        severity,
        state,
        title,
        description,
        event_ts,
        reading_id,
        replay_cycle_id,
        details
    )
    VALUES (
        :line_id,
        'ALARM',
        :event_code,
        'WARNING',
        :state,
        :title,
        :description,
        :event_ts,
        :reading_id,
        :replay_cycle_id,
        CAST(:details AS JSONB)
    )
    RETURNING id, recorded_at
    """).bindparams(
        bindparam("replay_cycle_id", type_=UUID(as_uuid=False)),
    )


def _validate_payload(payload: dict) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("Telemetry payload must be a JSON object.")

    required_fields = (
        "message_id",
        "replay_session_id",
        "replay_cycle_id",
        "replay_cycle_number",
        "line_id",
        "event_ts",
    )

    missing = [
        field
        for field in required_fields
        if field not in payload
    ]

    if missing:
        raise ValueError(
            "Telemetry payload is missing fields: "
            + ", ".join(missing)
        )

    message_id = str(payload["message_id"]).strip()
    line_id = str(payload["line_id"]).strip()

    if not message_id:
        raise ValueError("message_id cannot be empty.")

    if not line_id:
        raise ValueError("line_id cannot be empty.")

    try:
        replay_session_id = PythonUUID(
            str(payload["replay_session_id"])
        )
        replay_cycle_id = PythonUUID(
            str(payload["replay_cycle_id"])
        )
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError(
            "Invalid replay session or cycle UUID."
        ) from exc

    raw_cycle_number = payload["replay_cycle_number"]

    if isinstance(raw_cycle_number, bool):
        raise ValueError(
            "replay_cycle_number must be a positive integer."
        )

    try:
        cycle_number = int(raw_cycle_number)
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValueError(
            "replay_cycle_number must be a positive integer."
        ) from exc

    if isinstance(raw_cycle_number, float):
        if not raw_cycle_number.is_integer():
            raise ValueError(
                "replay_cycle_number must be a positive integer."
            )

    if cycle_number <= 0:
        raise ValueError(
            "replay_cycle_number must be greater than zero."
        )
    if "replay_total_records" in payload:
        raw_total = payload["replay_total_records"]
        raw_source_row = payload.get("source_row")
        source_hash = payload.get("source_file_sha256")

        if (
            isinstance(raw_total, bool)
            or not isinstance(raw_total, int)
            or raw_total <= 0
        ):
            raise ValueError(
                "replay_total_records must be a positive integer."
            )

        if (
            isinstance(raw_source_row, bool)
            or not isinstance(raw_source_row, int)
            or not 2 <= raw_source_row <= raw_total + 1
        ):
            raise ValueError(
                "source_row must be an integer within the expected "
                "source dataset row range."
            )

        if (
            not isinstance(source_hash, str)
            or re.fullmatch(r"[0-9a-fA-F]{64}", source_hash) is None
        ):
            raise ValueError(
                "source_file_sha256 must be a valid 64-character "
                "SHA-256 hexadecimal digest."
            )
    try:
        event_ts = datetime.fromisoformat(
            str(payload["event_ts"])
        )
    except (ValueError, TypeError) as exc:
        raise ValueError(
            "event_ts must be a valid ISO 8601 timestamp."
        ) from exc

    if event_ts.tzinfo is not None:
        raise ValueError(
            "event_ts must be timezone-naive for the current "
            "database schema."
        )

    try:
        serialized_payload = json.dumps(
            payload,
            allow_nan=False,
            separators=(",", ":"),
        )
    except (ValueError, TypeError) as exc:
        raise ValueError(
            "Telemetry payload must contain valid JSON values."
        ) from exc

    return {
        "message_id": message_id,
        "replay_session_id": str(replay_session_id),
        "replay_cycle_id": str(replay_cycle_id),
        "replay_cycle_number": cycle_number,
        "line_id": line_id,
        "event_ts": event_ts,
        "payload": serialized_payload,
    }


def _get_moisture_value(payload: dict) -> float | None:
    value = payload.get("Moisture PV")

    if isinstance(value, bool):
        return None

    if not isinstance(value, (int, float)):
        return None

    value = float(value)

    if not math.isfinite(value):
        return None

    return value


def _get_moisture_event_code(value: float) -> str | None:
    if value < MOISTURE_LOW_LIMIT:
        return "MOISTURE_LOW"

    if value > MOISTURE_HIGH_LIMIT:
        return "MOISTURE_HIGH"

    return None


def _event_title(event_code: str) -> str:
    if event_code == "MOISTURE_LOW":
        return "Moisture Below Operating Limit"

    if event_code == "MOISTURE_HIGH":
        return "Moisture Above Operating Limit"

    return "Moisture Operating Range"


def _insert_alarm_event(
    connection,
    *,
    line_id: str,
    event_code: str,
    event_state: str,
    event_ts: datetime,
    reading_id: int,
    replay_cycle_id: str,
    moisture_value: float,
    previous_event_code: str | None,
    next_event_code: str | None,
) -> dict:

    if event_state == "ACTIVE":
        description = (
            f"Moisture PV is {moisture_value:.4f}. "
            f"Operating limits are "
            f"{MOISTURE_LOW_LIMIT:.2f}–"
            f"{MOISTURE_HIGH_LIMIT:.2f}."
        )
    else:
        description = (
            f"Moisture alarm {event_code} cleared. "
            f"Current Moisture PV is {moisture_value:.4f}."
        )

    details = {
        "moisture_value": moisture_value,
        "lower_limit": MOISTURE_LOW_LIMIT,
        "upper_limit": MOISTURE_HIGH_LIMIT,
        "previous_event_code": previous_event_code,
        "next_event_code": next_event_code,
    }

    result = connection.execute(
        INSERT_EVENT_SQL,
        {
            "line_id": line_id,
            "event_code": event_code,
            "state": event_state,
            "title": _event_title(event_code),
            "description": description,
            "event_ts": event_ts,
            "reading_id": reading_id,
            "replay_cycle_id": replay_cycle_id,
            "details": json.dumps(
                details,
                allow_nan=False,
                separators=(",", ":"),
            ),
        },
    )

    inserted = result.mappings().one()

    return {
        "id": inserted["id"],
        "line_id": line_id,
        "event_type": "ALARM",
        "event_code": event_code,
        "severity": "WARNING",
        "state": event_state,
        "title": _event_title(event_code),
        "description": description,
        "event_ts": event_ts.isoformat(),
        "recorded_at": inserted["recorded_at"].isoformat(),
        "reading_id": reading_id,
        "replay_cycle_id": replay_cycle_id,
        "details": details,
    }


def _process_moisture_alarm(
    connection,
    *,
    line_id: str,
    event_ts: datetime,
    reading_id: int,
    replay_cycle_id: str,
    moisture_value: float,
) -> list[dict]:

    new_event_code = _get_moisture_event_code(
        moisture_value
    )

    connection.execute(
        INSERT_ALARM_STATE_SQL,
        {
            "line_id": line_id,
            "rule_key": RULE_KEY,
            "replay_cycle_id": replay_cycle_id,
        },
    )

    current_state = connection.execute(
        LOCK_ALARM_STATE_SQL,
        {
            "line_id": line_id,
            "rule_key": RULE_KEY,
            "replay_cycle_id": replay_cycle_id,
        },
    ).mappings().one()

    current_event_code = (
        current_state["active_event_code"]
        if current_state["state"] == "ACTIVE"
        else None
    )

    events = []

    transitioned = current_event_code != new_event_code

    if transitioned and current_event_code is not None:
        events.append(
            _insert_alarm_event(
                connection,
                line_id=line_id,
                event_code=current_event_code,
                event_state="CLEARED",
                event_ts=event_ts,
                reading_id=reading_id,
                replay_cycle_id=replay_cycle_id,
                moisture_value=moisture_value,
                previous_event_code=current_event_code,
                next_event_code=new_event_code,
            )
        )

    if transitioned and new_event_code is not None:
        events.append(
            _insert_alarm_event(
                connection,
                line_id=line_id,
                event_code=new_event_code,
                event_state="ACTIVE",
                event_ts=event_ts,
                reading_id=reading_id,
                replay_cycle_id=replay_cycle_id,
                moisture_value=moisture_value,
                previous_event_code=current_event_code,
                next_event_code=new_event_code,
            )
        )

    connection.execute(
        UPDATE_ALARM_STATE_SQL,
        {
            "line_id": line_id,
            "rule_key": RULE_KEY,
            "replay_cycle_id": replay_cycle_id,
            "state": (
                "ACTIVE"
                if new_event_code is not None
                else "NORMAL"
            ),
            "severity": (
                "WARNING"
                if new_event_code is not None
                else None
            ),
            "active_event_code": new_event_code,
            "reading_id": reading_id,
            "event_ts": event_ts,
            "transitioned": transitioned,
        },
    )

    return events


def save_telemetry(payload: dict) -> dict | None:
    parameters = _validate_payload(payload)

    with engine.begin() as connection:

        result = connection.execute(
            INSERT_TELEMETRY_SQL,
            parameters,
        )

        reading = result.mappings().one_or_none()

        if reading is None:
            return None

        reading_id = reading["id"]
        received_at = reading["received_at"]

        events = []

        moisture_value = _get_moisture_value(payload)

        if moisture_value is not None:
            events = _process_moisture_alarm(
                connection,
                line_id=parameters["line_id"],
                event_ts=parameters["event_ts"],
                reading_id=reading_id,
                replay_cycle_id=parameters["replay_cycle_id"],
                moisture_value=moisture_value,
            )

        return {
            "id": reading_id,
            "received_at": received_at.isoformat(),
            "events": events,
        }
