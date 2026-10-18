from flask import Flask, jsonify
from .config import Config, configure_logging
from .constants import Role
from .extensions import db, jwt, mail

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    configure_logging(app)

    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)

    from .routes.auth import auth_bp
    from .routes.orders import orders_bp
    from .routes.reports import reports_bp
    from .routes.products import products_bp
    from .routes.customers import customers_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(customers_bp)

    @app.get("/")
    def root():
        return jsonify(status="ok"), 200

    @app.get("/health")
    def health():
        return jsonify(status="ok"), 200
    return app