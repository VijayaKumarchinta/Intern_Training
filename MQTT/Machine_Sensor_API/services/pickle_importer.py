import csv
import hashlib
import pickle
from datetime import datetime, timezone
from pathlib import Path

import psycopg2.extras

from config import DATA_DIR, IMPORT_BATCH_SIZE
from database.connection import db
from utils.logger import logger

class PickleImporter:
    def __init__(self, batch_size=IMPORT_BATCH_SIZE):
        self.batch_size = batch_size
        self.machine_ids = {}

    def import_directory(self, directory):
        directory = Path(directory)

        if not directory.is_dir():
            raise ValueError(f"Directory does not exist: {directory}")
        totals = {
            "records_inserted": 0,
            "records_skipped": 0
        }
        for file_path in sorted(directory.glob("*.pkl")):
            result = self.import_file(file_path)

            totals["records_inserted"] += result["records_inserted"]
            totals["records_skipped"] += result["records_skipped"]
        logger.info(
            "Directory import completed: inserted=%s skipped=%s",
            totals["records_inserted"],
            totals["records_skipped"]
        )
        return totals

    def import_file(self, file_path):
        self.machine_ids = {}

        file_path = Path(file_path)
        if not file_path.is_file():
            raise ValueError(f"Pickle file does not exist: {file_path}")
        file_hash = self._get_file_hash(file_path)
        if self._is_already_imported(file_hash):
            raise ValueError(
                f"File already imported: {file_path.name}"
            )
        csv_path = self._convert_to_csv(file_path)
        result = self._import_csv(
            csv_path,
            file_path,
            file_hash
        )
        result["csv_file"] = csv_path.name
        logger.info(
            "Import completed: pickle=%s csv=%s inserted=%s skipped=%s",
            file_path.name,
            csv_path.name,
            result["records_inserted"],
            result["records_skipped"]
        )
        return result

    def _convert_to_csv(self, file_path):
        with open(file_path, "rb") as file:
            data = pickle.load(file)
        if not isinstance(data, dict):
            raise ValueError(
                "Pickle file must contain a dictionary"
            )
        csv_directory = DATA_DIR / "csv_files_28_03_2025"
        csv_directory.mkdir(parents=True, exist_ok=True)
        csv_path = csv_directory / f"{file_path.stem}.csv"
        temp_path = csv_path.with_suffix(".tmp")
        with open(
            temp_path,
            "w",
            newline="",
            encoding="utf-8"
        ) as file:
            writer = csv.writer(file)
            writer.writerow([
                "machine_name",
                "sensor_tag",
                "sensor_value",
                "timestamp"
            ])
            for machine_name, readings in data.items():
                if not isinstance(readings, list):
                    continue
                for reading in readings:
                    if not isinstance(reading, dict):
                        continue
                    sensor_tag = reading.get("ST")
                    timestamp = reading.get("TS")
                    values = reading.get("VR")
                    if (
                        not sensor_tag
                        or timestamp is None
                        or not values
                    ):
                        continue

                    try:
                        timestamp = datetime.fromtimestamp(
                            int(timestamp),
                            tz=timezone.utc
                        )
                    except (TypeError, ValueError, OverflowError):
                        continue

                    writer.writerow([
                        machine_name,
                        sensor_tag,
                        values[0],
                        timestamp.isoformat()
                    ])

        temp_path.replace(csv_path)

        logger.info(
            "CSV created: %s",
            csv_path
        )

        return csv_path

    def _import_csv(self, csv_path, file_path, file_hash):
        result = {
            "records_inserted": 0,
            "records_skipped": 0
        }

        with db.connection() as connection:
            cursor = connection.cursor()

            try:
                with open(
                    csv_path,
                    "r",
                    newline="",
                    encoding="utf-8"
                ) as file:

                    reader = csv.DictReader(file)

                    required_columns = {
                        "machine_name",
                        "sensor_tag",
                        "sensor_value",
                        "timestamp"
                    }

                    if not required_columns.issubset(
                        set(reader.fieldnames or [])
                    ):
                        raise ValueError(
                            "CSV is missing required columns"
                        )

                    batch = []

                    for row in reader:

                        machine_name = row.get("machine_name")
                        sensor_tag = row.get("sensor_tag")
                        sensor_value = row.get("sensor_value")
                        timestamp = row.get("timestamp")

                        if (
                            not machine_name
                            or not sensor_tag
                            or sensor_value in (None, "")
                            or not timestamp
                        ):
                            result["records_skipped"] += 1
                            continue

                        try:
                            sensor_value = float(sensor_value)
                            timestamp = datetime.fromisoformat(
                                timestamp
                            )

                            if timestamp.tzinfo is None:
                                timestamp = timestamp.replace(
                                    tzinfo=timezone.utc
                                )

                        except (
                            TypeError,
                            ValueError,
                            OverflowError
                        ):
                            result["records_skipped"] += 1
                            continue

                        if machine_name not in self.machine_ids:

                            cursor.execute(
                                f"""
                                SELECT id
                                FROM {db.schema}.machines
                                WHERE machine_name = %s
                                """,
                                (machine_name,)
                            )

                            machine = cursor.fetchone()

                            if machine is None:
                                cursor.execute(
                                    f"""
                                    INSERT INTO {db.schema}.machines (
                                        machine_name
                                    )
                                    VALUES (%s)
                                    ON CONFLICT (machine_name)
                                    DO UPDATE SET
                                        machine_name =
                                        EXCLUDED.machine_name
                                    RETURNING id
                                    """,
                                    (machine_name,)
                                )

                                machine = cursor.fetchone()

                            self.machine_ids[machine_name] = machine[0]

                        batch.append((
                            self.machine_ids[machine_name],
                            sensor_tag,
                            sensor_value,
                            timestamp
                        ))

                        if len(batch) >= self.batch_size:
                            self._insert_batch(
                                cursor,
                                batch
                            )

                            result["records_inserted"] += len(batch)
                            batch.clear()

                    if batch:
                        self._insert_batch(
                            cursor,
                            batch
                        )

                        result["records_inserted"] += len(batch)

                self._record_import(
                    cursor,
                    file_path,
                    file_hash,
                    result
                )

            finally:
                cursor.close()

        return result

    def _insert_batch(self, cursor, batch):
        psycopg2.extras.execute_values(
            cursor,
            f"""
            INSERT INTO {db.schema}.sensor_readings (
                machine_id,
                sensor_tag,
                sensor_value,
                timestamp
            )
            VALUES %s
            """,
            batch
        )

    def _record_import(
        self,
        cursor,
        file_path,
        file_hash,
        result
    ):
        try:
            cursor.execute(
                f"""
                INSERT INTO {db.schema}.import_batches (
                    file_name,
                    file_hash,
                    records_inserted,
                    records_skipped
                )
                VALUES (%s, %s, %s, %s)
                """,
                (
                    file_path.name,
                    file_hash,
                    result["records_inserted"],
                    result["records_skipped"]
                )
            )
        except psycopg2.errors.UniqueViolation:
            raise ValueError(
                f"File already imported: {file_path.name}"
            ) from None

    def _get_file_hash(self, file_path):
        sha256 = hashlib.sha256()

        with open(file_path, "rb") as file:
            for chunk in iter(
                lambda: file.read(65536),
                b""
            ):
                sha256.update(chunk)

        return sha256.hexdigest()

    def _is_already_imported(self, file_hash):
        with db.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT 1
                FROM {db.schema}.import_batches
                WHERE file_hash = %s
                """,
                (file_hash,)
            )

            return cursor.fetchone() is not None

pickle_importer = PickleImporter()