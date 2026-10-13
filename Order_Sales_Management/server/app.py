"""
Order & Sales Management Application - Main Flask Application.

A layered REST API for managing customer orders, validating order details,
calculating order totals, tracking order statuses, identifying duplicate orders,
and generating product-wise and date-wise sales reports.

Architecture:
    HTTP request
       ↓
    app.py            — factory, error handlers, health endpoints
       ↓
    routes/           — MethodViews/Blueprints: HTTP parsing, status codes, JSON
       ↓
    services/         — all SQL, one class per domain, commit/rollback each
       ↓
    database/db.py   — pooled connections + context managers
       ↓
    PostgreSQL (sales schema: customers, products, orders, order_items, signatures)
"""
import logging
from contextlib import closing

from flask import Flask, jsonify, request, send_from_directory

from Order_Sales_Management.server.config import (
    APP_HOST,
    APP_PORT,
    DEBUG,
    CLIENT_DIR,
    LOG_LEVEL,
    validate_config,
)
from Order_Sales_Management.server.db import get_connection, test_connection
from Order_Sales_Management.server.routes import (
    customer_bp,
    product_bp,
    order_bp,
    report_bp,
)
from Order_Sales_Management.server.logging_config import configure_logging


# Configure logging before anything else
configure_logging()

# Create Flask app
app = Flask(__name__)
app.config['DEBUG'] = DEBUG

# Register blueprints
app.register_blueprint(customer_bp)
app.register_blueprint(product_bp)
app.register_blueprint(order_bp)
app.register_blueprint(report_bp)

logger = logging.getLogger(__name__)


@app.route('/')
def index():
    """Serve the client HTML (if exists) or API info."""
    if CLIENT_DIR.exists():
        return send_from_directory(CLIENT_DIR, 'index.html')
    return jsonify({
        "name": "Order & Sales Management API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/api/docs"
    })


@app.route('/health')
def health():
    """Basic health check."""
    return jsonify({
        "status": "healthy",
        "timestamp": logging.Formatter().formatTime(logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0, msg="", args=(), exc_info=None
        ))
    }), 200


@app.route('/health/ready')
def health_ready():
    """Check if database is ready."""
    try:
        with closing(get_connection()) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        return jsonify({
            "status": "ready",
            "database": "connected"
        }), 200
    except Exception as e:
        logger.exception("Health check failed")
        return jsonify({
            "status": "not ready",
            "database": "disconnected",
            "error": str(e)
        }), 503


@app.route('/api/docs')
def api_docs():
    """API documentation endpoint."""
    return jsonify({
        "api": "Order & Sales Management",
        "version": "1.0.0",
        "description": "REST API for managing customer orders, products, and sales reports",
        "endpoints": {
            "customers": {
                "GET /api/customers": "List all customers",
                "GET /api/customers/<customer_id>": "Get a customer by ID",
                "POST /api/customers": "Create a new customer"
            },
            "products": {
                "GET /api/products": "List all products (with optional filtering)",
                "GET /api/products/<product_id>": "Get a product by ID",
                "POST /api/products": "Create a new product"
            },
            "orders": {
                "GET /api/orders": "List all orders (with filtering options)",
                "GET /api/orders/<order_id>": "Get an order by ID",
                "POST /api/orders": "Create a new order",
                "PUT /api/orders/<order_id>/status": "Update order status"
            },
            "reports": {
                "GET /api/reports/product-sales": "Product-wise sales report",
                "GET /api/reports/date-sales": "Date-wise sales report",
                "GET /api/reports/summary": "Overall sales summary (KPIs)"
            }
        },
        "status_flow": {
            "pending": ["processing", "cancelled"],
            "processing": ["shipped", "cancelled"],
            "shipped": ["delivered", "returned"],
            "delivered": ["returned"],
            "cancelled": [],
            "returned": []
        }
    }), 200


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        "status": "error",
        "message": "Resource not found",
        "error": str(error)
    }), 404


@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors."""
    return jsonify({
        "status": "error",
        "message": "Method not allowed",
        "error": str(error)
    }), 405


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.exception("Internal server error")
    return jsonify({
        "status": "error",
        "message": "Internal server error",
        "error": "An unexpected error occurred"
    }), 500


if __name__ == '__main__':
    # Validate configuration at startup
    validate_config()

    # Verify database connection
    try:
        if test_connection():
            logger.info("Database connection verified")
        else:
            logger.warning("Database connection test returned unexpected result")
    except Exception as e:
        logger.error("Database connection failed: %s", e)
        raise

    logger.info("Starting Order & Sales Management API on %s:%s", APP_HOST, APP_PORT)
    app.run(host=APP_HOST, port=APP_PORT, debug=DEBUG)
