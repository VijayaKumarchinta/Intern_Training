"""
Order and Sales Management - backend.

Flask API over PostgreSQL. Requests flow through:
    route  ->  validator  ->  service  ->  repository (SQL)
"""

from flask import Flask, jsonify, request
from flask_cors import CORS

from app import config as app_config
from app import repositories
from app import services
from app import validators


def create_app() -> Flask:
    app = Flask(__name__)

    # CORS: allow the Vue frontend to call the API.
    CORS(app, resources={r"/api/*": {"origins": app_config.config.FRONTEND_ORIGIN}})

    # Register API routes.
    from app.routes import orders_bp
    from app.routes import reports_bp
    app.register_blueprint(orders_bp)
    app.register_blueprint(reports_bp)

    # Health check.
    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok", "service": "order-sales-management"}), 200

    @app.errorhandler(404)
    def not_found(_e):
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Not found."}}), 404

    @app.errorhandler(405)
    def method_not_allowed(_e):
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "Method not allowed."}}), 405

    @app.errorhandler(500)
    def internal_error(e):
        # Details stay in the server log, not in the client response.
        return (
            jsonify({"error": {"code": "INTERNAL_ERROR", "message": "Something went wrong."}}),
            500,
        )

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=app_config.config.DEBUG)
