"""
orders.py - HTTP endpoints for orders.

Request flow:  route -> validator -> service -> repository (SQL).
"""

import logging

from flask import Blueprint, jsonify, request

from app import config as app_config
from app import services

logger = logging.getLogger(__name__)

orders_bp = Blueprint("orders", __name__)


def _admin_token():
    return request.headers.get("Authorization", "")


def _create_order():
    payload = request.get_json(silent=True)
    idempotency_key = request.headers.get("Idempotency-Key", "").strip()

    if not idempotency_key:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "Idempotency-Key header is required."}}), 400

    try:
        order, created, error = services.order_service.create_order(app_config.config.connect(), payload, idempotency_key)
        if error == "DUPLICATE_SUSPECTED":
            return jsonify({"error": {"code": "DUPLICATE_SUSPECTED", "message": "Looks like a repeat order. Add allow_duplicate: true to proceed."}}), 409
        if error == "IDEMPOTENCY_KEY_REUSED":
            return jsonify({"error": {"code": "IDEMPOTENCY_KEY_REUSED", "message": "This key was reused with different data."}}), 409
        if error:
            return jsonify({"error": {"code": "VALIDATION_ERROR", "message": error[0] if isinstance(error, list) else error}}), 400
        if created:
            return (
                jsonify({
                    "data": {
                        "order_id": order["order_id"],
                        "status": order["status"],
                        "total": str(order["unit_price"] * order["quantity"]),
                    }
                }),
                201,
            )
        # Retry: already existed.
        return (
            jsonify({
                "data": {
                    "order_id": order["order_id"],
                    "status": order["status"],
                    "total": str(order["unit_price"] * order["quantity"]),
                }
            }),
            200,
        )
    finally:
        conn = app_config.config.connect()
        if hasattr(conn, "close"):
            conn.close()


def _list_orders():
    try:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 50))
    except ValueError:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "page and page_size must be integers."}}), 400

    try:
        orders = services.order_service.list_orders(
            app_config.config.connect(),
            status=request.args.get("status"),
            customer_id=request.args.get("customer_id"),
            start_date=request.args.get("start_date"),
            end_date=request.args.get("end_date"),
            page=page,
            page_size=page_size,
        )
        return jsonify({"data": orders}), 200
    finally:
        conn = app_config.config.connect()
        if hasattr(conn, "close"):
            conn.close()


def _get_order():
    order_id = request.view_args["order_id"]
    try:
        order = services.order_service.get_order(app_config.config.connect(), order_id)
        if order is None:
            return jsonify({"error": {"code": "NOT_FOUND", "message": "Order not found."}}), 404
        return (
            jsonify({
                "data": {
                    "order_id": order["order_id"],
                    "customer_id": order["customer_id"],
                    "product": order["product"],
                    "quantity": order["quantity"],
                    "unit_price": order["unit_price"],
                    "order_date": order["order_date"],
                    "status": order["status"],
                    "total": str(order["unit_price"] * order["quantity"]),
                }
            }),
            200,
        )
    finally:
        conn = app_config.config.connect()
        if hasattr(conn, "close"):
            conn.close()


def _edit_order():
    order_id = request.view_args["order_id"]
    try:
        payload = request.get_json(silent=True)
        updated, error = services.order_service.edit_order(app_config.config.connect(), order_id, payload, _admin_token())
        if error == "UNAUTHORIZED":
            return jsonify({"error": {"code": "UNAUTHORIZED", "message": "Admin token required."}}), 401
        if error == "FORBIDDEN":
            return jsonify({"error": {"code": "FORBIDDEN", "message": "Admin token required."}}), 403
        if error == "ORDER_NOT_EDITABLE":
            return jsonify({"error": {"code": "ORDER_NOT_EDITABLE", "message": "Only Pending orders can be edited."}}), 409
        if error == "NOT_FOUND":
            return jsonify({"error": {"code": "NOT_FOUND", "message": "Order not found."}}), 404
        if error:
            return jsonify({"error": {"code": "VALIDATION_ERROR", "message": error[0] if isinstance(error, list) else error}}), 400
        return (
            jsonify({
                "data": {
                    "order_id": updated["order_id"],
                    "status": updated["status"],
                    "total": str(updated["unit_price"] * updated["quantity"]),
                }
            }),
            200,
        )
    finally:
        conn = app_config.config.connect()
        if hasattr(conn, "close"):
            conn.close()


def _change_status():
    order_id = request.view_args["order_id"]
    payload = request.get_json(silent=True)
    new_status = (payload or {}).get("status")

    if not new_status:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "status field is required."}}), 400

    try:
        updated, error = services.order_service.change_status(app_config.config.connect(), order_id, new_status, _admin_token())
        if error == "UNAUTHORIZED":
            return jsonify({"error": {"code": "UNAUTHORIZED", "message": "Admin token required."}}), 401
        if error == "FORBIDDEN":
            return jsonify({"error": {"code": "FORBIDDEN", "message": "Admin token required."}}), 403
        if error == "INVALID_STATUS_TRANSITION":
            return jsonify({"error": {"code": "INVALID_STATUS_TRANSITION", "message": f"Cannot transition from {updated['status'] if updated else 'unknown'} to {new_status}."}}), 409
        if error == "NOT_FOUND":
            return jsonify({"error": {"code": "NOT_FOUND", "message": "Order not found."}}), 404
        if error:
            return jsonify({"error": {"code": "VALIDATION_ERROR", "message": error[0] if isinstance(error, list) else error}}), 400
        return (
            jsonify({
                "data": {
                    "order_id": updated["order_id"],
                    "status": updated["status"],
                    "total": str(updated["unit_price"] * updated["quantity"]),
                }
            }),
            200,
        )
    finally:
        conn = app_config.config.connect()
        if hasattr(conn, "close"):
            conn.close()


orders_bp.add_url_rule("/orders", "create", _create_order, methods=["POST"])
orders_bp.add_url_rule("/orders", "list", _list_orders, methods=["GET"])
orders_bp.add_url_rule("/orders/<order_id>", "get", _get_order, methods=["GET"])
orders_bp.add_url_rule("/orders/<order_id>", "edit", _edit_order, methods=["PATCH"])
orders_bp.add_url_rule("/orders/<order_id>/status", "status", _change_status, methods=["PATCH"])
