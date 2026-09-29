import os
import time

from flask import Flask, jsonify, request

from config import (
    GENERIC_DB_ERROR,
    DATA_DIR,
    IMPORT_FILE_NAME,
)
from database.connection import (
    db,
    DatabaseError,
    ConflictError,
    RelatedResourceNotFoundError,
)
from errors import ValidationError
from routes.machine_routes import MachineView
from routes.reading_routes import (
    ReadingView,
    ReadingExportView,
    ReadingStatisticsView,
)
from services.pickle_importer import pickle_importer
from utils.logger import logger


def create_app():
    app = Flask(__name__)

    @app.before_request
    def start_request_timer():
        from flask import g
        g.request_start_time = time.perf_counter()

    @app.after_request
    def log_request(response):
        from flask import g
        start = getattr(g, "request_start_time", None)
        duration_ms = (time.perf_counter() - start) * 1000 if start else 0
        logger.info("HTTP %s %s status=%s duration_ms=%.2f", request.method, request.path, response.status_code, duration_ms)
        return response

    @app.errorhandler(404)
    def handle_404(_error):
        logger.warning("HTTP 404: method=%s path=%s", request.method, request.path)
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(405)
    def handle_405(_error):
        logger.warning("HTTP 405: method=%s path=%s", request.method, request.path)
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(400)
    def handle_400(_error):
        logger.warning("HTTP 400: method=%s path=%s", request.method, request.path)
        return jsonify({"error": "Bad request"}), 400

    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        logger.warning("Validation error: %s", error)
        return jsonify({"error": str(error)}), 400

    @app.errorhandler(ConflictError)
    def handle_conflict_error(error):
        logger.warning("Conflict error: %s", error)
        return jsonify({"error": str(error)}), 409

    @app.errorhandler(RelatedResourceNotFoundError)
    def handle_related_resource_not_found(error):
        logger.warning("Related resource not found: %s", error)
        return jsonify({"error": str(error)}), 400

    @app.errorhandler(DatabaseError)
    def handle_database_error(error):
        logger.exception("Database error: %s", error)
        return jsonify({"error": GENERIC_DB_ERROR}), 500

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        logger.exception("Unhandled application error: %s", error)
        return jsonify({"error": "An unexpected error occurred."}), 500

    app.add_url_rule(
        "/machines",
        view_func=MachineView.as_view("machines"),
        methods=["GET", "POST"],
    )

    app.add_url_rule(
        "/machines/<int:machine_id>",
        view_func=MachineView.as_view("machine_detail"),
        methods=["GET", "PUT", "DELETE"],
    )

    app.add_url_rule(
        "/readings",
        view_func=ReadingView.as_view("readings"),
        methods=["GET", "POST"],
    )

    app.add_url_rule(
        "/readings/<int:reading_id>",
        view_func=ReadingView.as_view("reading_detail"),
        methods=["GET", "PUT", "DELETE"],
    )

    app.add_url_rule(
        "/readings/export",
        view_func=ReadingExportView.as_view("reading_export"),
        methods=["GET"],
    )

    app.add_url_rule(
        "/readings/statistics",
        view_func=ReadingStatisticsView.as_view("reading_statistics"),
        methods=["GET"],
    )

    @app.route("/", methods=["GET"])
    def index():
        return jsonify({
            "name": "Machine Sensor API",
            "status": "running",
            "endpoints": [
                "GET /health",
                "GET|POST /machines",
                "GET|PUT|DELETE /machines/<machine_id>",
                "GET|POST /readings",
                "GET|PUT|DELETE /readings/<reading_id>",
                "GET /readings/statistics",
                "GET /readings/export",
                "POST /readings/import",
            ],
        }), 200

    @app.route("/health", methods=["GET"])
    def health():
        connection = None

        try:
            connection = db.get_connection()
            cursor = connection.cursor()

            try:
                cursor.execute("SELECT 1")
            finally:
                cursor.close()

            logger.info("Health check succeeded: database connected")
            return jsonify({
                "status": "ok",
                "database": "connected",
            }), 200

        except DatabaseError as error:
            logger.error("Health check failed: database disconnected: %s", error)
            return jsonify({
                "status": "error",
                "database": "disconnected",
            }), 503

        finally:
            if connection:
                connection.close()

    @app.route("/readings/import", methods=["POST"])
    def import_readings():
        try:
            file_path = os.path.join(DATA_DIR, IMPORT_FILE_NAME)

            logger.info("Data import started: pickle=%s", IMPORT_FILE_NAME)
            inserted = pickle_importer.import_file(file_path)
            logger.info("Data import completed: pickle=%s csv=%s inserted=%s skipped=%s", IMPORT_FILE_NAME, inserted["csv_file"], inserted["records_inserted"], inserted["records_skipped"])

            return jsonify({
                "message": "Pickle file converted to CSV and imported successfully",
                "file": IMPORT_FILE_NAME,
                "csv_file": inserted["csv_file"],
                "records_inserted": inserted["records_inserted"],
                "records_skipped": inserted["records_skipped"],
            }), 201

        except ValueError as error:
            logger.warning("Pickle import rejected: %s", error)
            return jsonify({"error": str(error)}), 400
    return app

app = create_app()

if __name__ == "__main__":
    from waitress import serve

    logger.info("Machine Sensor API starting")
    logger.info("Server: http://localhost:8080")

    serve(app)