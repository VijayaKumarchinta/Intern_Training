import logging
import psycopg2
import psycopg2.pool

from .config import (
    DB_HOST,
    DB_PORT,
    DB_NAME,
    DB_USER,
    DB_PASSWORD,
    DB_SCHEMA,
)

logger = logging.getLogger(__name__)

_pool = None


def _get_pool():
    global _pool
    if _pool is None:
        _pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            connect_timeout=5,
        )
        logger.info("Database connection pool created")
    return _pool


def get_connection():
    pool = _get_pool()
    return pool.getconn()


def return_connection(conn):
    if conn.closed:
        logger.warning("Closed connection returned to pool, discarding")
        _get_pool().putconn(conn, close=True)
    else:
        _get_pool().putconn(conn)


def qualified(table):
    return f"{DB_SCHEMA}.{table}"


class DatabaseError(Exception):
    pass


class NotFoundError(DatabaseError):
    pass


class ConflictError(DatabaseError):
    pass
