from datetime import datetime, timezone

from database.connection import db, DatabaseError
from services.reading_service import utc_z


def _event(row):
    return {
        "reading_id": row[0],
        "machine_id": row[1],
        "machine_name": row[2],
        "sensor_tag": row[3],
        "sensor_value": float(row[4]),
        "timestamp": utc_z(row[5]),
    }


EVENT_SELECT = """
    r.id, r.machine_id, m.machine_name, r.sensor_tag, r.sensor_value, r.timestamp
"""


class DashboardService:
    def overview(self, stale_after_seconds):
        """One row per machine: last_seen, readings in the last minute, status."""
        try:
            with db.cursor(commit=False) as cursor:
                cursor.execute(
                    f"""
                    SELECT m.id, m.machine_name, l.last_seen,
                           COALESCE(c.n, 0), now()
                    FROM {db.schema}.machines m
                    LEFT JOIN LATERAL (
                        SELECT timestamp AS last_seen
                        FROM {db.schema}.sensor_readings
                        WHERE machine_id = m.id
                        ORDER BY timestamp DESC LIMIT 1
                    ) l ON true
                    LEFT JOIN LATERAL (
                        SELECT count(*) AS n
                        FROM {db.schema}.sensor_readings
                        WHERE machine_id = m.id
                          AND timestamp > now() - interval '1 minute'
                    ) c ON true
                    ORDER BY m.machine_name
                    """
                )
                rows = cursor.fetchall()
        except Exception as error:
            raise DatabaseError(f"Failed to load overview: {error}") from error

        server_time = rows[0][4] if rows else datetime.now(timezone.utc)
        machines = []
        for machine_id, name, last_seen, per_minute, now in rows:
            age = max(0.0, (now - last_seen).total_seconds()) if last_seen else None
            machines.append({
                "machine_id": machine_id,
                "machine_name": name,
                "last_seen": utc_z(last_seen) if last_seen else None,
                "age_seconds": round(age, 1) if age is not None else None,
                "readings_last_minute": per_minute,
                "status": "no_data" if age is None else ("stale" if age > stale_after_seconds else "ok"),
            })
        return {
            "server_time": utc_z(server_time),
            "stale_after_seconds": stale_after_seconds,
            "machines": machines,
        }

    def latest(self, machine_id=None):
        """Last value per machine + sensor_tag."""
        try:
            with db.cursor(commit=False) as cursor:
                where = "WHERE r.machine_id = %s" if machine_id else ""
                cursor.execute(
                    f"""
                    SELECT DISTINCT ON (r.machine_id, r.sensor_tag) {EVENT_SELECT}
                    FROM {db.schema}.sensor_readings r
                    JOIN {db.schema}.machines m ON m.id = r.machine_id
                    {where}
                    ORDER BY r.machine_id, r.sensor_tag, r.timestamp DESC, r.id DESC
                    """,
                    (machine_id,) if machine_id else None,
                )
                return [_event(r) for r in cursor.fetchall()]
        except Exception as error:
            raise DatabaseError(f"Failed to load latest readings: {error}") from error

    def series(self, machine_id, sensor_tag, minutes, limit=5000):
        """Recent history for one machine + tag, relative to that series' newest point."""
        try:
            with db.cursor(commit=False) as cursor:
                cursor.execute(
                    f"""
                    SELECT timestamp, sensor_value
                    FROM {db.schema}.sensor_readings
                    WHERE machine_id = %s AND sensor_tag = %s
                      AND timestamp >= (
                          SELECT max(timestamp) FROM {db.schema}.sensor_readings
                          WHERE machine_id = %s AND sensor_tag = %s
                      ) - make_interval(mins => %s)
                    ORDER BY timestamp
                    LIMIT %s
                    """,
                    (machine_id, sensor_tag, machine_id, sensor_tag, minutes, limit),
                )
                return [{"timestamp": utc_z(t), "sensor_value": float(v)} for t, v in cursor.fetchall()]
        except Exception as error:
            raise DatabaseError(f"Failed to load series: {error}") from error

    def max_reading_id(self):
        with db.cursor(commit=False) as cursor:
            cursor.execute(f"SELECT COALESCE(max(id), 0) FROM {db.schema}.sensor_readings")
            return cursor.fetchone()[0]

    def readings_after(self, last_id, limit):
        with db.cursor(commit=False) as cursor:
            cursor.execute(
                f"""
                SELECT {EVENT_SELECT}
                FROM {db.schema}.sensor_readings r
                JOIN {db.schema}.machines m ON m.id = r.machine_id
                WHERE r.id > %s
                ORDER BY r.id
                LIMIT %s
                """,
                (last_id, limit),
            )
            return [_event(r) for r in cursor.fetchall()]


dashboard_service = DashboardService()
