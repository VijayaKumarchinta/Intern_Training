from contextlib import closing
from datetime import timezone

import psycopg2

from utils.logger import logger

from database.connection import (
    db,
    DatabaseError,
    RelatedResourceNotFoundError,
)

READING_SELECT = "id, machine_id, sensor_tag, sensor_value, timestamp"

def utc_z(value):
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

class ReadingService:
    def add_reading(self, machine_id, sensor_tag, sensor_value, timestamp):
        try:
            with db.cursor() as cursor:
                cursor.execute(
                    f"""
                    INSERT INTO {db.schema}.sensor_readings
                    (machine_id, sensor_tag, sensor_value, timestamp)
                    VALUES (%s, %s, %s, %s)
                    RETURNING {READING_SELECT}
                    """,
                    (machine_id, sensor_tag, sensor_value, timestamp),
                )
                row = cursor.fetchone()

            reading = self._format_reading(row)
            logger.info("Reading created: reading_id=%s machine_id=%s sensor_tag=%s", reading["reading_id"], machine_id, sensor_tag)
            return reading

        except psycopg2.errors.ForeignKeyViolation:
            logger.warning("Reading rejected: machine_id=%s does not exist", machine_id)
            raise RelatedResourceNotFoundError(
                f"Machine with id {machine_id} does not exist."
            ) from None

        except Exception as error:
            raise DatabaseError(f"Failed to add reading: {error}") from error

    def get_reading(self, reading_id):
        try:
            with db.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT {READING_SELECT}
                    FROM {db.schema}.sensor_readings
                    WHERE id = %s
                    """,
                    (reading_id,),
                )
                row = cursor.fetchone()

            if not row:
                logger.warning("Reading not found: reading_id=%s", reading_id)
                return None

            reading = self._format_reading(row)
            logger.info("Reading retrieved: reading_id=%s", reading_id)
            return reading

        except Exception as error:
            raise DatabaseError(f"Failed to retrieve reading: {error}") from error

    def get_readings(
        self,
        machine_id=None,
        sensor_tag=None,
        from_time=None,
        to_time=None,
        limit=100,
        offset=0,
    ):
        try:
            query, values = self._build_reading_filters(
                f"""
                SELECT {READING_SELECT}
                FROM {db.schema}.sensor_readings
                """,
                machine_id=machine_id,
                sensor_tag=sensor_tag,
                from_time=from_time,
                to_time=to_time,
            )
            query += " ORDER BY timestamp, id LIMIT %s OFFSET %s"
            values.extend([limit, offset])

            with db.cursor() as cursor:
                cursor.execute(query, values)
                rows = cursor.fetchall()

            readings = [self._format_reading(row) for row in rows]
            logger.info(
                "Readings retrieved: count=%s machine_id=%s sensor_tag=%s from=%s to=%s limit=%s offset=%s",
                len(readings), machine_id, sensor_tag, from_time, to_time, limit, offset
            )
            return readings

        except Exception as error:
            raise DatabaseError(f"Failed to retrieve readings: {error}") from error

    def iter_all_readings(
        self,
        machine_id=None,
        sensor_tag=None,
        from_time=None,
        to_time=None,
        chunk_size=1000,
    ):
        try:
            query, values = self._build_reading_filters(
                f"""
                SELECT {READING_SELECT}
                FROM {db.schema}.sensor_readings
                """,
                machine_id=machine_id,
                sensor_tag=sensor_tag,
                from_time=from_time,
                to_time=to_time,
            )
            query += " ORDER BY timestamp, id"

            with db.connection(commit=False) as connection:
                with closing(connection.cursor(name="readings_export_cursor")) as cursor:
                    cursor.itersize = chunk_size
                    cursor.execute(query, values)

                    for row in cursor:
                        yield row

        except Exception as error:
            raise DatabaseError(f"Failed to stream readings: {error}") from error

    def update_reading(
        self,
        reading_id,
        machine_id=None,
        sensor_tag=None,
        sensor_value=None,
        timestamp=None,
    ):
        try:
            fields = []
            values = []

            if machine_id is not None:
                fields.append("machine_id = %s")
                values.append(machine_id)

            if sensor_tag is not None:
                fields.append("sensor_tag = %s")
                values.append(sensor_tag)

            if sensor_value is not None:
                fields.append("sensor_value = %s")
                values.append(sensor_value)

            if timestamp is not None:
                fields.append("timestamp = %s")
                values.append(timestamp)

            if not fields:
                return None

            values.append(reading_id)

            query = f"""
                    UPDATE {db.schema}.sensor_readings
                    SET {", ".join(fields)}
                    WHERE id = %s
                    RETURNING {READING_SELECT}
                    """

            with db.cursor() as cursor:
                cursor.execute(query, values)
                row = cursor.fetchone()

            if not row:
                logger.warning("Reading update failed: reading_id=%s not found", reading_id)
                return None

            reading = self._format_reading(row)
            logger.info("Reading updated: reading_id=%s", reading_id)
            return reading

        except psycopg2.errors.ForeignKeyViolation:
            logger.warning(
                "Reading update rejected: reading_id=%s machine_id=%s does not exist",
                reading_id, machine_id
            )
            raise RelatedResourceNotFoundError(
                f"Machine with id {machine_id} does not exist."
            ) from None

        except Exception as error:
            raise DatabaseError(f"Failed to update reading: {error}") from error

    def delete_reading(self, reading_id):
        try:
            with db.cursor() as cursor:
                cursor.execute(
                    f"""
                    DELETE FROM {db.schema}.sensor_readings
                    WHERE id = %s
                    """,
                    (reading_id,),
                )
                deleted = cursor.rowcount > 0

            if deleted:
                logger.info("Reading deleted: reading_id=%s", reading_id)
            return deleted

        except Exception as error:
            logger.exception("Failed to delete reading: reading_id=%s", reading_id)
            raise DatabaseError(f"Failed to delete reading: {error}") from error

    def get_statistics(
        self,
        machine_id=None,
        sensor_tag=None,
        from_time=None,
        to_time=None,
    ):
        try:
            query, values = self._build_reading_filters(
                f"""
                SELECT MIN(sensor_value), MAX(sensor_value), AVG(sensor_value)
                FROM {db.schema}.sensor_readings
                """,
                machine_id=machine_id,
                sensor_tag=sensor_tag,
                from_time=from_time,
                to_time=to_time,
            )

            with db.cursor() as cursor:
                cursor.execute(query, values)
                row = cursor.fetchone()

            statistics = {
                "minimum": float(row[0]) if row[0] is not None else None,
                "maximum": float(row[1]) if row[1] is not None else None,
                "average": float(row[2]) if row[2] is not None else None,
            }
            logger.info(
                "Reading statistics calculated: machine_id=%s sensor_tag=%s from=%s to=%s",
                machine_id, sensor_tag, from_time, to_time
            )
            return statistics

        except Exception as error:
            raise DatabaseError(f"Failed to calculate statistics: {error}") from error

    def _build_reading_filters(
        self,
        base_query,
        machine_id=None,
        sensor_tag=None,
        from_time=None,
        to_time=None,
    ):
        """Return (query, values) with the standard reading filters appended.

        Single source of truth for reading filtering — used by get_readings,
        iter_all_readings and get_statistics (previously built inline in three places).
        """
        conditions = []
        values = []
        query = base_query

        if machine_id is not None:
            conditions.append("machine_id = %s")
            values.append(machine_id)

        if sensor_tag is not None:
            conditions.append("sensor_tag = %s")
            values.append(sensor_tag)

        if from_time is not None:
            conditions.append("timestamp >= %s")
            values.append(from_time)

        if to_time is not None:
            conditions.append("timestamp <= %s")
            values.append(to_time)

        if conditions:
            query = base_query + " WHERE " + " AND ".join(conditions)

        return query, values

    def _format_reading(self, row):
        return {
            "reading_id": row[0],
            "machine_id": row[1],
            "sensor_tag": row[2],
            "sensor_value": float(row[3]),
            "timestamp": utc_z(row[4]),
        }

reading_service = ReadingService()
