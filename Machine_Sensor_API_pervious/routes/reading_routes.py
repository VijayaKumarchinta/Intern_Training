import csv
import io
from datetime import datetime

from flask import Response, jsonify, request
from flask.views import MethodView

from config import DEFAULT_PAGE_SIZE
from errors import ValidationError
from services.reading_service import reading_service, utc_z

class ReadingView(MethodView):

    def get(self, reading_id=None):
        if reading_id is not None:
            reading = reading_service.get_reading(reading_id)

            if not reading:
                return jsonify({"error": "Reading not found"}), 404

            return jsonify(reading), 200

        machine_id = self._get_machine_id_query_param()
        sensor_tag = request.args.get("sensor_tag")
        from_time = self._timestamp_from_query("from")
        to_time = self._timestamp_from_query("to")
        limit, offset = self._pagination_from_query()

        if (
            from_time is not None
            and to_time is not None
            and from_time > to_time
        ):
            raise ValidationError(
                "'from' timestamp cannot be later than 'to' timestamp"
            )

        readings = reading_service.get_readings(
            machine_id=machine_id,
            sensor_tag=sensor_tag,
            from_time=from_time,
            to_time=to_time,
            limit=limit,
            offset=offset,
        )

        return jsonify(readings), 200

    def post(self):
        data = request.get_json(silent=True)

        if not data:
            raise ValidationError("Request body is required")

        required_fields = [
            "machine_id",
            "sensor_tag",
            "sensor_value",
            "timestamp",
        ]

        missing = [field for field in required_fields if field not in data]
        if missing:
            raise ValidationError(
                ", ".join(missing) + " is required"
            )

        machine_id = self._validate_machine_id(data["machine_id"])
        sensor_tag = self._validate_sensor_tag(data["sensor_tag"])

        try:
            sensor_value = float(data["sensor_value"])
        except (TypeError, ValueError):
            raise ValidationError("sensor_value must be numeric") from None

        timestamp = self._validate_timestamp(data["timestamp"])

        reading = reading_service.add_reading(
            machine_id=machine_id,
            sensor_tag=sensor_tag,
            sensor_value=sensor_value,
            timestamp=timestamp,
        )

        return jsonify(reading), 201

    def put(self, reading_id):
        data = request.get_json(silent=True)

        if not data:
            raise ValidationError("Request body is required")

        allowed_fields = {
            "machine_id",
            "sensor_tag",
            "sensor_value",
            "timestamp",
        }

        if not any(field in data for field in allowed_fields):
            raise ValidationError(
                "At least one valid field is required for update"
            )

        machine_id = None
        sensor_tag = None
        sensor_value = None
        timestamp = None

        if "machine_id" in data:
            machine_id = self._validate_machine_id(data["machine_id"])

        if "sensor_tag" in data:
            sensor_tag = self._validate_sensor_tag(data["sensor_tag"])

        if "sensor_value" in data:
            try:
                sensor_value = float(data["sensor_value"])
            except (TypeError, ValueError):
                raise ValidationError(
                    "sensor_value must be numeric"
                ) from None

        if "timestamp" in data:
            timestamp = self._validate_timestamp(data["timestamp"])

        reading = reading_service.update_reading(
            reading_id=reading_id,
            machine_id=machine_id,
            sensor_tag=sensor_tag,
            sensor_value=sensor_value,
            timestamp=timestamp,
        )

        if not reading:
            return jsonify({
                "error": "Reading not found or no fields to update"
            }), 404

        return jsonify(reading), 200

    def delete(self, reading_id):
        deleted = reading_service.delete_reading(reading_id)

        if not deleted:
            return jsonify({"error": "Reading not found"}), 404

        return jsonify({"message": "Reading deleted successfully"}), 200

    @staticmethod
    def _validate_machine_id(value):
        try:
            machine_id = int(value)

            if machine_id <= 0:
                raise ValueError

            return machine_id

        except (TypeError, ValueError):
            raise ValidationError(
                "machine_id must be a positive integer"
            ) from None

    @staticmethod
    def _validate_sensor_tag(value):
        if not isinstance(value, str) or not value.strip():
            raise ValidationError("sensor_tag must be a non-empty string")

        return value.strip()

    @staticmethod
    def _validate_timestamp(value):
        if not isinstance(value, str) or not value.strip():
            raise ValidationError("timestamp must be a non-empty string")

        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            raise ValidationError(
                "timestamp must be a valid ISO 8601 timestamp"
            ) from None

    @classmethod
    def _timestamp_from_query(cls, name):
        value = request.args.get(name)

        if value is None:
            return None

        return cls._validate_timestamp(value)

    @classmethod
    def _get_machine_id_query_param(cls):
        value = request.args.get("machine_id")

        if value is None:
            return None

        return cls._validate_machine_id(value)

    @staticmethod
    def _pagination_from_query():
        try:
            limit = int(request.args.get("limit", DEFAULT_PAGE_SIZE))
            offset = int(request.args.get("offset", 0))
        except ValueError:
            raise ValidationError(
                "limit and offset must be integers"
            ) from None

        if limit < 1:
            raise ValidationError("limit must be >= 1")

        if offset < 0:
            raise ValidationError("offset must be >= 0")

        return min(limit, DEFAULT_PAGE_SIZE), offset

class ReadingExportView(MethodView):
    def get(self):
        machine_id = ReadingView._get_machine_id_query_param()
        sensor_tag = request.args.get("sensor_tag")
        from_time = ReadingView._timestamp_from_query("from")
        to_time = ReadingView._timestamp_from_query("to")

        if (
            from_time is not None
            and to_time is not None
            and from_time > to_time
        ):
            raise ValidationError(
                "'from' timestamp cannot be later than 'to' timestamp"
            )

        def generate():
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(
                ["reading_id", "machine_id", "sensor_tag", "sensor_value", "timestamp"]
            )
            yield output.getvalue()

            for row in reading_service.iter_all_readings(
                machine_id=machine_id,
                sensor_tag=sensor_tag,
                from_time=from_time,
                to_time=to_time,
            ):
                output.seek(0)
                output.truncate()
                writer.writerow(
                    [
                        row[0],
                        row[1],
                        row[2],
                        float(row[3]),
                        utc_z(row[4]),
                    ]
                )
                yield output.getvalue()

        return Response(
            generate(),
            mimetype="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=readings_export.csv"
            },
        )

class ReadingStatisticsView(MethodView):
    def get(self):
        machine_id = ReadingView._get_machine_id_query_param()
        sensor_tag = request.args.get("sensor_tag")
        from_time = ReadingView._timestamp_from_query("from")
        to_time = ReadingView._timestamp_from_query("to")

        if (
            from_time is not None
            and to_time is not None
            and from_time > to_time
        ):
            raise ValidationError(
                "'from' timestamp cannot be later than 'to' timestamp"
            )

        statistics = reading_service.get_statistics(
            machine_id=machine_id,
            sensor_tag=sensor_tag,
            from_time=from_time,
            to_time=to_time,
        )
        return jsonify(statistics), 200