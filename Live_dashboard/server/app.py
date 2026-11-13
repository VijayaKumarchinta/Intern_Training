
from flask import Flask
from flask_cors import CORS
from server.api import api
from server.config import SOCKETIO_CORS_ORIGINS
from server.extensions import socketio

def create_app() -> Flask:
    app = Flask(__name__)

    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": SOCKETIO_CORS_ORIGINS,
            }
        },
    )

    app.register_blueprint(api)

    socketio.init_app(
        app,
        cors_allowed_origins=SOCKETIO_CORS_ORIGINS,
        async_mode="threading",
        logger=False,
        engineio_logger=False,
    )

    return app
