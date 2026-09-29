from config import DB_SCHEMA

CREATE_SCHEMA_SQL = f"""
CREATE SCHEMA IF NOT EXISTS {DB_SCHEMA};
"""
CREATE_MACHINES_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS {DB_SCHEMA}.machines (
    id SERIAL PRIMARY KEY,

    machine_name VARCHAR(100) UNIQUE NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""
CREATE_SENSOR_READINGS_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS {DB_SCHEMA}.sensor_readings (
    id BIGSERIAL PRIMARY KEY,

    machine_id INTEGER NOT NULL
        REFERENCES {DB_SCHEMA}.machines(id)
        ON DELETE CASCADE,

    sensor_tag VARCHAR(50) NOT NULL,

    sensor_value NUMERIC NOT NULL,

    timestamp TIMESTAMPTZ NOT NULL
);
"""
CREATE_MACHINE_TIMESTAMP_INDEX_SQL = f"""
CREATE INDEX IF NOT EXISTS
idx_sensor_readings_machine_timestamp
ON {DB_SCHEMA}.sensor_readings
(machine_id, timestamp);
"""
CREATE_SENSOR_TAG_INDEX_SQL = f"""
CREATE INDEX IF NOT EXISTS
idx_sensor_readings_sensor_tag
ON {DB_SCHEMA}.sensor_readings
(sensor_tag);
"""
CREATE_TIMESTAMP_INDEX_SQL = f"""
CREATE INDEX IF NOT EXISTS
idx_sensor_readings_timestamp
ON {DB_SCHEMA}.sensor_readings
(timestamp);
"""
CREATE_IMPORT_BATCHES_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS {DB_SCHEMA}.import_batches (
    id SERIAL PRIMARY KEY,

    file_name VARCHAR(255) NOT NULL,

    file_hash CHAR(64) NOT NULL UNIQUE,

    records_inserted INTEGER NOT NULL DEFAULT 0,

    records_skipped INTEGER NOT NULL DEFAULT 0,

    imported_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""
