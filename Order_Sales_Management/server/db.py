"""
Database connection module for Order & Sales Management Application.
Uses psycopg2 with proper error handling and context management.
Connects to existing database - does NOT create schema/tables.
"""
import logging
import psycopg2
import psycopg2.pool
from contextlib import contextmanager

from .config import (
    DB_HOST,
    DB_PORT,
    DB_NAME,
    DB_USER,
    DB_PASSWORD,
)

logger = logging.getLogger(__name__)

# Thread-safe connection pool for concurrent requests
_connection_pool = None


def get_pool():
    """Get or create the connection pool (singleton)."""
    global _connection_pool
    if _connection_pool is None:
        _connection_pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            connect_timeout=5,
        )
        logger.info("Database connection pool initialized")
    return _connection_pool


@contextmanager
def get_connection():
    """
    Get a database connection from the pool.
    Returns connection to pool on exit; discards if broken.
    """
    pool = get_pool()
    conn = pool.getconn()
    try:
        yield conn
    except Exception:
        conn.rollback()
        raise
    finally:
        try:
            if conn.closed:
                logger.warning("Connection was closed, discarding from pool")
                pool.putconn(conn, close=True)
            else:
                pool.putconn(conn)
        except Exception:
            logger.exception("Error returning connection to pool")


@contextmanager
def get_cursor(commit_on_success=True):
    """
    Get a cursor with automatic commit/rollback.
    Usage:
        with get_cursor() as cursor:
            cursor.execute("SELECT ...")
    """
    with get_connection() as conn:
        with conn.cursor() as cursor:
            try:
                yield cursor
                if commit_on_success:
                    conn.commit()
            except Exception:
                conn.rollback()
                raise


def test_connection():
    """Verify database connection is working."""
    with get_cursor(commit_on_success=False) as cursor:
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        if result and result[0] == 1:
            logger.info("Database connection verified")
            return True
    return False


class DatabaseError(Exception):
    """Base exception for database errors."""
    pass


class ValidationError(DatabaseError):
    """Raised when data validation fails."""
    pass


class ConflictError(DatabaseError):
    """Raised when a conflict occurs (e.g., duplicate entry)."""
    pass


class NotFoundError(DatabaseError):
    """Raised when a resource is not found."""
    pass
