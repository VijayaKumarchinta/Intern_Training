import argparse
import json
import logging
import signal
import threading
import uuid
from datetime import date, datetime, time as datetime_time
from pathlib import Path
import pandas as pd
import paho.mqtt.client as mqtt

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PARQUET_FILE = PROJECT_ROOT / "data" / "processed" / "line_speed_30_clean.parquet"

BROKER_HOST = "127.0.0.1"
BROKER_PORT = 1883
MQTT_TOPIC = "factory/line30/telemetry"
MQTT_QOS = 1
KEEPALIVE = 60
PUBLISH_TIMEOUT = 10

LINE_ID = "line30"
DEFAULT_REPLAY_SPEED = 1.0

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("line30.publisher")

stop_event = threading.Event()
connected_event = threading.Event()


def handle_shutdown(signum, frame):
    logger.info("Shutdown requested. Finishing current operation...")
    stop_event.set()


def json_serializer(value):
    if isinstance(value, (pd.Timestamp, datetime, date, datetime_time)):
        return value.isoformat()

    if hasattr(value, "item"):
        return value.item()

    raise TypeError(f"Unsupported JSON value: {type(value).__name__}")


def load_telemetry():
    if not PARQUET_FILE.is_file():
        raise FileNotFoundError(f"Processed dataset not found: {PARQUET_FILE}")

    dataframe = pd.read_parquet(PARQUET_FILE)

    required_columns = {"message_id", "event_ts", "source_row"}
    missing_columns = required_columns.difference(dataframe.columns)

    if missing_columns:
        raise ValueError(
            f"Processed dataset is missing required columns: {sorted(missing_columns)}"
        )

    if dataframe.empty:
        raise ValueError("Processed dataset contains no telemetry records.")

    if dataframe["message_id"].isna().any():
        raise ValueError("Dataset contains missing message IDs.")

    if not dataframe["message_id"].is_unique:
        raise ValueError("Source message IDs are not unique.")

    if dataframe["event_ts"].isna().any():
        raise ValueError("Dataset contains missing event timestamps.")

    dataframe = dataframe.sort_values(
        ["event_ts", "source_row"]
    ).reset_index(drop=True)

    return dataframe


def create_mqtt_client():
    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id=f"line30-{uuid.uuid4().hex[:8]}",
        protocol=mqtt.MQTTv311,
    )

    def on_connect(client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            connected_event.set()
            logger.info("Connected to MQTT broker at %s:%s", BROKER_HOST, BROKER_PORT)
        else:
            logger.error("MQTT connection rejected: %s", reason_code)

    def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
        connected_event.clear()
        logger.warning("MQTT disconnected: %s", reason_code)

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect

    return client


def publish_record(
    client,
    record,
    session_id,
    cycle_id,
    cycle_number,
    total_records,
):
    payload = dict(record)

    payload.update({
        "line_id": LINE_ID,
        "replay_session_id": session_id,
        "replay_cycle_id": cycle_id,
        "replay_cycle_number": cycle_number,
        "replay_total_records": total_records,
    })

    encoded_payload = json.dumps(
        payload,
        default=json_serializer,
        separators=(",", ":"),
        allow_nan=False,
    )

    info = client.publish(
        MQTT_TOPIC,
        payload=encoded_payload,
        qos=MQTT_QOS,
        retain=False,
    )

    info.wait_for_publish(timeout=PUBLISH_TIMEOUT)

    if not info.is_published():
        raise TimeoutError(
            f"Publish acknowledgement timed out for message {record['message_id']}"
        )


def calculate_delay(current_timestamp, next_timestamp, fallback_interval, speed):
    interval = (next_timestamp - current_timestamp).total_seconds()

    if interval <= 0:
        interval = fallback_interval

    return interval / speed


def run_replay(dataframe, speed, once, limit):
    session_id = str(uuid.uuid4())
    cycle_number = 0
    fallback_interval = float(
        dataframe["event_ts"].diff().dt.total_seconds().median()
    )

    if fallback_interval <= 0:
        raise ValueError("Unable to determine a valid replay interval.")

    client = create_mqtt_client()

    try:
        client.connect(BROKER_HOST, BROKER_PORT, keepalive=KEEPALIVE)
        client.loop_start()

        if not connected_event.wait(timeout=10):
            raise TimeoutError("Could not establish MQTT connection within 10 seconds.")

        logger.info("Dataset records: %d", len(dataframe))
        logger.info("Topic: %s | QoS: %d | Replay speed: %sx",
                    MQTT_TOPIC, MQTT_QOS, speed)
        logger.info("Replay session: %s", session_id)

        while not stop_event.is_set():
            cycle_number += 1
            cycle_id = str(uuid.uuid4())
            published_count = 0

            logger.info(
                "Starting replay cycle %d | cycle_id=%s",
                cycle_number,
                cycle_id,
            )

            for index, row in dataframe.iterrows():
                if stop_event.is_set():
                    break

                record = row.to_dict()

                publish_record(
                    client,
                    record,
                    session_id,
                    cycle_id,
                    cycle_number,
                    len(dataframe),
                )

                published_count += 1

                if published_count == 1 or published_count % 100 == 0:
                    logger.info(
                        "Cycle %d | Published %d records | Last source row: %s",
                        cycle_number,
                        published_count,
                        record["source_row"],
                    )

                if limit is not None and published_count >= limit:
                    break

                if index < len(dataframe) - 1:
                    next_timestamp = dataframe.iloc[index + 1]["event_ts"]
                    delay = calculate_delay(
                        record["event_ts"],
                        next_timestamp,
                        fallback_interval,
                        speed,
                    )
                else:
                    delay = fallback_interval / speed

                if stop_event.wait(delay):
                    break

            logger.info(
                "Replay cycle %d ended | Published: %d",
                cycle_number,
                published_count,
            )

            if once or limit is not None or stop_event.is_set():
                break

        logger.info("Replay publisher stopped.")

    finally:
        client.loop_stop()
        client.disconnect()


def main():
    parser = argparse.ArgumentParser(
        description="Replay Line Speed 30 Parquet telemetry over MQTT."
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=DEFAULT_REPLAY_SPEED,
        help="Replay speed multiplier. 1.0 preserves source timing.",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Publish one dataset cycle and exit.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of records to publish in this test run.",
    )

    args = parser.parse_args()

    if args.speed <= 0:
        parser.error("--speed must be greater than zero.")

    if args.limit is not None and args.limit <= 0:
        parser.error("--limit must be greater than zero.")

    signal.signal(signal.SIGINT, handle_shutdown)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, handle_shutdown)

    dataframe = load_telemetry()
    logger.info("Loaded cleaned Parquet dataset: %s", PARQUET_FILE)

    run_replay(dataframe, args.speed, args.once, args.limit)


if __name__ == "__main__":
    main()

