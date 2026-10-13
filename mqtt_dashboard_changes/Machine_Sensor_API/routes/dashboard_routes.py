import json
import time

from flask import Response, jsonify, request, stream_with_context

from config import (
    SSE_BATCH_LIMIT, SSE_MAX_SECONDS, SSE_POLL_SECONDS, STALE_AFTER_SECONDS,
)
from errors import ValidationError
from services.dashboard_service import dashboard_service
from utils.logger import logger
from utils.validation import machine_id_from_query, validate_sensor_tag

HEARTBEAT_SECONDS = 15


def overview():
    return jsonify(dashboard_service.overview(STALE_AFTER_SECONDS)), 200


def latest():
    return jsonify(dashboard_service.latest(machine_id_from_query())), 200


def series():
    machine_id = machine_id_from_query()
    if machine_id is None:
        raise ValidationError("machine_id is required")
    sensor_tag = validate_sensor_tag(request.args.get("sensor_tag"))
    try:
        minutes = int(request.args.get("minutes", 30))
    except ValueError:
        raise ValidationError("minutes must be an integer") from None
    if not 1 <= minutes <= 1440:
        raise ValidationError("minutes must be between 1 and 1440")
    return jsonify(dashboard_service.series(machine_id, sensor_tag, minutes)), 200


def _sse(event, data, event_id=None):
    head = f"id: {event_id}\n" if event_id is not None else ""
    return f"{head}event: {event}\ndata: {json.dumps(data)}\n\n"


def stream():
    """Server-Sent Events: new readings as they land in the database.

    Resumes from Last-Event-ID after a reconnect. Closes itself after
    SSE_MAX_SECONDS so the browser's EventSource reconnects and a dead client
    can never pin a server thread forever.
    """
    header = request.headers.get("Last-Event-ID", "")
    last_id = int(header) if header.isdigit() else dashboard_service.max_reading_id()

    def generate():
        nonlocal last_id
        started = last_beat = time.monotonic()
        yield "retry: 3000\n\n"
        yield _sse("hello", {"last_id": last_id})
        try:
            while time.monotonic() - started < SSE_MAX_SECONDS:
                batch = dashboard_service.readings_after(last_id, SSE_BATCH_LIMIT)
                if batch:
                    last_id = batch[-1]["reading_id"]
                    yield _sse("readings", batch, last_id)
                    last_beat = time.monotonic()
                    if len(batch) == SSE_BATCH_LIMIT:
                        continue  # more waiting, don't sleep
                elif time.monotonic() - last_beat >= HEARTBEAT_SECONDS:
                    yield ": heartbeat\n\n"
                    last_beat = time.monotonic()
                time.sleep(SSE_POLL_SECONDS)
        except GeneratorExit:
            logger.info("SSE client disconnected: last_id=%s", last_id)
            raise
        except Exception:
            logger.exception("SSE stream failed: last_id=%s", last_id)
            yield _sse("error", {"message": "stream interrupted"})

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
