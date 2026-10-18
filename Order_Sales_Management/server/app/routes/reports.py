import csv
import io
from flask import Blueprint, jsonify, request, Response
from ..constants import Role
from ..services.order_service import (
    product_wise_report,
    date_wise_report,
    get_dashboard_summary,
)
from ..utils.decorators import role_required

reports_bp = Blueprint("reports", __name__, url_prefix="/api/reports")


@reports_bp.get("/summary")
@role_required(Role.ADMIN.value)
def dashboard_summary():
    return jsonify(get_dashboard_summary()), 200


@reports_bp.get("/product-wise")
@role_required(Role.ADMIN.value)
def product_wise():
    data = product_wise_report()
    if request.args.get("format") == "csv":
        return _generate_product_csv(data)
    return jsonify(data), 200

@reports_bp.get("/date-wise")
@role_required(Role.ADMIN.value)
def date_wise():
    group = request.args.get("group", "day")
    if group not in ("day", "month"):
        return jsonify(error="group must be 'day' or 'month'"), 400
    data = date_wise_report(group)
    if request.args.get("format") == "csv":
        return _generate_date_csv(data, group)
    return jsonify(data), 200

def _generate_product_csv(data):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Product", "Items Sold", "Units Sold", "Revenue (INR)"])
    for row in data:
        writer.writerow([row["product"], row["items"], row["units"], f"{row['revenue']:.2f}"])
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=product_wise_report.csv"},
    )

def _generate_date_csv(data, group):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([f"Period ({group})", "Orders", "Units Sold", "Revenue (INR)"])
    for row in data:
        writer.writerow([row["period"][:10], row["orders"], row["units"], f"{row['revenue']:.2f}"])
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=date_wise_report_{group}.csv"},
    )