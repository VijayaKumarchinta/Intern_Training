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