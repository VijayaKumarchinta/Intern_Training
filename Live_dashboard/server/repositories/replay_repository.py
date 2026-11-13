from sqlalchemy import text
from server.database import engine

REPLAY_CYCLES_SQL = text("""
    WITH cycle_statistics AS (
        SELECT
            replay_cycle_id,
            COUNT(*) AS persisted_records,

            COUNT(*) FILTER (
                WHERE payload ? 'replay_total_records'
            ) AS metadata_records,

            COUNT(*) FILTER (
                WHERE payload ->> 'source_file_sha256'
                    ~ '^[0-9a-fA-F]{64}$'
            ) AS hash_records,
            COUNT(*) FILTER (
                WHERE payload ? 'replay_session_id'
                  AND NULLIF(BTRIM(payload ->> 'replay_session_id'), '') IS NOT NULL
            ) AS session_id_records,

            COUNT(DISTINCT payload ->> 'replay_session_id')
                AS session_id_variants,

            COUNT(*) FILTER (
                WHERE payload ->> 'replay_cycle_number' ~ '^[0-9]+$'
            ) AS cycle_number_records,

            COUNT(DISTINCT payload ->> 'replay_cycle_number')
            FILTER (
                WHERE payload ->> 'replay_cycle_number' ~ '^[0-9]+$'
            ) AS cycle_number_variants,

            COUNT(*) FILTER (
                WHERE payload ? 'source_row'
                  AND payload ->> 'source_row' ~ '^[0-9]+$'
            ) AS valid_source_rows,

            COUNT(*) FILTER (
                WHERE payload ->> 'replay_total_records' ~ '^[0-9]+$'
            ) AS expected_count_records,

            COUNT(DISTINCT (payload ->> 'replay_total_records')::BIGINT)
            FILTER (
                WHERE payload ->> 'replay_total_records' ~ '^[0-9]+$'
            ) AS expected_count_variants,

            MAX((payload ->> 'replay_total_records')::BIGINT)
            FILTER (
                WHERE payload ->> 'replay_total_records' ~ '^[0-9]+$'
            ) AS expected_records,

            COUNT(DISTINCT payload ->> 'source_file_sha256')
            FILTER (
                WHERE payload ->> 'source_file_sha256'
                    ~ '^[0-9a-fA-F]{64}$'
            ) AS source_hash_variants,

            MAX(payload ->> 'source_file_sha256')
            FILTER (
                WHERE payload ->> 'source_file_sha256'
                    ~ '^[0-9a-fA-F]{64}$'
            ) AS source_file_sha256,

            COUNT(DISTINCT (payload ->> 'source_row')::BIGINT)
            FILTER (
                WHERE payload ->> 'source_row' ~ '^[0-9]+$'
            ) AS distinct_source_rows,

            MIN((payload ->> 'source_row')::BIGINT)
            FILTER (
                WHERE payload ->> 'source_row' ~ '^[0-9]+$'
            ) AS min_source_row,

            MAX((payload ->> 'source_row')::BIGINT)
            FILTER (
                WHERE payload ->> 'source_row' ~ '^[0-9]+$'
            ) AS max_source_row,

            MAX(payload ->> 'replay_session_id') AS replay_session_id,
            MAX(payload ->> 'replay_cycle_number') AS replay_cycle_number,

            MIN(event_ts) AS first_event_ts,
            MAX(event_ts) AS last_event_ts,
            MIN(received_at) AS first_received_at,
            MAX(received_at) AS last_received_at

        FROM telemetry.readings
        WHERE line_id = :line_id
        GROUP BY replay_cycle_id
    ),

    classified_cycles AS (
        SELECT
            *,
            CASE
                WHEN metadata_records = 0
                    THEN 'UNKNOWN'

                WHEN metadata_records <> persisted_records
                  OR hash_records <> persisted_records
                  OR session_id_records <> persisted_records
                  OR session_id_variants <> 1
                  OR cycle_number_records <> persisted_records
                  OR cycle_number_variants <> 1
                  OR valid_source_rows <> persisted_records
                  OR expected_count_variants <> 1
                  OR source_hash_variants <> 1
                    THEN 'INCOMPLETE'

                WHEN expected_records = persisted_records
                  AND distinct_source_rows = expected_records
                  AND min_source_row = 2
                  AND max_source_row = expected_records + 1
                    THEN 'COMPLETED'

                ELSE 'INCOMPLETE'
            END AS status
        FROM cycle_statistics
    )

    SELECT
        replay_cycle_id,
        replay_session_id,
        replay_cycle_number,
        status,

        persisted_records,
        expected_records,
        distinct_source_rows,
        min_source_row,
        max_source_row,
        source_file_sha256,

        first_event_ts,
        last_event_ts,
        first_received_at,
        last_received_at,

        CASE
            WHEN status = 'COMPLETED'
                THEN 'All expected source records are persisted.'
            WHEN status = 'UNKNOWN'
                THEN 'Legacy cycle has no replay completion metadata.'
            WHEN metadata_records <> persisted_records
                THEN 'Some persisted records are missing replay metadata.'
            WHEN hash_records <> persisted_records
                THEN 'Some persisted records are missing the source fingerprint.'
            WHEN session_id_records <> persisted_records
                THEN 'Some persisted records are missing the replay session ID.'
            WHEN session_id_variants <> 1
                THEN 'Replay session IDs are inconsistent within this cycle.'
            WHEN cycle_number_records <> persisted_records
                THEN 'Some persisted records are missing a valid replay cycle number.'
            WHEN cycle_number_variants <> 1
                THEN 'Replay cycle numbers are inconsistent within this cycle.'
            WHEN valid_source_rows <> persisted_records
                THEN 'Some persisted records have invalid or missing source rows.'
            WHEN expected_count_variants <> 1
                THEN 'Expected record counts are missing or inconsistent.'
            WHEN source_hash_variants <> 1
                THEN 'Source file fingerprints are missing or inconsistent.'
            WHEN expected_records <> persisted_records
                THEN 'Persisted record count does not match the expected count.'
            WHEN distinct_source_rows <> expected_records
                THEN 'Distinct source-row coverage does not match the expected count.'
            WHEN min_source_row <> 2
              OR max_source_row <> expected_records + 1
                THEN 'Source-row boundaries do not match the expected range.'
            ELSE 'Replay completion checks have not been satisfied.'
        END AS status_reason

    FROM classified_cycles
    ORDER BY last_received_at DESC, replay_cycle_id DESC
    LIMIT :limit
""")


def get_replay_cycles(line_id: str, limit: int = 50) -> list[dict]:
    with engine.connect() as connection:
        rows = connection.execute(
            REPLAY_CYCLES_SQL,
            {
                "line_id": line_id,
                "limit": limit,
            },
        ).mappings().all()
    return [dict(row) for row in rows]


