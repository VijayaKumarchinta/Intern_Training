from flask import jsonify, request
from flask.views import MethodView

from errors import ValidationError
from services.machine_service import machine_service

class MachineView(MethodView):
    def get(self, machine_id=None):
        if machine_id is not None:
            machine = machine_service.get_machine(machine_id)

            if not machine:
                return jsonify({"error": "Machine not found"}), 404

            return jsonify(machine), 200

        machines = machine_service.get_all_machines()
        return jsonify(machines), 200

    def post(self):
        data = request.get_json(silent=True)

        if not data:
            raise ValidationError("Request body is required")

        machine_name = data.get("machine_name")

        if (
            not machine_name
            or not isinstance(machine_name, str)
            or not machine_name.strip()
        ):
            raise ValidationError("machine_name is required")

        machine = machine_service.add_machine(machine_name.strip())
        return jsonify(machine), 201

    def put(self, machine_id):
        data = request.get_json(silent=True)

        if not data:
            raise ValidationError("Request body is required")

        machine_name = data.get("machine_name")
        if (
            not machine_name
            or not isinstance(machine_name, str)
            or not machine_name.strip()
        ):
            raise ValidationError("machine_name is required")

        machine = machine_service.update_machine(machine_id, machine_name.strip())

        if not machine:
            return jsonify({"error": "Machine not found"}), 404

        return jsonify(machine), 200

    def delete(self, machine_id):
        deleted = machine_service.delete_machine(machine_id)

        if not deleted:
            return jsonify({"error": "Machine not found"}), 404

        return jsonify({"message": "Machine deleted successfully"}), 200
