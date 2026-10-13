import logging
from flask import Blueprint, request, jsonify

from ..db import ConflictError
from ..services.product_service import (
    create_product, get_product_by_id, get_all_products, count_products,
)

logger = logging.getLogger(__name__)
product_bp = Blueprint('products', __name__, url_prefix='/api/products')


@product_bp.route('', methods=['GET'])
def list_products():
    try:
        products = get_all_products()
        return jsonify({"status": "success", "data": {"products": products, "total": count_products()}}), 200
    except Exception as e:
        logger.exception("Failed to list products")
        return jsonify({"status": "error", "message": str(e)}), 500


@product_bp.route('/<product_id>', methods=['GET'])
def get_product(product_id):
    try:
        product = get_product_by_id(product_id)
        return jsonify({"status": "success", "data": product}), 200
    except Exception as e:
        logger.exception("Failed to get product")
        return jsonify({"status": "error", "message": str(e)}), 500


@product_bp.route('', methods=['POST'])
def create_product_route():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Request body is required"}), 400
        if 'product_id' not in data:
            return jsonify({"status": "error", "message": "product_id is required"}), 400
        if 'name' not in data:
            return jsonify({"status": "error", "message": "name is required"}), 400
        if 'unit_price' not in data:
            return jsonify({"status": "error", "message": "unit_price is required"}), 400

        product = create_product(
            product_id=data['product_id'],
            name=data['name'],
            unit_price=data['unit_price'],
            description=data.get('description'),
            category=data.get('category'),
        )
        return jsonify({"status": "success", "message": "Product created", "data": product}), 201
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except ConflictError as e:
        return jsonify({"status": "error", "message": str(e)}), 409
    except Exception as e:
        logger.exception("Failed to create product")
        return jsonify({"status": "error", "message": str(e)}), 500
