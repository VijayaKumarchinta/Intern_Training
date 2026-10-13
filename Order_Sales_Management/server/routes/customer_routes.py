"""
Customer API routes.
"""
import logging
from flask import Blueprint, request, jsonify

from ..services.customer_service import CustomerService
from ..db import ValidationError, ConflictError, NotFoundError

logger = logging.getLogger(__name__)
customer_bp = Blueprint('customers', __name__, url_prefix='/api/customers')


@customer_bp.route('', methods=['GET'])
def list_customers():
    """Get all customers with pagination."""
    try:
        limit = request.args.get('limit', 100)
        offset = request.args.get('offset', 0)
        customers = CustomerService.get_all_customers(limit=limit, offset=offset)
        return jsonify({
            "status": "success",
            "data": {
                "customers": customers,
                "total": CustomerService.count_customers(),
                "limit": int(limit),
                "offset": int(offset)
            }
        }), 200
    except Exception as e:
        logger.exception("Failed to list customers")
        return jsonify({"status": "error", "message": str(e)}), 500


@customer_bp.route('/<customer_id>', methods=['GET'])
def get_customer(customer_id):
    """Get a specific customer by ID."""
    try:
        customer = CustomerService.get_customer_by_id(customer_id)
        return jsonify({
            "status": "success",
            "data": customer
        }), 200
    except NotFoundError as e:
        return jsonify({"status": "error", "message": str(e)}), 404
    except Exception as e:
        logger.exception("Failed to get customer")
        return jsonify({"status": "error", "message": str(e)}), 500


@customer_bp.route('', methods=['POST'])
def create_customer():
    """Create a new customer."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Request body is required"}), 400

        # Validate required fields
        if 'customer_id' not in data:
            return jsonify({"status": "error", "message": "customer_id is required"}), 400
        if 'name' not in data:
            return jsonify({"status": "error", "message": "name is required"}), 400
        if 'email' not in data:
            return jsonify({"status": "error", "message": "email is required"}), 400

        customer = CustomerService.create_customer(
            customer_id=data['customer_id'],
            name=data['name'],
            email=data['email'],
            phone=data.get('phone'),
            address=data.get('address')
        )

        return jsonify({
            "status": "success",
            "message": "Customer created successfully",
            "data": customer
        }), 201

    except ValidationError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except ConflictError as e:
        return jsonify({"status": "error", "message": str(e)}), 409
    except Exception as e:
        logger.exception("Failed to create customer")
        return jsonify({"status": "error", "message": str(e)}), 500
