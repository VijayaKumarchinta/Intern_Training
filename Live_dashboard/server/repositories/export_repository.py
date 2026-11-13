from sqlalchemy import DateTime, bindparam, text
from sqlalchemy.dialects.postgresql import UUID

from server.database import engine

EXPORT_READINGS_SQL = text("""
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
    ORDER BY event_ts ASC, id ASC
    LIMIT :row_limit
    """).bindparams(
        bindparam("selected_cycle_id", type_=UUID(as_uuid=False)),
        bindparam("start_time", type_=DateTime()),
        bindparam("end_time", type_=DateTime()),
    )


def get_readings_for_export(
    line_id: str,
    limit: int,
    cycle_id=None,
    start=None,
    end=None,
):
    with engine.connect() as connection:
        return connection.execute(
            EXPORT_READINGS_SQL,
            {
                "line_id": line_id,
                "selected_cycle_id": cycle_id,
                "start_time": start,
                "end_time": end,
                "row_limit": limit,
            },
        ).mappings().all()
