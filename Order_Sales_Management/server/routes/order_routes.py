"""
Order API routes.
"""
import logging
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify

from ..services.order_service import OrderService
from ..db import ValidationError, ConflictError, NotFoundError

logger = logging.getLogger(__name__)
order_bp = Blueprint('orders', __name__, url_prefix='/api/orders')


@order_bp.route('', methods=['GET'])
def list_orders():
    """Get all orders with optional filtering."""
    try:
        limit = request.args.get('limit', 100)
        offset = request.args.get('offset', 0)
        status = request.args.get('status')
        customer_id = request.args.get('customer_id')

        # Date range filtering
        from_date_str = request.args.get('from_date')
        to_date_str = request.args.get('to_date')

        from_date = None
        to_date = None

        if from_date_str:
            try:
                from_date = datetime.fromisoformat(from_date_str.replace('Z', '+00:00'))
                if from_date.tzinfo is None:
                    from_date = from_date.replace(tzinfo=timezone.utc)
            except ValueError:
                return jsonify({"status": "error", "message": "Invalid from_date format"}), 400

        if to_date_str:
            try:
                to_date = datetime.fromisoformat(to_date_str.replace('Z', '+00:00'))
                if to_date.tzinfo is None:
                    to_date = to_date.replace(tzinfo=timezone.utc)
            except ValueError:
                return jsonify({"status": "error", "message": "Invalid to_date format"}), 400

        orders = OrderService.get_all_orders(
            limit=limit,
            offset=offset,
            status=status,
            customer_id=customer_id,
            from_date=from_date,
            to_date=to_date
        )

        return jsonify({
            "status": "success",
            "data": {
                "orders": orders,
                "limit": int(limit),
                "offset": int(offset)
            }
        }), 200

    except Exception as e:
        logger.exception("Failed to list orders")
        return jsonify({"status": "error", "message": str(e)}), 500


@order_bp.route('/<order_id>', methods=['GET'])
def get_order(order_id):
    """Get a specific order by ID."""
    try:
        order = OrderService.get_order_by_id(order_id)
        return jsonify({
            "status": "success",
            "data": order
        }), 200
    except NotFoundError as e:
        return jsonify({"status": "error", "message": str(e)}), 404
    except Exception as e:
        logger.exception("Failed to get order")
        return jsonify({"status": "error", "message": str(e)}), 500


@order_bp.route('', methods=['POST'])
def create_order():
    """Create a new order."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Request body is required"}), 400

        # Validate required fields
        if 'customer_id' not in data:
            return jsonify({"status": "error", "message": "customer_id is required"}), 400
        if 'items' not in data:
            return jsonify({"status": "error", "message": "items is required"}), 400

        order = OrderService.create_order(
            customer_id=data['customer_id'],
            items=data['items'],
            order_id=data.get('order_id'),
            order_date=data.get('order_date'),
            shipping_address=data.get('shipping_address'),
            notes=data.get('notes'),
            discount_percent=data.get('discount_percent')
        )

        return jsonify({
            "status": "success",
            "message": "Order created successfully",
            "data": order
        }), 201

    except ValidationError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except ConflictError as e:
        return jsonify({"status": "error", "message": str(e)}), 409
    except NotFoundError as e:
        return jsonify({"status": "error", "message": str(e)}), 404
    except Exception as e:
        logger.exception("Failed to create order")
        return jsonify({"status": "error", "message": str(e)}), 500


@order_bp.route('/<order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    """Update order status."""
    try:
        data = request.get_json()
        if not data or 'status' not in data:
            return jsonify({"status": "error", "message": "status is required"}), 400

        new_status = data['status']
        order = OrderService.update_order_status(order_id, new_status)

        return jsonify({
            "status": "success",
            "message": f"Order status updated to '{new_status}'",
            "data": order
        }), 200

    except ValidationError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except NotFoundError as e:
        return jsonify({"status": "error", "message": str(e)}), 404
    except Exception as e:
        logger.exception("Failed to update order status")
        return jsonify({"status": "error", "message": str(e)}), 500


@order_bp.route('/check-duplicate', methods=['POST'])
def check_duplicate():
    """Check if an order would be a duplicate."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Request body is required"}), 400

        if 'customer_id' not in data:
            return jsonify({"status": "error", "message": "customer_id is required"}), 400
        if 'items' not in data:
            return jsonify({"status": "error", "message": "items is required"}), 400

        # Calculate subtotal for comparison
        from Order_Sales_Management.server.services.order_service import OrderService as OS
        from decimal import Decimal
        items = data['items']
        subtotal = Decimal('0')
        for item in items:
            price = Decimal(str(item.get('unit_price', 0)))
            qty = int(item.get('quantity', 0))
            subtotal += price * qty

        result = OrderService.check_duplicate_order(data['customer_id'], items, subtotal)

        status_msg = "Potential duplicate detected" if result['is_duplicate'] else "Order is unique"

        return jsonify({
            "status": "success",
            "data": {
                "is_duplicate": result['is_duplicate'],
                "message": status_msg,
                "signature": result['signature']
            }
        }), 200

    except Exception as e:
        logger.exception("Failed to check duplicate")
        return jsonify({"status": "error", "message": str(e)}), 500
