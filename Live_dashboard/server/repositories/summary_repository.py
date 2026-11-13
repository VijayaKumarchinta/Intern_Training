from datetime import datetime, timedelta
from sqlalchemy import DateTime, bindparam, text
from sqlalchemy.dialects.postgresql import UUID
from server.database import engine

CYCLE_INFO_SQL = text("""
    SELECT
        replay_cycle_id,
        MIN(event_ts) AS first_event_ts,
        MAX(event_ts) AS last_event_ts
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
    GROUP BY replay_cycle_id
    """).bindparams(
        bindparam("selected_cycle_id", type_=UUID(as_uuid=False)),
    )

HOURLY_SUMMARY_SQL = text("""
WITH
        buckets AS (
            SELECT generate_series(
                :window_start,
                :window_end,
                INTERVAL '1 hour'
            ) AS hour_start
        ),

        cycle_readings AS (
            SELECT
                id,
                event_ts,
                CASE
                    WHEN jsonb_typeof(
                        payload -> 'Burner Output Load'
                    ) = 'number'
                    THEN (payload ->> 'Burner Output Load')::NUMERIC
                END AS burner_load,

                CASE
                    WHEN jsonb_typeof(payload -> 'Burner PV') = 'number'
                    THEN (payload ->> 'Burner PV')::NUMERIC
                END AS burner_pv,

                CASE
                    WHEN jsonb_typeof(payload -> 'DeltaT') = 'number'
                    THEN (payload ->> 'DeltaT')::NUMERIC
                END AS delta_t,

                CASE
                    WHEN jsonb_typeof(payload -> 'Moisture PV') = 'number'
                    THEN (payload ->> 'Moisture PV')::NUMERIC
                END AS moisture,

                CASE
                    WHEN jsonb_typeof(payload -> 'Paddle Speed') = 'number'
                    THEN (payload ->> 'Paddle Speed')::NUMERIC
                END AS paddle_speed,

                CASE
                    WHEN jsonb_typeof(payload -> 'oil Level PV') = 'number'
                    THEN (payload ->> 'oil Level PV')::NUMERIC
                END AS oil_level

            FROM telemetry.readings
            WHERE line_id = :line_id
             AND replay_cycle_id = :cycle_id
        ),

        ordered_readings AS (
            SELECT
                id,
                event_ts,
                burner_load,
                burner_pv,
                delta_t,
                moisture,
                paddle_speed,
                oil_level,
                LEAD(event_ts) OVER (
                    ORDER BY event_ts, id
                ) AS next_event_ts
            FROM cycle_readings
        ),

        hourly_metrics AS (
            SELECT
                date_trunc('hour', event_ts) AS hour_start,
                COUNT(*) AS sample_count,

                AVG(burner_pv) AS burner_pv_avg,
                MIN(burner_pv) AS burner_pv_min,
                MAX(burner_pv) AS burner_pv_max,

                AVG(delta_t) AS delta_t_avg,
                MIN(delta_t) AS delta_t_min,
                MAX(delta_t) AS delta_t_max,

                AVG(burner_load) AS burner_load_avg,
                MIN(burner_load) AS burner_load_min,
                MAX(burner_load) AS burner_load_max,

                AVG(moisture) AS moisture_avg,
                MIN(moisture) AS moisture_min,
                MAX(moisture) AS moisture_max,

                AVG(paddle_speed) AS paddle_speed_avg,
                MIN(paddle_speed) AS paddle_speed_min,
                MAX(paddle_speed) AS paddle_speed_max,

                AVG(oil_level) AS oil_level_avg,
                MIN(oil_level) AS oil_level_min,
                MAX(oil_level) AS oil_level_max

            FROM ordered_readings
            WHERE event_ts >= :window_start
              AND event_ts < :window_end + INTERVAL '1 hour'
            GROUP BY date_trunc('hour', event_ts)
        ),

        burner_intervals AS (
            SELECT
                event_ts,
                next_event_ts
            FROM ordered_readings
            WHERE burner_load = 100
              AND next_event_ts > event_ts
              AND event_ts < :window_end + INTERVAL '1 hour'
              AND next_event_ts > :window_start
        ),

        burner_hour_splits AS (
            SELECT
                hour_bucket.hour_start,
                EXTRACT(
                    EPOCH FROM (
                        LEAST(
                            burner_intervals.next_event_ts,
                            hour_bucket.hour_start + INTERVAL '1 hour'
                        )
                        -
                        GREATEST(
                            burner_intervals.event_ts,
                            hour_bucket.hour_start
                        )
                    )
                ) AS duration_seconds
            FROM burner_intervals
            CROSS JOIN LATERAL generate_series(
                date_trunc(
                    'hour',
                    GREATEST(
                        burner_intervals.event_ts,
                        :window_start
                    )
                ),
                date_trunc(
                    'hour',
                    LEAST(
                        burner_intervals.next_event_ts,
                        :window_end + INTERVAL '1 hour'
                    ) - INTERVAL '1 microsecond'
                ),
                INTERVAL '1 hour'
            ) AS hour_bucket(hour_start)
        ),
        burner_durations AS (
            SELECT
                hour_start,
                SUM(duration_seconds) AS burner_at_100_seconds
            FROM burner_hour_splits
            GROUP BY hour_start
        )

        SELECT
            buckets.hour_start,
            COALESCE(metrics.sample_count, 0) AS sample_count,

            metrics.burner_pv_avg,
            metrics.burner_pv_min,
            metrics.burner_pv_max,

            metrics.delta_t_avg,
            metrics.delta_t_min,
            metrics.delta_t_max,

            metrics.burner_load_avg,
            metrics.burner_load_min,
            metrics.burner_load_max,

            metrics.moisture_avg,
            metrics.moisture_min,
            metrics.moisture_max,

            metrics.paddle_speed_avg,
            metrics.paddle_speed_min,
            metrics.paddle_speed_max,

            metrics.oil_level_avg,
            metrics.oil_level_min,
            metrics.oil_level_max,

            COALESCE(
                durations.burner_at_100_seconds,
                0
            ) AS burner_at_100_seconds

        FROM buckets
        LEFT JOIN hourly_metrics AS metrics
            ON metrics.hour_start = buckets.hour_start
        LEFT JOIN burner_durations AS durations
            ON durations.hour_start = buckets.hour_start
        ORDER BY buckets.hour_start ASC
        """).bindparams(
            bindparam("cycle_id", type_=UUID(as_uuid=False)),
            bindparam("window_start", type_=DateTime()),
            bindparam("window_end", type_=DateTime()),
        )

