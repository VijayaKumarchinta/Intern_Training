"""
Report API routes - product-wise and date-wise sales reports.
"""
import logging
from flask import Blueprint, request, jsonify
from datetime import datetime, timezone

from ..services.order_service import OrderService
from ..utils.validation import validate_order_date

logger = logging.getLogger(__name__)
report_bp = Blueprint('reports', __name__, url_prefix='/api/reports')


@report_bp.route('/product-sales', methods=['GET'])
def product_sales_report():
    """
    Generate product-wise sales report.

    Query parameters:
        - from_date: Start date (ISO format, optional)
        - to_date: End date (ISO format, optional)
        - product_id: Filter by specific product (optional)

    Returns:
        List of products with sales metrics.
    """
    try:
        from_date_str = request.args.get('from_date')
        to_date_str = request.args.get('to_date')
        product_id = request.args.get('product_id')

        from_date = None
        to_date = None

        if from_date_str:
            from_date = validate_order_date(from_date_str)
        if to_date_str:
            to_date = validate_order_date(to_date_str)

        # If either date is provided, both should be (for a meaningful range)
        if (from_date or to_date) and not (from_date and to_date):
            # Auto-compute the missing end if only start is given
            if from_date and not to_date:
                to_date = datetime.now(timezone.utc)
            elif to_date and not from_date:
                from_date = datetime(to_date.year, 1, 1, tzinfo=timezone.utc)

        report = OrderService.get_product_sales_report(
            from_date=from_date,
            to_date=to_date,
            product_id=product_id
        )

        # Calculate summary
        total_revenue = sum(r['total_revenue'] for r in report)
        total_quantity = sum(r['total_quantity_sold'] for r in report)
        total_orders = sum(r['order_count'] for r in report)

        return jsonify({
            "status": "success",
            "data": {
                "report_type": "product-wise sales",
                "filters": {
                    "from_date": from_date.isoformat() if from_date else None,
                    "to_date": to_date.isoformat() if to_date else None,
                    "product_id": product_id
                },
                "summary": {
                    "total_revenue": round(total_revenue, 2),
                    "total_quantity_sold": total_quantity,
                    "total_orders": total_orders,
                    "product_count": len(report)
                },
                "products": report
            }
        }), 200

    except Exception as e:
        logger.exception("Failed to generate product sales report")
        return jsonify({"status": "error", "message": str(e)}), 500


@report_bp.route('/date-sales', methods=['GET'])
def date_sales_report():
    """
    Generate date-wise sales report.

    Query parameters:
        - from_date: Start date (ISO format, required)
        - to_date: End date (ISO format, required)

    Returns:
        Daily sales aggregates.
    """
    try:
        from_date_str = request.args.get('from_date')
        to_date_str = request.args.get('to_date')

        if not from_date_str or not to_date_str:
            return jsonify({
                "status": "error",
                "message": "Both from_date and to_date are required"
            }), 400

        from_date = validate_order_date(from_date_str)
        to_date = validate_order_date(to_date_str)

        if from_date > to_date:
            return jsonify({
                "status": "error",
                "message": "from_date must be before or equal to to_date"
            }), 400

        report = OrderService.get_date_sales_report(
            from_date=from_date,
            to_date=to_date
        )

        # Calculate summary
        total_revenue = sum(r['total_revenue'] for r in report)
        total_orders = sum(r['order_count'] for r in report)
        total_items = sum(r['item_count'] for r in report)
        total_discount = sum(r['total_discounts'] for r in report)
        total_tax = sum(r['total_tax'] for r in report)

        return jsonify({
            "status": "success",
            "data": {
                "report_type": "date-wise sales",
                "filters": {
                    "from_date": from_date.isoformat(),
                    "to_date": to_date.isoformat()
                },
                "summary": {
                    "period_days": (to_date - from_date).days + 1,
                    "total_revenue": round(total_revenue, 2),
                    "total_orders": total_orders,
                    "total_items_sold": total_items,
                    "total_discounts": round(total_discount, 2),
                    "total_tax": round(total_tax, 2),
                    "average_daily_revenue": round(total_revenue / max(1, (to_date - from_date).days + 1), 2)
                },
                "daily_sales": report
            }
        }), 200

    except Exception as e:
        logger.exception("Failed to generate date sales report")
        return jsonify({"status": "error", "message": str(e)}), 500


@report_bp.route('/summary', methods=['GET'])
def sales_summary():
    """
    Get overall sales summary (KPI dashboard).

    Query parameters:
        - from_date: Start date (optional)
        - to_date: End date (optional)

    Returns:
        Key metrics and counts.
    """
    try:
        from ..services.order_service import OrderService as OS
        from Order_Sales_Management.server.services.customer_service import CustomerService
        from Order_Sales_Management.server.services.product_service import ProductService

        from_date_str = request.args.get('from_date')
        to_date_str = request.args.get('to_date')

        from_date = None
        to_date = None

        if from_date_str:
            from_date = validate_order_date(from_date_str)
        if to_date_str:
            to_date = validate_order_date(to_date_str)

        # Get product sales for revenue metrics
        product_report = OS.get_product_sales_report(
            from_date=from_date,
            to_date=to_date
        )

        # Get date sales for order metrics
        if from_date and to_date:
            date_report = OS.get_date_sales_report(from_date, to_date)
        else:
            date_report = []

        # Build summary
        return jsonify({
            "status": "success",
            "data": {
                "summary": {
                    "total_customers": CustomerService.count_customers(),
                    "total_products": ProductService.count_products(),
                    "total_revenue": round(sum(r['total_revenue'] for r in product_report), 2),
                    "total_orders": sum(r['order_count'] for r in product_report),
                    "total_items_sold": sum(r['total_quantity_sold'] for r in product_report),
                    "total_discounts": round(sum(r['total_discounts'] for r in product_report), 2),
                    "top_product": max(product_report, key=lambda x: x['total_revenue']) if product_report else None,
                    "average_order_value": round(
                        sum(r['total_revenue'] for r in product_report) / max(1, sum(r['order_count'] for r in product_report)),
                        2
                    ) if product_report else 0
                }
            }
        }), 200

    except Exception as e:
        logger.exception("Failed to generate sales summary")
        return jsonify({"status": "error", "message": str(e)}), 500
