from flask import Flask, jsonify
from .config import Config, configure_logging
from .extensions import db, jwt, mail
from flask_jwt_extended import jwt_required

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

    app.register_blueprint(auth_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(reports_bp)

    @app.get("/")
    def root():
        return jsonify(status="ok"), 200

    @app.get("/health")
    def health():
        return jsonify(status="ok"), 200

    @app.get("/db")
    @jwt_required()
    def database():
        from .models import Customer, Order, User
        return jsonify(
            orders=Order.query.count(),
            customers=Customer.query.count(),
            users=User.query.count(),
        ), 200

    return app