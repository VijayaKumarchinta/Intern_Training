GRANT CONNECT ON DATABASE line_speed_30_db TO line30_app;
CREATE SCHEMA IF NOT EXISTS telemetry AUTHORIZATION postgres;
GRANT USAGE ON SCHEMA telemetry TO line30_app;

CREATE TABLE IF NOT EXISTS telemetry.readings (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    message_id TEXT NOT NULL,
    replay_session_id UUID NOT NULL,
    replay_cycle_id UUID NOT NULL,
    replay_cycle_number INTEGER NOT NULL,

    line_id TEXT NOT NULL,

    event_ts TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    received_at TIMESTAMP WITH TIME ZONE NOT NULL
        DEFAULT clock_timestamp(),

    payload JSONB NOT NULL,

    CONSTRAINT uq_readings_cycle_message
        UNIQUE (replay_cycle_id, message_id),

    CONSTRAINT chk_readings_message_id
        CHECK (length(trim(message_id)) > 0),

    CONSTRAINT chk_readings_line_id
        CHECK (length(trim(line_id)) > 0),

    CONSTRAINT chk_readings_cycle_number
        CHECK (replay_cycle_number > 0),

    CONSTRAINT chk_readings_payload_object
        CHECK (jsonb_typeof(payload) = 'object')
);


-- Readings indexes

CREATE INDEX IF NOT EXISTS idx_readings_line_event_ts
    ON telemetry.readings (line_id, event_ts DESC);

CREATE INDEX IF NOT EXISTS idx_readings_received_at
    ON telemetry.readings (received_at DESC);


-- Readings permissions

GRANT SELECT, INSERT
    ON TABLE telemetry.readings
    TO line30_app;


-- ============================================================
-- 3. OPERATIONAL EVENTS
-- Stores alarm activations, clearances and system events.
-- ============================================================

CREATE TABLE IF NOT EXISTS telemetry.events (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    line_id TEXT NOT NULL,

    event_type TEXT NOT NULL,
    event_code TEXT NOT NULL,
    severity TEXT NOT NULL,
    state TEXT NOT NULL,

    title TEXT NOT NULL,
    description TEXT,

    event_ts TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL
        DEFAULT clock_timestamp(),

    reading_id BIGINT
        REFERENCES telemetry.readings(id)
        ON DELETE SET NULL,

    replay_cycle_id UUID,

    details JSONB NOT NULL DEFAULT '{}'::JSONB,

    CONSTRAINT chk_events_type
        CHECK (event_type IN ('ALARM', 'SYSTEM')),

    CONSTRAINT chk_events_severity
        CHECK (severity IN ('INFO', 'WARNING', 'CRITICAL')),

    CONSTRAINT chk_events_state
        CHECK (state IN ('ACTIVE', 'CLEARED', 'INFO')),

    CONSTRAINT chk_events_details_object
        CHECK (jsonb_typeof(details) = 'object'),

    CONSTRAINT chk_events_line_id
        CHECK (length(trim(line_id)) > 0)
);


-- Events indexes

CREATE INDEX IF NOT EXISTS idx_events_line_recorded
    ON telemetry.events (line_id, recorded_at DESC, id DESC);

CREATE INDEX IF NOT EXISTS idx_events_line_event_ts
    ON telemetry.events (line_id, event_ts DESC);

CREATE INDEX IF NOT EXISTS idx_events_code_state
    ON telemetry.events (line_id, event_code, state);


-- ============================================================
-- 4. CURRENT ALARM STATE
-- Maintains the current state of each process alarm rule.
-- ============================================================

CREATE TABLE IF NOT EXISTS telemetry.alarm_state (
    line_id TEXT NOT NULL,
    rule_key TEXT NOT NULL,
    replay_cycle_id UUID NOT NULL,

    state TEXT NOT NULL DEFAULT 'NORMAL',
    severity TEXT,

    last_reading_id BIGINT
        REFERENCES telemetry.readings(id)
        ON DELETE SET NULL,

    last_event_ts TIMESTAMP WITHOUT TIME ZONE,

    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
        DEFAULT clock_timestamp(),

    CONSTRAINT pk_alarm_state
        PRIMARY KEY (line_id, rule_key, replay_cycle_id),

    CONSTRAINT chk_alarm_state_value
        CHECK (state IN ('NORMAL', 'ACTIVE')),

    CONSTRAINT chk_alarm_state_severity
        CHECK (
            severity IS NULL
            OR severity IN ('WARNING', 'CRITICAL')
        )
);


-- ============================================================
-- 5. SEQUENCE PERMISSIONS
-- ============================================================

GRANT USAGE, SELECT
    ON ALL SEQUENCES IN SCHEMA telemetry
    TO line30_app;


-- Default privileges for objects created by postgres

ALTER DEFAULT PRIVILEGES
    FOR ROLE postgres
    IN SCHEMA telemetry
    GRANT SELECT, INSERT ON TABLES TO line30_app;

ALTER DEFAULT PRIVILEGES
    FOR ROLE postgres
    IN SCHEMA telemetry
    GRANT USAGE, SELECT ON SEQUENCES TO line30_app;


-- ============================================================
-- 6. ALARM TABLE PERMISSIONS
-- ============================================================

GRANT SELECT, INSERT
    ON TABLE telemetry.events
    TO line30_app;

GRANT SELECT, INSERT, UPDATE
    ON TABLE telemetry.alarm_state
    TO line30_app;


-- ============================================================
-- 7. DATABASE DOCUMENTATION
-- ============================================================

COMMENT ON TABLE telemetry.readings IS
    'Stores complete Line Speed 30 telemetry snapshots received through MQTT.';

COMMENT ON COLUMN telemetry.readings.message_id IS
    'Stable identity of the original processed source record.';

COMMENT ON COLUMN telemetry.readings.replay_cycle_id IS
    'Identifies one replay cycle; combined with message_id for idempotency.';

COMMENT ON COLUMN telemetry.readings.event_ts IS
    'Original source event timestamp, retained without timezone conversion.';

COMMENT ON COLUMN telemetry.readings.received_at IS
    'Database timestamp when the telemetry record was inserted.';

COMMENT ON COLUMN telemetry.readings.payload IS
    'Complete incoming telemetry JSON message.';

COMMENT ON TABLE telemetry.events IS
    'Persistent alarm and operational event history for Line 30.';

COMMENT ON TABLE telemetry.alarm_state IS
    'Current state of each Line 30 process alarm rule.';


-- ============================================================
-- END OF SCHEMA
-- ============================================================

-- ============================================================
-- 8. ACTIVE ALARM EVENT IDENTIFICATION
-- Supports correct LOW/HIGH alarm clearance and transitions.
-- ============================================================

ALTER TABLE telemetry.alarm_state
    ADD COLUMN IF NOT EXISTS active_event_code TEXT;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'chk_alarm_state_event_code'
          AND conrelid = 'telemetry.alarm_state'::regclass
    ) THEN
        ALTER TABLE telemetry.alarm_state
            ADD CONSTRAINT chk_alarm_state_event_code
            CHECK (
                active_event_code IS NULL
                OR active_event_code IN (
                    'MOISTURE_LOW',
                    'MOISTURE_HIGH'
                )
            );
    END IF;
END
$$;

