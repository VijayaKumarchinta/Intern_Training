from sqlalchemy import DateTime, String, bindparam, text
from sqlalchemy.dialects.postgresql import UUID
from server.database import engine

LATEST_READING_SQL = text("""
    SELECT
        id,
        message_id,
        replay_session_id,
        replay_cycle_id,
        replay_cycle_number,
        line_id,
        event_ts,
        received_at,
        payload
    FROM telemetry.readings
    WHERE line_id = :line_id
    AND replay_cycle_id = (
        SELECT replay_cycle_id
        FROM telemetry.readings
        WHERE line_id = :line_id
        ORDER BY received_at DESC, id DESC
        LIMIT 1
    )
    ORDER BY event_ts DESC, id DESC
    LIMIT 1
    """)

HISTORY_SQL = text("""
    SELECT
        id,
        message_id,
        replay_session_id,
        replay_cycle_id,
        replay_cycle_number,
        line_id,
        event_ts,
        received_at,
        payload
    FROM telemetry.readings
    WHERE line_id = :line_id
      AND replay_cycle_id = COALESCE(
          :selected_cycle_id,
          (
              SELECT replay_cycle_id
              FROM telemetry.readings
              WHERE line_id = :line_id
              ORDER BY received_at DESC, id DESC
              LIMIT 1
          )
      )
      AND (:start_time IS NULL OR event_ts >= :start_time)
      AND (:end_time IS NULL OR event_ts < :end_time)
      AND (:before_time IS NULL OR event_ts < :before_time)
    ORDER BY event_ts DESC, id DESC
    LIMIT :row_limit
    """).bindparams(
        bindparam("selected_cycle_id", type_=UUID(as_uuid=False)),
        bindparam("start_time", type_=DateTime()),
        bindparam("end_time", type_=DateTime()),
        bindparam("before_time", type_=DateTime()),
    )

STATISTICS_SQL = text("""
    WITH selected_cycle AS (
        SELECT COALESCE(
            :selected_cycle_id,
            (
                SELECT replay_cycle_id
                FROM telemetry.readings
                WHERE line_id = :line_id
                ORDER BY received_at DESC, id DESC
                LIMIT 1
            )
        ) AS replay_cycle_id
    )
    SELECT
        selected_cycle.replay_cycle_id AS cycle_id,

        COUNT(*) FILTER (
            WHERE jsonb_typeof(readings.payload -> :field_name) = 'number'
        ) AS sample_count,

        AVG((readings.payload ->> :field_name)::NUMERIC) FILTER (
            WHERE jsonb_typeof(readings.payload -> :field_name) = 'number'
        ) AS average,

        MIN((readings.payload ->> :field_name)::NUMERIC) FILTER (
            WHERE jsonb_typeof(readings.payload -> :field_name) = 'number'
        ) AS minimum,

        MAX((readings.payload ->> :field_name)::NUMERIC) FILTER (
            WHERE jsonb_typeof(readings.payload -> :field_name) = 'number'
        ) AS maximum

    FROM selected_cycle
    LEFT JOIN telemetry.readings AS readings
      ON readings.line_id = :line_id
     AND readings.replay_cycle_id = selected_cycle.replay_cycle_id
     AND (:start_time IS NULL OR readings.event_ts >= :start_time)
     AND (:end_time IS NULL OR readings.event_ts < :end_time)
    GROUP BY selected_cycle.replay_cycle_id
    """).bindparams(
        bindparam("selected_cycle_id", type_=UUID(as_uuid=False)),
        bindparam("field_name", type_=String()),
        bindparam("start_time", type_=DateTime()),
        bindparam("end_time", type_=DateTime()),
    )

def get_latest_reading(line_id: str):
    with engine.connect() as connection:
        return connection.execute(
            LATEST_READING_SQL,
            {"line_id": line_id},
        ).mappings().one_or_none()

def get_reading_history(
    line_id: str,
    before,
    limit: int,
    cycle_id=None,
    start=None,
    end=None,
):
    with engine.connect() as connection:
        return connection.execute(
            HISTORY_SQL,
            {
                "line_id": line_id,
                "selected_cycle_id": cycle_id,
                "start_time": start,
                "end_time": end,
                "before_time": before,
                "row_limit": limit,
            },
        ).mappings().all()
    
def get_reading_statistics(
    line_id: str,
    field: str,
    start,
    end,
    cycle_id=None,
):
    with engine.connect() as connection:
        return connection.execute(
            STATISTICS_SQL,
            {
                "line_id": line_id,
                "selected_cycle_id": cycle_id,
                "field_name": field,
                "start_time": start,
                "end_time": end,
            },
        ).mappings().one()
