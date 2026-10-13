import logging
from flask import Blueprint, request, jsonify

from ..db import ConflictError, NotFoundError
from ..services.order_service import (
    create_order, get_order_by_id, get_all_orders, update_order_status,
    order_exists, validate_order_date,
)
from ..utils.validation import VALID_ORDER_STATUSES, validate_order_items

logger = logging.getLogger(__name__)
order_bp = Blueprint('orders', __name__, url_prefix='/api/orders')


@order_bp.route('', methods=['GET'])
def list_orders():
    try:
        limit = request.args.get('limit', 100)
        offset = request.args.get('offset', 0)
        status = request.args.get('status')
        customer_id = request.args.get('customer_id')
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')

        from_date_parsed = validate_order_date(from_date) if from_date else None
        to_date_parsed = validate_order_date(to_date) if to_date else None

        orders = get_all_orders(
            limit=limit, offset=offset, status=status,
            customer_id=customer_id, from_date=from_date_parsed, to_date=to_date_parsed,
        )
        return jsonify({"status": "success", "data": {"orders": orders}}), 200
    except Exception as e:
        logger.exception("Failed to list orders")
        return jsonify({"status": "error", "message": str(e)}), 500


@order_bp.route('/<order_id>', methods=['GET'])
def get_order(order_id):
    try:
        order = get_order_by_id(order_id)
        return jsonify({"status": "success", "data": order}), 200
    except Exception as e:
        logger.exception("Failed to get order")
        return jsonify({"status": "error", "message": str(e)}), 500


@order_bp.route('', methods=['POST'])
def create_order_route():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Request body is required"}), 400
        if 'customer_id' not in data:
            return jsonify({"status": "error", "message": "customer_id is required"}), 400

        items = data.get('items')
        if not items or not isinstance(items, list) or len(items) == 0:
            return jsonify({"status": "error", "message": "items must be a non-empty list"}), 400

        validated_items = validate_order_items(items)

        provided_id = data.get('order_id')
        if provided_id:
            if order_exists(provided_id):
                return jsonify({"status": "error", "message": f"Order '{provided_id}' already exists"}), 409

        order = create_order(
            customer_id=data['customer_id'],
            items=validated_items,
            order_id=data.get('order_id'),
            order_date=data.get('order_date'),
            shipping_address=data.get('shipping_address'),
            notes=data.get('notes'),
        )
        return jsonify({"status": "success", "message": "Order created", "data": order}), 201
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except ConflictError as e:
        return jsonify({"status": "error", "message": str(e)}), 409
    except Exception as e:
        logger.exception("Failed to create order")
        return jsonify({"status": "error", "message": str(e)}), 500


@order_bp.route('/<order_id>/status', methods=['PUT'])
def update_order_status_route(order_id):
    try:
        data = request.get_json()
        if not data or 'status' not in data:
            return jsonify({"status": "error", "message": "status is required"}), 400

        status = data['status'].strip().lower()
        if status not in VALID_ORDER_STATUSES:
            return jsonify({"status": "error", "message": f"Invalid status: {data['status']}"}), 400

        order = update_order_status(order_id, status)
        return jsonify({"status": "success", "message": f"Status updated to '{data['status']}'", "data": order}), 200
    except Exception as e:
        logger.exception("Failed to update order status")
        return jsonify({"status": "error", "message": str(e)}), 500
