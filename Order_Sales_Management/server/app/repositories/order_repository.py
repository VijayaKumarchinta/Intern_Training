"""
order_repository - all SQL against PostgreSQL.

Every query is parameterized to avoid SQL injection.
The repository opens its own connection from the configured DSN, so callers
just pass the DSN (or an existing connection) and the repository cleans up.
"""

import logging

import psycopg2
from psycopg2 import sql

from app import config as app_config

logger = logging.getLogger(__name__)


def _get_conn():
    """Open a fresh connection from the configured DSN."""
    return app_config.Config().connect()


def _get_schema():
    return app_config.config.DB_SCHEMA


def _order_columns():
    return [
        "order_id", "customer_id", "product", "quantity",
        "unit_price", "order_date", "status", "created_at", "updated_at",
    ]


def _connect(conn_or_dsn):
    """Accept an existing connection or a DSN string, return a connection."""
    if hasattr(conn_or_dsn, "cursor"):
        return conn_or_dsn
    return _get_conn()


def _close(conn):
    """Close a connection we opened ourselves; ignore connections we did not open."""
    if conn is not None and not hasattr(conn, "_owned_by_repo"):
        try:
            conn.close()
        except Exception:
            pass


# ---- Create ----


def insert_order(conn_or_dsn, order):
    """
    Insert one order inside a transaction.
    Returns the inserted row.
    """
    conn = _connect(conn_or_dsn)
    try:
        schema = _get_schema()
        with conn.cursor() as cur:
            cur.execute(
                sql.SQL(
                    "INSERT INTO {schema}.orders "
                    "(order_id, customer_id, product, quantity, unit_price, order_date, status) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s) "
                    "RETURNING {columns}"
                ).format(
                    schema=sql.Identifier(schema),
                    columns=sql.SQL(", ").join(sql.Identifier(c) for c in _order_columns()),
                ),
                (
                    order["order_id"],
                    order["customer_id"],
                    order["product"],
                    order["quantity"],
                    order["unit_price"],
                    order["order_date"],
                    order["status"],
                ),
            )
            row = cur.fetchone()
            conn.commit()
            return dict(zip(_order_columns(), row))
    finally:
        _close(conn)


# ---- Read ----


def find_order(conn_or_dsn, order_id):
    """
    Find one order by id.
    Returns the row, or None.
    """
    conn = _connect(conn_or_dsn)
    try:
        schema = _get_schema()
        with conn.cursor() as cur:
            cur.execute(
                sql.SQL("SELECT {columns} FROM {schema}.orders WHERE order_id = %s").format(
                    schema=sql.Identifier(schema),
                    columns=sql.SQL(", ").join(sql.Identifier(c) for c in _order_columns()),
                ),
                (order_id,),
            )
            row = cur.fetchone()
            return None if row is None else dict(zip(_order_columns(), row))
    finally:
        _close(conn)


def list_orders(
    conn_or_dsn,
    status=None,
    customer_id=None,
    start_date=None,
    end_date=None,
    page=1,
    page_size=50,
):
    """
    Paginated, filterable order list.
    Filters are inclusive; an empty filter set returns the newest orders first.
    """
    conn = _connect(conn_or_dsn)
    try:
        schema = _get_schema()
        clauses = ["1=1"]
        params = []

        if status:
            clauses.append("status = %s")
            params.append(status)
        if customer_id:
            clauses.append("customer_id = %s")
            params.append(customer_id)
        if start_date:
            clauses.append("order_date >= %s")
            params.append(start_date)
        if end_date:
            clauses.append("order_date <= %s")
            params.append(end_date)

        where = sql.SQL(" AND ").join(sql.SQL(c) for c in clauses)

        offset = (page - 1) * page_size

        query = sql.SQL(
            "SELECT {columns} FROM {schema}.orders "
            "WHERE {where} "
            "ORDER BY created_at DESC "
            "LIMIT %s OFFSET %s"
        ).format(
            schema=sql.Identifier(schema),
            columns=sql.SQL(", ").join(sql.Identifier(c) for c in _order_columns()),
            where=where,
        )
        params.extend([page_size, offset])

        with conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
            return [dict(zip(_order_columns(), r)) for r in rows]
    finally:
        _close(conn)


# ---- Update ----


