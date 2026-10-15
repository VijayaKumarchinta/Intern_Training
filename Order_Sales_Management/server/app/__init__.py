from flask import Flask, jsonify

from .config import Config, configure_logging
from .extensions import db, jwt, mail

from .config import Config, configure_logging
from .extensions import db, jwt, mail

from .routes import auth, orders, reports


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    configure_logging(app)

    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)

    app.register_blueprint(auth, url_prefix="/api/auth")
    app.register_blueprint(orders, url_prefix="/api/orders")
    app.register_blueprint(reports, url_prefix="/api/reports")

    @app.get("/")
    def root():
        return jsonify(status="ok"), 200

    @app.get("/health")
    def health():
        return jsonify(status="ok"), 200

    @app.get("/db")
    def database():
        from .models import Order, Customer, User

        return jsonify(
            orders=Order.query.count(),
            customers=Customer.query.count(),
            users=User.query.count(),
        ), 200

    return app
