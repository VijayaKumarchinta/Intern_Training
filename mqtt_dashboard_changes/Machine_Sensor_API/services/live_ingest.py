"""Turns one MQTT-style message into validated rows in sensor_readings.

Message shape (same as the pickle): topic = machine name, payload =
{"ID": "1", "ST": "41984", "TS": 1743143035, "VR": [200]}  (or a list of them).
"""
import json
from datetime import datetime, timezone

from database.connection import db, DatabaseError
from utils.logger import logger


class LiveIngest:
    def __init__(self):
        self._machine_ids = {}

    def _machine_id(self, cursor, machine_name):
        machine_id = self._machine_ids.get(machine_name)
        if machine_id is None:
            cursor.execute(
                f"""
                INSERT INTO {db.schema}.machines (machine_name)
                VALUES (%s)
                ON CONFLICT (machine_name)
                DO UPDATE SET machine_name = EXCLUDED.machine_name
                RETURNING id
                """,
                (machine_name,),
            )
            machine_id = cursor.fetchone()[0]
            self._machine_ids[machine_name] = machine_id
        return machine_id

    @staticmethod
    def parse(payload):
        """Return (rows, rejected). rows = [(sensor_tag, value, datetime)]."""
        try:
            data = json.loads(payload)
        except (TypeError, ValueError):
            return [], 1
        items = data if isinstance(data, list) else [data]
        rows, rejected = [], 0
        for item in items:
            try:
                tag = str(item["ST"]).strip()
                values = item["VR"]
                value = float(values[0] if isinstance(values, list) else values)
                ts = datetime.fromtimestamp(int(item["TS"]), tz=timezone.utc)
                if not tag:
                    raise ValueError
                rows.append((tag, value, ts))
            except (KeyError, IndexError, TypeError, ValueError, OverflowError, OSError):
                rejected += 1
        return rows, rejected

    def ingest(self, machine_name, payload):
        """Returns (inserted, rejected). Never raises on bad payloads."""
        machine_name = (machine_name or "").strip()
        rows, rejected = self.parse(payload)
        if not machine_name:
            return 0, rejected + len(rows)
        if not rows:
            if rejected:
                logger.warning("Live ingest rejected: machine=%s rejected=%s", machine_name, rejected)
            return 0, rejected
        try:
            with db.cursor() as cursor:
                machine_id = self._machine_id(cursor, machine_name)
                cursor.executemany(
                    f"""
                    INSERT INTO {db.schema}.sensor_readings
                    (machine_id, sensor_tag, sensor_value, timestamp)
                    VALUES (%s, %s, %s, %s)
                    """,
                    [(machine_id, tag, value, ts) for tag, value, ts in rows],
                )
        except Exception as error:
            self._machine_ids.pop(machine_name, None)
            raise DatabaseError(f"Live ingest failed: {error}") from error
        return len(rows), rejected


live_ingest = LiveIngest()
