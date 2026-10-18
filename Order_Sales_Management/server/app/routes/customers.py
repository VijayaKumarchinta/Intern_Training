from flask import Blueprint, jsonify
from ..models import Customer
from ..utils.decorators import auth_required

customers_bp = Blueprint("customers", __name__, url_prefix="/api/customers")

@customers_bp.get("")
@auth_required
def list_customers():
    customers = Customer.query.order_by(Customer.customer_id).all()
    return jsonify(customers=[c.to_dict() for c in customers]), 200