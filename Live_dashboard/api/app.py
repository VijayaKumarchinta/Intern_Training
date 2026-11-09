import logging

from flask import Flask, jsonify
from flask.logging import default_handler

from .config import config_by_name
from .db import db, migrate
from .routes.health import health_bp
from .routes.history import history_bp
from .routes.stats import stats_bp
from .routes.manifest import manifest_bp
from .routes.alarms import alarms_bp
from .routes.export import export_bp


def create_app(config_name='production'):
    app = Flask(__name__)

    app.config.from_object(config_by_name[config_name])

    db.init_app(app)
    migrate.init_app(app, db)

    _setup_logging(app)
    _register_blueprints(app)
    _register_error_handlers(app)
    return app

def _setup_logging(app):
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s %(name)s %(filename)s:%(lineno)d %(funcName)s %(message)s'
    )
    handler.setFormatter(formatter)

    if not app.logger.handlers:
        app.logger.addHandler(handler)

    app.logger.setLevel(getattr(logging, app.config.get('LOG_LEVEL', 'INFO')))


def _register_blueprints(app):
    app.register_blueprint(health_bp, url_prefix='/api/v1')
    app.register_blueprint(history_bp, url_prefix='/api/v1')
    app.register_blueprint(stats_bp, url_prefix='/api/v1')
    app.register_blueprint(manifest_bp, url_prefix='/api/v1')
    app.register_blueprint(alarms_bp, url_prefix='/api/v1')
    app.register_blueprint(export_bp, url_prefix='/api/v1')


def _register_error_handlers(app):

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'not_found', 'message': 'Resource not found'}), 404

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({'error': 'internal_error', 'message': 'Internal server error'}), 500

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({'error': 'bad_request', 'message': 'Bad request'}), 400