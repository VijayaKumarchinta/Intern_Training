
from flask import jsonify
from sqlalchemy.exc import SQLAlchemyError

from server.api import api
from server.database import ping_database
from server.mqtt.subscriber import is_mqtt_connected


@api.get("/health")
def health():
    database_connected = False

    try:
        ping_database()
        database_connected = True
    except SQLAlchemyError:
        pass

    mqtt_connected = is_mqtt_connected()
    healthy = database_connected and mqtt_connected

    return jsonify({
        "status": "healthy" if healthy else "unhealthy",
        "database": (
            "connected" if database_connected else "disconnected"
        ),
        "mqtt": (
            "connected" if mqtt_connected else "disconnected"
        ),
    }), 200 if healthy else 503
