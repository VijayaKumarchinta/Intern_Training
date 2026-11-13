from sqlalchemy import DateTime, bindparam, text
from sqlalchemy.dialects.postgresql import UUID
from server.database import engine

EVENT_HISTORY_SQL = text("""
    SELECT
        id,
        line_id,
        event_type,
        event_code,
        severity,
        state,
        title,
        description,
        event_ts,
        recorded_at,
        reading_id,
        replay_cycle_id,
        details
    FROM telemetry.events
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
    ORDER BY event_ts DESC, id DESC
    LIMIT :row_limit
    """).bindparams(
        bindparam("selected_cycle_id", type_=UUID(as_uuid=False)),
        bindparam("start_time", type_=DateTime()),
        bindparam("end_time", type_=DateTime()),
    )

def get_events(
    line_id: str,
    limit: int = 100,
    cycle_id=None,
    start=None,
    end=None,
):
    with engine.connect() as connection:
        return connection.execute(
            EVENT_HISTORY_SQL,
            {
                "line_id": line_id,
                "selected_cycle_id": cycle_id,
                "start_time": start,
                "end_time": end,
                "row_limit": limit,
            },
        ).mappings().all()