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
    def health():
        return jsonify(status="ok"), 200

    return app