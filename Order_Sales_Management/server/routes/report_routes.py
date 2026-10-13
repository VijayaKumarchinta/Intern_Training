import logging
from flask import Blueprint, request, jsonify

from ..db import get_connection, return_connection, qualified
from ..services.order_service import (
    get_product_sales_report, get_date_sales_report,
)
from ..utils.validation import validate_order_date

logger = logging.getLogger(__name__)
report_bp = Blueprint('reports', __name__, url_prefix='/api/reports')


@report_bp.route('/product-sales', methods=['GET'])
def product_sales_report():
    try:
        from_date_str = request.args.get('from_date')
        to_date_str = request.args.get('to_date')
        product_id = request.args.get('product_id')

        from_date = validate_order_date(from_date_str) if from_date_str else None
        to_date = validate_order_date(to_date_str) if to_date_str else None

        report = get_product_sales_report(from_date=from_date, to_date=to_date, product_id=product_id)
        total_revenue = round(sum(r['total_revenue'] for r in report), 2)
        total_quantity = sum(r['total_quantity_sold'] for r in report)
        total_orders = sum(r['order_count'] for r in report)

        return jsonify({
            "status": "success",
            "data": {
                "products": report,
                "summary": {
                    "total_revenue": total_revenue,
                    "total_quantity_sold": total_quantity,
                    "total_orders": total_orders,
                    "product_count": len(report),
                }
            }
        }), 200
    except Exception as e:
        logger.exception("Failed to generate product sales report")
        return jsonify({"status": "error", "message": str(e)}), 500


@report_bp.route('/date-sales', methods=['GET'])
def date_sales_report():
    try:
        from_date_str = request.args.get('from_date')
        to_date_str = request.args.get('to_date')

        if not from_date_str or not to_date_str:
            return jsonify({"status": "error", "message": "Both from_date and to_date are required"}), 400

        if not isinstance(from_date_str, str) or not from_date_str.strip():
            return jsonify({"status": "error", "message": "from_date must be a valid date string"}), 400
        if not isinstance(to_date_str, str) or not to_date_str.strip():
            return jsonify({"status": "error", "message": "to_date must be a valid date string"}), 400

        from_date = validate_order_date(from_date_str)
        to_date = validate_order_date(to_date_str)
        if not from_date or not to_date:
            return jsonify({"status": "error", "message": "from_date and to_date must be valid dates (format: YYYY-MM-DD)"}), 400

        report = get_date_sales_report(from_date, to_date)
        total_revenue = round(sum(r['total_revenue'] for r in report), 2)
        total_orders = sum(r['order_count'] for r in report)
        period_days = max(1, len(report))

        return jsonify({
            "status": "success",
            "data": {
                "daily_sales": report,
                "summary": {
                    "total_revenue": total_revenue,
                    "total_orders": total_orders,
                    "period_days": period_days,
                    "average_daily_revenue": round(total_revenue / period_days, 2) if period_days > 0 else 0,
                }
            }
        }), 200
    except Exception as e:
        logger.exception("Failed to generate date sales report")
        return jsonify({"status": "error", "message": str(e)}), 500
