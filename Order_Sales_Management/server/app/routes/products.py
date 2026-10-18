from flask import Blueprint, jsonify, request
from ..models import Product
from ..extensions import db
from ..utils.decorators import auth_required, role_required
from ..constants import Role

products_bp = Blueprint("products", __name__, url_prefix="/api/products")

@products_bp.get("")
@auth_required
def list_products():
    products = Product.query.order_by(Product.pro_name).all()
    return jsonify(products=[p.to_dict() for p in products]), 200

@products_bp.post("")
@role_required(Role.ADMIN.value)
def create_product():
    data = request.get_json() or {}
    name = (data.get("pro_name") or "").strip()
    price = data.get("current_price")

    if not name:
        return jsonify(error="pro_name is required"), 400
    if price is None or float(price) < 0:
        return jsonify(error="current_price must be >= 0"), 400
    if Product.query.filter_by(pro_name=name).first():
        return jsonify(error="Product name already exists"), 409

    product = Product(pro_name=name, current_price=price)
    db.session.add(product)
    db.session.commit()
    return jsonify(product=product.to_dict()), 201

@products_bp.patch("/<int:product_id>")
@role_required(Role.ADMIN.value)
def update_product_price(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        return jsonify(error="Product not found"), 404
        
    new_price = request.get_json().get("current_price")
    if new_price is None or float(new_price) < 0:
        return jsonify(error="Invalid price"), 400
        
    product.current_price = new_price
    db.session.commit()
    return jsonify(message="Price updated", product=product.to_dict()), 200

@products_bp.delete("/<int:product_id>")
@role_required(Role.ADMIN.value)
def delete_product(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        return jsonify(error="Product not found"), 404
    
    if product.order_items:
        return jsonify(error="Cannot delete product: it is used in orders. Archive it instead."), 409
    
    db.session.delete(product)
    db.session.commit()
    return jsonify(message="Product deleted"), 200