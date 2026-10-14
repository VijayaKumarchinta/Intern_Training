from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from werkzeug.exceptions import BadRequest, Forbidden, NotFound

from app import models
from app.services.order_service import (
    validate_order as validate_payload,
    change_status,
    find_duplicates,
    get_order_by_id,
    line_total,
    product_wise_report,
    date_wise_report,
    summary_report,
    visible_orders_for,
)
from app.utils.decorators import role_required, current_user
from app.extensions import db

orders_bp = Blueprint("orders", __name__)


def _parse_row(body: dict) -> dict:
    return {
        "order_id": body.get("order_id"),
        "order_date": body.get("order_date"),
        "customer_id": body.get("customer_id"),
        "product": body.get("product"),
        "quantity": body.get("quantity"),
        "unit_price": body.get("unit_price"),
        "order_status": body.get("order_status"),
    }


@orders_bp.route("", methods=["GET"])
@jwt_required()
def list_orders():
    user = current_user()
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    status = request.args.get("status")
    product = request.args.get("product")
    from_date = request.args.get("from_date")
    to_date = request.args.get("to_date")

    query = visible_orders_for(user).filter(models.Order.is_valid.is_(True))

    if status:
        query = query.filter(models.Order.order_status == status)
    if product:
        query = query.filter(models.Order.product == product)
    if from_date:
        query = query.filter(models.Order.order_date >= _parse_date(from_date))
    if to_date:
        query = query.filter(models.Order.order_date <= _parse_date(to_date))

    pagination = query.order_by(models.Order.order_id).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "items": [_order_json(o) for o in pagination.items],
        "total": pagination.total,
        "page": page,
        "per_page": per_page,
        "pages": pagination.pages,
    })


@orders_bp.route("/<order_id>", methods=["GET"])
@jwt_required()
def get_order(order_id):
    user = current_user()
    order = get_order_by_id(order_id, user)
    if order is None:
        raise NotFound("order not found")
    return jsonify(_order_json(order))


@orders_bp.route("", methods=["POST"])
@jwt_required()
@role_required("admin")
def create_order():
    body = request.get_json(silent=True) or {}
    row = _parse_row(body)
    errors = validate_payload(row)
    if errors:
        raise BadRequest(", ".join(errors))

    if db.session.execute(db.select(models.Order).where(models.Order.order_id == row["order_id"])).scalar_one_or_none():
        raise BadRequest("order_id already exists")

    order = models.Order(
        order_id=row["order_id"],
        order_date=_parse_date(row["order_date"]) or None,
        customer_id=row["customer_id"],
        product=row["product"],
        quantity=row["quantity"],
        unit_price=row["unit_price"],
        order_status=row.get("order_status") or "Pending",
    )
    db.session.add(order)
    db.session.commit()
    return jsonify(_order_json(order)), 201


@orders_bp.route("/<order_id>", methods=["PUT"])
@jwt_required()
@role_required("admin")
def update_order(order_id):
    order = get_order_by_id(order_id)
    if order is None:
        raise NotFound("order not found")

    body = request.get_json(silent=True) or {}
    row = _parse_row(body)

    if row["order_id"] and row["order_id"] != order_id:
        raise BadRequest("order_id cannot be changed")

    errors = validate_payload(row)
    if errors:
        raise BadRequest(", ".join(errors))

    order.order_date = _parse_date(row["order_date"]) or order.order_date
    order.customer_id = row["customer_id"] or order.customer_id
    order.product = row["product"] or order.product
    order.quantity = row["quantity"] if row["quantity"] is not None else order.quantity
    order.unit_price = row["unit_price"] if row["unit_price"] is not None else order.unit_price
    order.order_status = row["order_status"] or order.order_status
    order.updated_at = _now()
    db.session.commit()
    return jsonify(_order_json(order))


@orders_bp.route("/<order_id>/status", methods=["PATCH"])
@jwt_required()
@role_required("admin")
def patch_status(order_id):
    order = get_order_by_id(order_id)
    if order is None:
        raise NotFound("order not found")
    body = request.get_json(silent=True) or {}
    new_status = (body.get("order_status") or "").strip()
    if not new_status:
        raise BadRequest("order_status is required")
    try:
        change_status(order, new_status)
    except ValueError as exc:
        raise BadRequest(str(exc))
    db.session.commit()
    return jsonify(_order_json(order))


@orders_bp.route("/<order_id>", methods=["DELETE"])
@jwt_required()
@role_required("admin")
def delete_order(order_id):
    order = get_order_by_id(order_id)
    if order is None:
        raise NotFound("order not found")
    db.session.delete(order)
    db.session.commit()
    return "", 204


@orders_bp.route("/duplicates", methods=["GET"])
@jwt_required()
@role_required("admin")
def duplicates():
    return jsonify({"duplicates": find_duplicates()})


@orders_bp.route("/validate", methods=["POST"])
@jwt_required()
@role_required("admin")
def validate_dry_run():
    body = request.get_json(silent=True) or {}
    row = _parse_row(body)
    errors = validate_payload(row)
    return jsonify({"valid": not errors, "errors": errors})


@orders_bp.route("/reports", methods=["GET"])
@jwt_required()
@role_required("admin")
def reports():
    return jsonify({
        "product_wise": product_wise_report(_filters()),
        "date_wise": date_wise_report(_filters(), group=(request.args.get("group") or "day")),
        "summary": summary_report(_filters()),
    })


def _parse_date(value):
    from datetime import date, datetime
    if isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
            try:
                return datetime.strptime(value.strip(), fmt).date()
            except ValueError:
                continue
    return None


def _now():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc)


def _filters():
    return {
        "status": request.args.get("status"),
        "product": request.args.get("product"),
        "from_date": request.args.get("from_date"),
        "to_date": request.args.get("to_date"),
    }


def _order_json(order: models.Order) -> dict:
    from decimal import Decimal
    quantity = order.quantity
    unit_price = order.unit_price
    if isinstance(quantity, Decimal):
        quantity = float(quantity)
    if isinstance(unit_price, Decimal):
        unit_price = float(unit_price)
    return {
        "order_id": order.order_id,
        "order_date": order.order_date.isoformat() if order.order_date else None,
        "customer_id": order.customer_id,
        "product": order.product,
        "quantity": quantity,
        "unit_price": unit_price,
        "order_status": order.order_status,
        "is_valid": bool(order.is_valid),
        "validation_errors": order.validation_errors,
        "line_total": float(line_total(order.quantity, order.unit_price)),
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "updated_at": order.updated_at.isoformat() if order.updated_at else None,
    }
