import logging
from flask import Blueprint, g, jsonify, request
from sqlalchemy.exc import IntegrityError
from ..constants import Role
from ..models import Order
from ..services.order_service import (
    change_status,
    create_order,
    find_duplicates,
    validate_order_payload,
    visible_orders_for,
)
from ..utils.decorators import auth_required, role_required

log = logging.getLogger(__name__)

orders_bp = Blueprint("orders", __name__, url_prefix="/api/orders")

def _json():
    return request.get_json(silent=True) or {}

def _order_response(order, include_items=False):
    data = order.to_dict(include_items=include_items)
    if include_items:
        data["total"] = float(
            sum(i.quantity * i.unit_price for i in order.items) if order.items else 0
        )
    return data

@orders_bp.get("/duplicates")
@role_required(Role.ADMIN.value)
def list_duplicates():
    return jsonify(duplicates=find_duplicates()), 200

@orders_bp.get("")
@auth_required
def list_orders():
    user = g.current_user
    q = visible_orders_for(user)

    status = request.args.get("status")
    if status:
        q = q.filter(Order.order_status == status)

    customer_id = request.args.get("customer_id")
    if customer_id:
        if user.role != Role.ADMIN.value and (
            user.customer is None or user.customer.customer_id != customer_id
        ):
            return jsonify(error="Forbidden"), 403
        q = q.filter(Order.customer_id == customer_id)

    q = q.order_by(Order.order_date.desc(), Order.order_id.desc())

    page = max(request.args.get("page", 1, type=int), 1)
    per_page = min(max(request.args.get("per_page", 50, type=int), 1), 200)

    paginated = q.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify(
        orders=[_order_response(o) for o in paginated.items],
        page=paginated.page,
        per_page=paginated.per_page,
        total=paginated.total,
        pages=paginated.pages,
    ), 200

@orders_bp.get("/<order_id>")
@auth_required
def get_order(order_id):
    user = g.current_user
    order = Order.query.filter_by(order_id=order_id).first()
    if order is None:
        return jsonify(error="Order not found"), 404

    if user.role != Role.ADMIN.value:
        customer = order.customer
        if customer is None or customer.user_id != user.id:
            return jsonify(error="Order not found"), 404

    return jsonify(_order_response(order, include_items=True)), 200

@orders_bp.post("")
@role_required(Role.ADMIN.value)
def create_order():
    payload = _json()
    try:
        order, err, status = create_order(payload)
    except IntegrityError:
        return jsonify(error="Order already exists"), 409
    except Exception:
        log.exception("create_order failed")
        return jsonify(error="Failed to create order"), 400

    if err:
        if isinstance(err, list):
            return jsonify(errors=err), status
        return jsonify(error=err), status

    return jsonify(_order_response(order, include_items=True)), status

@orders_bp.post("/validate")
@role_required(Role.ADMIN.value)
def dry_run_validation():
    payload = _json()
    errors = validate_order_payload(payload)
    return jsonify(valid=len(errors) == 0, errors=errors), 200

@orders_bp.patch("/<order_id>/status")
@role_required(Role.ADMIN.value)
def update_status(order_id):
    new_status = _json().get("order_status")
    if not new_status:
        return jsonify(error="order_status is required"), 400

    order = Order.query.filter_by(order_id=order_id).first()
    if order is None:
        return jsonify(error="Order not found"), 404

    ok, msg = change_status(order, new_status)
    if not ok:
        return jsonify(error=msg), 400

    return jsonify(_order_response(order)), 200