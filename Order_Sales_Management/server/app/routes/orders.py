from flask import Blueprint, jsonify, request

from flask import Blueprint, jsonify, request

from ..utils.decorators import get_current_user, role_required
from ..models import Customer, Order, OrderItem, Product
from ..services.order_service import (
    change_status,
    date_wise_report,
    find_duplicates,
    product_wise_report,
    validate_order_payload,
    visible_orders_for,
)

orders_bp = Blueprint("orders", __name__, url_prefix="/api/orders")


def _json():
    return request.get_json(silent=True) or {}


def _build_order_response(order, include_items=False):
    data = order.to_dict(include_items=include_items)
    if include_items:
        data["total"] = float(
            sum(i.quantity * i.unit_price for i in order.items) if order.items else 0
        )
    return data


@orders_bp.get("")
def list_orders():
    user = get_current_user()
    if user is None:
        return jsonify(error="User not found"), 404

    q = visible_orders_for(user)

    status = request.args.get("status")
    if status:
        q = q.filter(Order.order_status == status)

    customer_id = request.args.get("customer_id")
    if customer_id:
        q = q.filter(Order.customer_id == customer_id)

    q = q.order_by(Order.order_date.desc(), Order.order_id.desc())

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    per_page = min(max(per_page, 1), 200)

    return jsonify(
        orders=[_build_order_response(o) for o in paginated.items],
        page=paginated.page,
        per_page=paginated.per_page,
        total=paginated.total,
        pages=paginated.pages,
    ), 200


@orders_bp.get("/<order_id>")
def get_order(order_id):
    user = get_current_user()
    if user is None:
        return jsonify(error="User not found"), 404

    order = Order.query.filter_by(order_id=order_id).first()
    if order is None:
        return jsonify(error="Order not found"), 404

    if user.role != "admin":
        customer = order.customer
        if customer is None or customer.user_id != user.id:
            return jsonify(error="Order not found"), 404

    return jsonify(_build_order_response(order, include_items=True)), 200


@orders_bp.post("")
@role_required("admin")
def create_order():
    payload = _json()
    errors = validate_order_payload(payload)
    if errors:
        return jsonify(errors=errors), 400

    customer = Customer.query.filter_by(
        customer_id=payload.get("customer_id")
    ).first()
    if customer is None:
        return jsonify(error="Customer not found"), 404

    try:
        order = Order(
            order_id=payload["order_id"],
            customer_id=customer.customer_id,
            order_date=payload.get("order_date"),
            order_status=payload.get("order_status", "Pending"),
        )
        db.session.add(order)
        db.session.flush()

        for item in payload.get("items", []):
            product = Product.query.filter_by(
                product_id=item.get("product_id")
            ).first()
            if product is None:
                db.session.rollback()
                return jsonify(errors=[f"Product {item.get('product_id')} not found"]), 400
            line = OrderItem(
                order_id=order.order_id,
                product_id=product.product_id,
                quantity=item.get("quantity"),
                unit_price=item.get("unit_price"),
            )
            db.session.add(line)

        db.session.commit()
        return jsonify(_build_order_response(order, include_items=True)), 201
    except Exception:  
        db.session.rollback()
        return jsonify(error="Failed to create order"), 400


@orders_bp.post("/validate")
@role_required("admin")
def dry_run_validation():
    payload = _json()
    errors = validate_order_payload(payload)
    return jsonify(valid=len(errors) == 0, errors=errors), 200


@orders_bp.patch("/<order_id>/status")
@role_required("admin")
def update_status(order_id):
    payload = _json()
    new_status = payload.get("order_status")
    if not new_status:
        return jsonify(error="order_status is required"), 400

    order = Order.query.filter_by(order_id=order_id).first()
    if order is None:
        return jsonify(error="Order not found"), 404

    ok, msg = change_status(order, new_status)
    if not ok:
        return jsonify(error=msg), 400

    return jsonify(_build_order_response(order)), 200


@orders_bp.get("/duplicates")
@role_required("admin")
def list_duplicates():
    return jsonify(duplicates=find_duplicates()), 200
