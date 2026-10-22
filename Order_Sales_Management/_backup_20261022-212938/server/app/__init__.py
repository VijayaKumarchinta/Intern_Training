from flask import Flask, jsonify
from .config import Config, configure_logging
from .extensions import db, jwt, mail

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    configure_logging(app)

    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)

    @jwt.invalid_token_loader
    def invalid_token(reason):
        return jsonify(error="Invalid token"), 401

    @jwt.unauthorized_loader
    def missing_token(reason):
        return jsonify(error="Missing token"), 401

    @jwt.expired_token_loader
    def expired_token(jwt_header, jwt_payload):
        return jsonify(error="Token expired"), 401

    from .routes.auth import auth_bp
    from .routes.orders import orders_bp
    from .routes.reports import reports_bp
    from .routes.products import products_bp
    from .routes.customers import customers_bp
    from .routes.users import users_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(customers_bp)
    app.register_blueprint(users_bp)

    @app.get("/")
    def root():
        return jsonify(status="ok"), 200

    @app.get("/health")
    def health():
        return jsonify(status="ok"), 200
    return app