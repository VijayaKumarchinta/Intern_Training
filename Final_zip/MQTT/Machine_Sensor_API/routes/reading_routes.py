import csv
import io

from flask import Response, jsonify, request
from flask.views import MethodView

from errors import ValidationError
from services.reading_service import reading_service, utc_z
from utils.validation import (
    machine_id_from_query,
    pagination_from_query,
    timestamp_from_query,
    validate_from_to_order,
    validate_machine_id,
    validate_sensor_tag,
    validate_timestamp,
)

class ReadingView(MethodView):

    def get(self, reading_id=None):
        if reading_id is not None:
            reading = reading_service.get_reading(reading_id)

            if not reading:
                return jsonify({"error": "Reading not found"}), 404

            return jsonify(reading), 200

        from_time = timestamp_from_query("from")
        to_time = timestamp_from_query("to")
        validate_from_to_order(from_time, to_time)
        limit, offset = pagination_from_query()

        readings = reading_service.get_readings(
            machine_id=machine_id_from_query(),
            sensor_tag=request.args.get("sensor_tag"),
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

        machine_id = validate_machine_id(data["machine_id"])
        sensor_tag = validate_sensor_tag(data["sensor_tag"])

        try:
            sensor_value = float(data["sensor_value"])
        except (TypeError, ValueError):
            raise ValidationError("sensor_value must be numeric") from None

        timestamp = validate_timestamp(data["timestamp"])

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
            machine_id = validate_machine_id(data["machine_id"])

        if "sensor_tag" in data:
            sensor_tag = validate_sensor_tag(data["sensor_tag"])

        if "sensor_value" in data:
            try:
                sensor_value = float(data["sensor_value"])
            except (TypeError, ValueError):
                raise ValidationError(
                    "sensor_value must be numeric"
                ) from None

        if "timestamp" in data:
            timestamp = validate_timestamp(data["timestamp"])

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

class ReadingExportView(MethodView):
    def get(self):
        from_time = timestamp_from_query("from")
        to_time = timestamp_from_query("to")
        validate_from_to_order(from_time, to_time)

        def generate():
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(
                ["reading_id", "machine_id", "sensor_tag", "sensor_value", "timestamp"]
            )
            yield output.getvalue()

            for row in reading_service.iter_all_readings(
                machine_id=machine_id_from_query(),
                sensor_tag=request.args.get("sensor_tag"),
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
        from_time = timestamp_from_query("from")
        to_time = timestamp_from_query("to")
        validate_from_to_order(from_time, to_time)

        statistics = reading_service.get_statistics(
            machine_id=machine_id_from_query(),
            sensor_tag=request.args.get("sensor_tag"),
            from_time=from_time,
            to_time=to_time,
        )
        return jsonify(statistics), 200
