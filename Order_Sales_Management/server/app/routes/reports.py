"""
reports.py - HTTP endpoints for sales reports (gross vs net).
"""

import logging

from flask import Blueprint, jsonify, request

from app import services
from app import config as app_config

logger = logging.getLogger(__name__)

reports_bp = Blueprint("reports", __name__)


def _report():
    try:
        if request.path.endswith("/by-product"):
            return jsonify({"data": services.sales_by_product(conn)}), 200
        # /api/reports/sales/by-date
        start = request.args.get("start_date")
        end = request.args.get("end_date")
        try:
            page = int(request.args.get("page", 1))
            page_size = int(request.args.get("page_size", 50))
        except ValueError:
            return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "page and page_size must be integers."}}), 400
        return jsonify({"data": services.sales_by_date(conn, start, end)}), 200
    finally:
        conn.close()


reports_bp.add_url_rule("/reports/sales/by-product", "by_product", _report, methods=["GET"])
reports_bp.add_url_rule("/reports/sales/by-date", "by_date", _report, methods=["GET"])