SUMMARY_STATISTICS_SQL = text("""
    SELECT
        COUNT(*) AS sample_count,

        AVG((payload ->> 'Burner PV')::NUMERIC) FILTER (
            WHERE jsonb_typeof(payload -> 'Burner PV') = 'number'
        ) AS burner_pv_avg,
        MIN((payload ->> 'Burner PV')::NUMERIC) FILTER (
            WHERE jsonb_typeof(payload -> 'Burner PV') = 'number'
        ) AS burner_pv_min,
        MAX((payload ->> 'Burner PV')::NUMERIC) FILTER (
            WHERE jsonb_typeof(payload -> 'Burner PV') = 'number'
        ) AS burner_pv_max,

        AVG((payload ->> 'DeltaT')::NUMERIC) FILTER (
            WHERE jsonb_typeof(payload -> 'DeltaT') = 'number'
        ) AS delta_t_avg,
        MIN((payload ->> 'DeltaT')::NUMERIC) FILTER (
            WHERE jsonb_typeof(payload -> 'DeltaT') = 'number'
        ) AS delta_t_min,
        MAX((payload ->> 'DeltaT')::NUMERIC) FILTER (
            WHERE jsonb_typeof(payload -> 'DeltaT') = 'number'
        ) AS delta_t_max,

        AVG((payload ->> 'Burner Output Load')::NUMERIC) FILTER (
            WHERE jsonb_typeof(payload -> 'Burner Output Load') = 'number'
        ) AS burner_load_avg,
        MIN((payload ->> 'Burner Output Load')::NUMERIC) FILTER (
            WHERE jsonb_typeof(payload -> 'Burner Output Load') = 'number'
        ) AS burner_load_min,
        MAX((payload ->> 'Burner Output Load')::NUMERIC) FILTER (
            WHERE jsonb_typeof(payload -> 'Burner Output Load') = 'number'
        ) AS burner_load_max,

        AVG((payload ->> 'Moisture PV')::NUMERIC) FILTER (
            WHERE jsonb_typeof(payload -> 'Moisture PV') = 'number'
        ) AS moisture_avg,
        MIN((payload ->> 'Moisture PV')::NUMERIC) FILTER (
            WHERE jsonb_typeof(payload -> 'Moisture PV') = 'number'
        ) AS moisture_min,
        MAX((payload ->> 'Moisture PV')::NUMERIC) FILTER (
            WHERE jsonb_typeof(payload -> 'Moisture PV') = 'number'
        ) AS moisture_max,

        AVG((payload ->> 'Paddle Speed')::NUMERIC) FILTER (
            WHERE jsonb_typeof(payload -> 'Paddle Speed') = 'number'
        ) AS paddle_speed_avg,
        MIN((payload ->> 'Paddle Speed')::NUMERIC) FILTER (
            WHERE jsonb_typeof(payload -> 'Paddle Speed') = 'number'
        ) AS paddle_speed_min,
        MAX((payload ->> 'Paddle Speed')::NUMERIC) FILTER (
            WHERE jsonb_typeof(payload -> 'Paddle Speed') = 'number'
        ) AS paddle_speed_max,

        AVG((payload ->> 'oil Level PV')::NUMERIC) FILTER (
            WHERE jsonb_typeof(payload -> 'oil Level PV') = 'number'
        ) AS oil_level_avg,
        MIN((payload ->> 'oil Level PV')::NUMERIC) FILTER (
            WHERE jsonb_typeof(payload -> 'oil Level PV') = 'number'
        ) AS oil_level_min,
        MAX((payload ->> 'oil Level PV')::NUMERIC) FILTER (
            WHERE jsonb_typeof(payload -> 'oil Level PV') = 'number'
        ) AS oil_level_max

    FROM telemetry.readings
    WHERE line_id = :line_id
      AND replay_cycle_id = :cycle_id
      AND event_ts >= :window_start
      AND event_ts < :window_end + INTERVAL '1 hour'
    """).bindparams(
        bindparam("cycle_id", type_=UUID(as_uuid=False)),
        bindparam("window_start", type_=DateTime()),
        bindparam("window_end", type_=DateTime()),
    )


