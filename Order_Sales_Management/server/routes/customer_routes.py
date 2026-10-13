import logging
from flask import Blueprint, request, jsonify

from ..db import ConflictError
from ..services.customer_service import (
    create_customer, get_customer_by_id, get_all_customers, count_customers,
)

logger = logging.getLogger(__name__)
customer_bp = Blueprint('customers', __name__, url_prefix='/api/customers')


@customer_bp.route('', methods=['GET'])
def list_customers():
    try:
        customers = get_all_customers()
        return jsonify({"status": "success", "data": {"customers": customers, "total": count_customers()}}), 200
    except Exception as e:
        logger.exception("Failed to list customers")
        return jsonify({"status": "error", "message": str(e)}), 500


@customer_bp.route('/<customer_id>', methods=['GET'])
def get_customer(customer_id):
    try:
        customer = get_customer_by_id(customer_id)
        return jsonify({"status": "success", "data": customer}), 200
    except Exception as e:
        logger.exception("Failed to get customer")
        return jsonify({"status": "error", "message": str(e)}), 500


@customer_bp.route('', methods=['POST'])
def create_customer_route():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Request body is required"}), 400
        if 'customer_id' not in data:
            return jsonify({"status": "error", "message": "customer_id is required"}), 400
        if 'name' not in data:
            return jsonify({"status": "error", "message": "name is required"}), 400
        if 'email' not in data:
            return jsonify({"status": "error", "message": "email is required"}), 400

        customer = create_customer(
            customer_id=data['customer_id'],
            name=data['name'],
            email=data['email'],
            phone=data.get('phone'),
            address=data.get('address'),
        )
        return jsonify({"status": "success", "message": "Customer created", "data": customer}), 201
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except ConflictError as e:
        return jsonify({"status": "error", "message": str(e)}), 409
    except Exception as e:
        logger.exception("Failed to create customer")
        return jsonify({"status": "error", "message": str(e)}), 500
