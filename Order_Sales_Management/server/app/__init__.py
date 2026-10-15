from flask import Flask, jsonify
from .config import Config
from .extensions import db, jwt, mail, bcrypt


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)

    @app.get("/")
    def root():
        return jsonify("All set to go......")

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