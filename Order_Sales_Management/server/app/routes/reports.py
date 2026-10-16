from flask import Blueprint, jsonify, request
from ..constants import Role
from ..services.order_service import date_wise_report, product_wise_report
from ..utils.decorators import role_required

reports_bp = Blueprint("reports", __name__, url_prefix="/api/reports")

@reports_bp.get("/product-wise")
@role_required(Role.ADMIN.value)
def product_wise():
    return jsonify(product_wise_report()), 200

@reports_bp.get("/date-wise")
@role_required(Role.ADMIN.value)
def date_wise():
    group = request.args.get("group", "day")
    if group not in ("day", "month"):
        return jsonify(error="group must be 'day' or 'month'"), 400
    return jsonify(date_wise_report(group)), 200