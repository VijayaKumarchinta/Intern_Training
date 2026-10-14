from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from app.utils.decorators import role_required

from app.services.order_service import product_wise_report, date_wise_report, summary_report


reports_bp = Blueprint("reports", __name__)


@reports_bp.route("/product-wise", methods=["GET"])
@jwt_required()
@role_required("admin")
def product_wise():
    return jsonify({"reports": product_wise_report(_filters())})


@reports_bp.route("/date-wise", methods=["GET"])
@jwt_required()
@role_required("admin")
def date_wise():
    return jsonify({
        "reports": date_wise_report(_filters(), group=(request.args.get("group") or "day")),
    })


@reports_bp.route("/summary", methods=["GET"])
@jwt_required()
@role_required("admin")
def summary():
    return jsonify({"summary": summary_report(_filters())})


def _filters():
    return {
        "status": request.args.get("status"),
        "product": request.args.get("product"),
        "from_date": request.args.get("from_date"),
        "to_date": request.args.get("to_date"),
    }
