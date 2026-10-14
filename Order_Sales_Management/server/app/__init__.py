from flask import Flask

from app.config import Config
from app.extensions import db, jwt, mail, bcrypt
from app import cli


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    bcrypt.init_app(app)

    _register_blueprints(app)
    cli.register_cli(app)

    @app.route("/health")
    def health():
        return {"status": "ok"}

    return app


def _register_blueprints(app: Flask) -> None:
    from app.routes.auth import auth_bp
    from app.routes.orders import orders_bp
    from app.routes.reports import reports_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(orders_bp, url_prefix="/api/orders")
    app.register_blueprint(reports_bp, url_prefix="/api/reports")
