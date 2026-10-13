"""
Product API routes.
"""
import logging
from flask import Blueprint, request, jsonify

from ..services.product_service import ProductService
from ..db import ValidationError, ConflictError, NotFoundError

logger = logging.getLogger(__name__)
product_bp = Blueprint('products', __name__, url_prefix='/api/products')


@product_bp.route('', methods=['GET'])
def list_products():
    """Get all products with optional filtering."""
    try:
        limit = request.args.get('limit', 100)
        offset = request.args.get('offset', 0)
        category = request.args.get('category')
        search = request.args.get('search')

        products = ProductService.get_all_products(
            limit=limit,
            offset=offset,
            category=category,
            search=search
        )
        return jsonify({
            "status": "success",
            "data": {
                "products": products,
                "total": ProductService.count_products(),
                "limit": int(limit),
                "offset": int(offset)
            }
        }), 200
    except Exception as e:
        logger.exception("Failed to list products")
        return jsonify({"status": "error", "message": str(e)}), 500


@product_bp.route('/<product_id>', methods=['GET'])
def get_product(product_id):
    """Get a specific product by ID."""
    try:
        product = ProductService.get_product_by_id(product_id)
        return jsonify({
            "status": "success",
            "data": product
        }), 200
    except NotFoundError as e:
        return jsonify({"status": "error", "message": str(e)}), 404
    except Exception as e:
        logger.exception("Failed to get product")
        return jsonify({"status": "error", "message": str(e)}), 500


@product_bp.route('', methods=['POST'])
def create_product():
    """Create a new product."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Request body is required"}), 400

        # Validate required fields
        if 'product_id' not in data:
            return jsonify({"status": "error", "message": "product_id is required"}), 400
        if 'name' not in data:
            return jsonify({"status": "error", "message": "name is required"}), 400
        if 'unit_price' not in data:
            return jsonify({"status": "error", "message": "unit_price is required"}), 400

        product = ProductService.create_product(
            product_id=data['product_id'],
            name=data['name'],
            description=data.get('description'),
            category=data.get('category'),
            unit_price=data['unit_price'],
            stock_quantity=data.get('stock_quantity', 0)
        )

        return jsonify({
            "status": "success",
            "message": "Product created successfully",
            "data": product
        }), 201

    except ValidationError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except ConflictError as e:
        return jsonify({"status": "error", "message": str(e)}), 409
    except Exception as e:
        logger.exception("Failed to create product")
        return jsonify({"status": "error", "message": str(e)}), 500
