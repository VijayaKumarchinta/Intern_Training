"""
report_service - business rules for sales reports (gross vs net).

Reports are grouped either by product or by date.
"""

import logging

from app import repositories

logger = logging.getLogger(__name__)


def sales_by_product(conn):
    return repositories._product_rows(conn)


def sales_by_date(conn, start_date=None, end_date=None):
    return repositories._date_rows(conn, start_date, end_date)
