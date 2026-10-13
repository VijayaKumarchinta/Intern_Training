import logging

from flask import Flask, jsonify, send_from_directory

from .config import (
    APP_HOST, APP_PORT, DEBUG, CLIENT_DIR, LOG_LEVEL, validate_config,
)
from .db import get_connection, return_connection
from .logging_config import configure_logging
from .routes import customer_bp, product_bp, order_bp, report_bp

configure_logging()
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['DEBUG'] = DEBUG

app.register_blueprint(customer_bp)
app.register_blueprint(product_bp)
app.register_blueprint(order_bp)
app.register_blueprint(report_bp)


@app.route('/')
def index():
    if CLIENT_DIR.exists():
        return send_from_directory(CLIENT_DIR, 'index.html')
    return jsonify({"name": "Order & Sales Management API", "version": "1.0.0", "status": "running"})


@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200


@app.route('/health/ready')
def health_ready():
    try:
        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            return jsonify({"status": "ready", "database": "connected"}), 200
        finally:
            return_connection(conn)
    except Exception as e:
        logger.exception("Health check failed")
        return jsonify({"status": "not ready", "database": "disconnected", "error": str(e)}), 503


@app.errorhandler(404)
def not_found(error):
    return jsonify({"status": "error", "message": "Resource not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.exception("Internal server error")
    return jsonify({"status": "error", "message": "Internal server error"}), 500


if __name__ == '__main__':
    validate_config()
    try:
        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
            logger.info("Database connection verified")
        finally:
            return_connection(conn)
    except Exception as e:
        logger.error("Database connection failed: %s", e)
        raise
    logger.info("Starting API on %s:%s", APP_HOST, APP_PORT)
    app.run(host=APP_HOST, port=APP_PORT, debug=DEBUG)
