from flask import Blueprint, jsonify
from ..models import Product
from ..utils.decorators import auth_required

products_bp = Blueprint("products", __name__, url_prefix="/api/products")

@products_bp.get("")
@auth_required
def list_products():
    products = Product.query.order_by(Product.pro_name).all()
    return jsonify(products=[p.to_dict() for p in products]), 200