def update_order_fields(conn_or_dsn, order_id, fields):
    """
    Update editable columns on a Pending order.
    fields may contain product, quantity, unit_price.
    """
    if not fields:
        return find_order(conn_or_dsn, order_id)

    conn = _connect(conn_or_dsn)
    try:
        schema = _get_schema()
        set_clauses = []
        params = []

        if "product" in fields:
            set_clauses.append("product = %s")
            params.append(fields["product"])
        if "quantity" in fields:
            set_clauses.append("quantity = %s")
            params.append(fields["quantity"])
        if "unit_price" in fields:
            set_clauses.append("unit_price = %s")
            params.append(fields["unit_price"])

        query = sql.SQL(
            "UPDATE {schema}.orders "
            "SET {set_clause}, updated_at = NOW() "
            "WHERE order_id = %s AND status = 'Pending' "
            "RETURNING {columns}"
        ).format(
            schema=sql.Identifier(schema),
            set_clause=sql.SQL(", ").join(sql.SQL(c) for c in set_clauses),
            columns=sql.SQL(", ").join(sql.Identifier(c) for c in _order_columns()),
        )
        params.append(order_id)

        with conn.cursor() as cur:
            cur.execute(query, params)
            row = cur.fetchone()
            if row is None:
                return None
            return dict(zip(_order_columns(), row))
    finally:
        _close(conn)


def update_order_status(conn_or_dsn, order_id, status):
    """
    Change status only on allowed transitions.
    Returns the updated row, or None if it does not exist / transition is invalid.
    """
    conn = _connect(conn_or_dsn)
    try:
        schema = _get_schema()
        with conn.cursor() as cur:
            cur.execute(
                sql.SQL(
                    "UPDATE {schema}.orders "
                    "SET status = %s, updated_at = NOW() "
                    "WHERE order_id = %s AND status = %s "
                    "RETURNING {columns}"
                ).format(
                    schema=sql.Identifier(schema),
                    columns=sql.SQL(", ").join(sql.Identifier(c) for c in _order_columns()),
                ),
                (status, order_id, "Pending"),
            )
            row = cur.fetchone()
            if row is None:
                return None
            return dict(zip(_order_columns(), row))
    finally:
        _close(conn)


# ---- Idempotency / duplicates ----


def find_by_idempotency_key(conn_or_dsn, key):
    """
    Find the order_id and payload_hash behind an Idempotency-Key.
    Returns a dict, or None if the key is unknown.
    """
    conn = _connect(conn_or_dsn)
    try:
        schema = _get_schema()
        with conn.cursor() as cur:
            cur.execute(
                sql.SQL("SELECT order_id, payload_hash FROM {schema}.idempotency WHERE idempotency_key = %s").format(
                    schema=sql.Identifier(schema),
                ),
                (key,),
            )
            row = cur.fetchone()
            if row is None:
                return None
            return {"order_id": row[0], "payload_hash": row[1]}
    finally:
        _close(conn)


def find_by_payload_hash(conn_or_dsn, payload_hash):
    """
    Find the order_id that shares a payload_hash (duplicate-content check).
    Returns the order_id, or None.
    """
    conn = _connect(conn_or_dsn)
    try:
        schema = _get_schema()
        with conn.cursor() as cur:
            cur.execute(
                sql.SQL("SELECT order_id FROM {schema}.idempotency WHERE payload_hash = %s").format(
                    schema=sql.Identifier(schema),
                ),
                (payload_hash,),
            )
            row = cur.fetchone()
            return row[0] if row else None
    finally:
        _close(conn)


def record_idempotency(conn_or_dsn, key, payload_hash, order_id):
    """
    Persist one Idempotency-Key (durable storage).
    Idempotent: safe to call again with the same key.
    """
    conn = _connect(conn_or_dsn)
    try:
        schema = _get_schema()
        with conn.cursor() as cur:
            cur.execute(
                sql.SQL(
                    "INSERT INTO {schema}.idempotency (idempotency_key, payload_hash, order_id) "
                    "VALUES (%s, %s, %s) "
                    "ON CONFLICT (idempotency_key) DO UPDATE "
                    "SET payload_hash = EXCLUDED.payload_hash, order_id = EXCLUDED.order_id"
                ).format(schema=sql.Identifier(schema)),
                (key, payload_hash, order_id),
            )
            conn.commit()
    finally:
        _close(conn)
