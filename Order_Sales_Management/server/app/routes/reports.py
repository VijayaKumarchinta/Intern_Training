from flask import Blueprint, jsonify, request

from ..decorators import role_required
from ..services.order_service import date_wise_report, product_wise_report

bp = Blueprint("reports", __name__, url_prefix="/api/reports")


@bp.route("/product-wise", methods=["GET"])
@role_required("admin")
def product_wise():
    rows = product_wise_report()
    return jsonify(rows=rows), 200


@bp.route("/date-wise", methods=["GET"])
@role_required("admin")
def date_wise():
    group = request.args.get("group", "day")
    if group not in ("day", "month"):
        return jsonify(error="group must be 'day' or 'month'"), 400
    rows = date_wise_report(group=group)
    return jsonify(rows=rows), 200
