"""
report_repository - sales aggregation SQL (gross vs net).

Reports are grouped either by product or by date.
"""

import logging

from psycopg2 import sql

from app import config as app_config

logger = logging.getLogger(__name__)


def _get_schema():
    return app_config.config.DB_SCHEMA


def _connect(conn_or_dsn):
    """Accept an existing connection or a DSN string, return a connection."""
    if hasattr(conn_or_dsn, "cursor"):
        return conn_or_dsn
    return app_config.config.connect()


def _close(conn):
    """Close a connection we opened ourselves; ignore connections we did not open."""
    if conn is not None and not hasattr(conn, "_owned_by_repo"):
        try:
            conn.close()
        except Exception:
            pass


def _product_report():
    schema = _get_schema()
    query = sql.SQL(
        "SELECT "
        " product AS order_date, "
        " COUNT(*) AS order_count, "
        " COUNT(*) FILTER (WHERE status NOT IN ('Cancelled','Returned')) AS net_order_count, "
        " SUM(quantity) AS quantity_sold, "
        " SUM(unit_price * quantity) AS gross_sales, "
        " SUM(unit_price * quantity) FILTER (WHERE status NOT IN ('Cancelled','Returned')) AS net_sales "
        "FROM {schema}.orders "
        "GROUP BY product "
        "ORDER BY net_sales DESC, product"
    ).format(schema=sql.Identifier(schema))
    return query


def _date_report(start_date=None, end_date=None):
    schema = _get_schema()
    base = (
        "SELECT "
        " order_date, "
        " COUNT(*) AS order_count, "
        " COUNT(*) FILTER (WHERE status NOT IN ('Cancelled','Returned')) AS net_order_count, "
        " SUM(quantity) AS quantity_sold, "
        " SUM(unit_price * quantity) AS gross_sales, "
        " SUM(unit_price * quantity) FILTER (WHERE status NOT IN ('Cancelled','Returned')) AS net_sales "
        "FROM {schema}.orders "
        "WHERE 1=1"
    ).format(schema=sql.Identifier(schema))

    params = []
    if start_date:
        base += " AND order_date >= %s"
        params.append(start_date)
    if end_date:
        base += " AND order_date <= %s"
        params.append(end_date)

    base += " GROUP BY order_date ORDER BY order_date"
    return base, params


def _product_rows(conn_or_dsn):
    conn = _connect(conn_or_dsn)
    try:
        with conn.cursor() as cur:
            cur.execute(_product_report())
            rows = cur.fetchall()
            keys = ["product", "order_count", "net_order_count", "quantity_sold", "gross_sales", "net_sales"]
            return [dict(zip(keys, r)) for r in rows]
    finally:
        _close(conn)


def _date_rows(conn_or_dsn, start_date=None, end_date=None):
    conn = _connect(conn_or_dsn)
    try:
        query, params = _date_report(start_date, end_date)
        with conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
            keys = ["order_date", "order_count", "net_order_count", "quantity_sold", "gross_sales", "net_sales"]
            return [dict(zip(keys, r)) for r in rows]
    finally:
        _close(conn)