def get_hourly_summary_data(
    line_id: str,
    hours: int | None = None,
    cycle_id: str | None = None,
    hour_start: datetime | None = None,
) -> dict | None:
    """Fetch a complete cycle summary or one selected hourly bucket."""

    with engine.connect() as connection:
        cycle_info = connection.execute(
            CYCLE_INFO_SQL,
            {
                "line_id": line_id,
                "selected_cycle_id": cycle_id,
            },
        ).mappings().one_or_none()

        if cycle_info is None:
            return None

        cycle_id = cycle_info["replay_cycle_id"]
        first_event_ts = cycle_info["first_event_ts"]
        last_event_ts = cycle_info["last_event_ts"]

        if first_event_ts is None or last_event_ts is None:
            return None

        if hour_start is not None:
            window_start = hour_start.replace(
                minute=0,
                second=0,
                microsecond=0,
            )
            window_end = window_start

        elif hours is None:
            window_start = first_event_ts.replace(
                minute=0,
                second=0,
                microsecond=0,
            )
            window_end = last_event_ts.replace(
                minute=0,
                second=0,
                microsecond=0,
            )

        else:
            window_end = last_event_ts.replace(
                minute=0,
                second=0,
                microsecond=0,
            )
            window_start = window_end - timedelta(hours=hours - 1)

        parameters = {
            "line_id": line_id,
            "cycle_id": cycle_id,
            "window_start": window_start,
            "window_end": window_end,
        }

        hourly_rows = connection.execute(
            HOURLY_SUMMARY_SQL,
            parameters,
        ).mappings().all()

        statistics = connection.execute(
            SUMMARY_STATISTICS_SQL,
            parameters,
        ).mappings().one()

    return {
        "cycle_id": cycle_id,
        "window_start": window_start,
        "window_end": window_end,
        "hourly_rows": hourly_rows,
        "statistics": statistics,
    }