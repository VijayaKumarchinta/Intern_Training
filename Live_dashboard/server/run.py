
import logging
from server.app import create_app
from server.extensions import socketio
from server.mqtt.subscriber import (
    start_mqtt_subscriber,
    stop_mqtt_subscriber,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
app = create_app()

def main():
    subscriber = None

    try:
        subscriber = start_mqtt_subscriber()

        socketio.run(
            app,
            host="127.0.0.1",
            port=8000,
            debug=False,
            use_reloader=False,
            allow_unsafe_werkzeug=True,
        )
    except KeyboardInterrupt:
        logging.info("Application shutdown requested")
    finally:
        if subscriber is not None:
            stop_mqtt_subscriber(subscriber)

if __name__ == "__main__":
    main()
