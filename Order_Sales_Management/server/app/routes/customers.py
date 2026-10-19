from flask import Blueprint, jsonify, request
from ..models import Customer
from ..extensions import db
from ..utils.decorators import auth_required, role_required
from ..constants import Role

customers_bp = Blueprint("customers", __name__, url_prefix="/api/customers")

@customers_bp.get("")
@role_required(Role.ADMIN.value)
def list_customers():
    customers = Customer.query.order_by(Customer.customer_id).all()
    return jsonify(customers=[c.to_dict() for c in customers]), 200

@customers_bp.post("")
@role_required(Role.ADMIN.value)
def create_customer():
    data = request.get_json() or {}
    customer_id = (data.get("customer_id") or "").strip().upper()
    cust_name = (data.get("cust_name") or "").strip()
    email = (data.get("email") or "").strip().lower() or None

    if not customer_id:
        return jsonify(error="customer_id is required"), 400
    if not cust_name:
        return jsonify(error="cust_name is required"), 400
    if Customer.query.get(customer_id):
        return jsonify(error="Customer ID already exists"), 409

    customer = Customer(customer_id=customer_id, cust_name=cust_name, email=email)
    db.session.add(customer)
    db.session.commit()
    return jsonify(customer=customer.to_dict()), 201


@customers_bp.patch("/<customer_id>/link")
@role_required(Role.ADMIN.value)
def link_customer_route(customer_id):
    data = request.get_json() or {}
    user_id = data.get("user_id")
    
    if not user_id:
        return jsonify(error="user_id is required"), 400
        
    cust = db.session.get(Customer, customer_id)
    if not cust:
        return jsonify(error="Customer not found"), 404
        
    from ..models import User
    user = db.session.get(User, user_id)
    if not user:
        return jsonify(error="User not found"), 404
        
    if cust.user_id is not None:
        return jsonify(error="Customer is already linked to a user"), 409
    
    cust.user_id = user.id
    if not cust.email:
        cust.email = user.email
    if not cust.cust_name:
        cust.cust_name = user.full_name
        
    db.session.commit()
    return jsonify(message="Customer linked successfully", customer=cust.to_dict()), 200