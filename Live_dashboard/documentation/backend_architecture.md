# 3. Backend Architecture Explanation

## 3.1 Responsibilities

The backend is a Flask + Flask-SocketIO service. It has four runtime zones:

1. **MQTT ingest zone** — receives telemetry from the broker and persists it.
2. **REST API zone** — serves health, telemetry, summary, events, cycle
   classification, and CSV exports.
3. **Socket.IO broadcast zone** — pushes live telemetry and operational events
   to subscribed frontends.
4. **Database zone** — SQLAlchemy engine and SQL queries.

There is no message queue, no cache tier, and no separate worker process.
Batching and lifecycle management live inside the Flask application and the
MQTT subscriber.

## 3.2 Application structure

```text
server/run.py                # entry point: MQTT subscriber + socketio.run()
server/app.py                # Flask application factory
server/config.py             # environment validation
server/extensions.py         # Socket.IO instance
server/api/__init__.py       # registered blueprint
server/api/health_routes.py  # /api/health
server/api/telemetry_routes.py   # /api/telemetry/*
server/api/summary_routes.py     # /api/summary/hourly
server/api/event_routes.py       # /api/events
server/api/replay_routes.py      # /api/history/cycles
server/api/export_routes.py      # /api/exports/*.csv
server/sockets/__init__.py
server/sockets/socket_events.py  # join_line / leave_line
server/sockets/broadcaster.py    # Socket.IO emit helpers
server/repositories/__init__.py
server/repositories/telemetry_query_repository.py
server/repositories/telemetry_repository.py
server/repositories/summary_repository.py
server/repositories/event_repository.py
server/repositories/export_repository.py
server/repositories/replay_repository.py
server/services/__init__.py
server/services/telemetry_service.py
server/services/summary_service.py
server/services/event_service.py
server/services/export_service.py
server/services/replay_service.py
server/database/__init__.py
server/database/connection.py
server/mqtt/__init__.py
server/mqtt/subscriber.py
server/mqtt/message_handler.py
```

## 3.3 Application bootstrap

1. `server/run.py` creates the application with `create_app()`.
2. `server/app.py` configures CORS for `/api/*`, registers the API blueprint,
   and initializes the Socket.IO instance with the allowed CORS origins.
3. `import server.sockets.socket_events` registers the Socket.IO event handlers.
4. `run.py` starts `start_mqtt_subscriber()` and then `socketio.run(app, ...)`.

`create_app()` is the only factory that wires the two runtimes together.

## 3.4 MQTT ingest pipeline

```text
paho.mqtt client
  -> socket/connect callback
  -> subscribe(factory/line30/telemetry, qos=1)
  -> loop_start()
  -> on_message -> on_message()
       -> decode -> json.loads -> save_telemetry()
       -> ack or keep unacked
```

The subscriber uses `clean_session=False` and `manual_ack=True`, so a
restarted client can safely resume with a broker that does not discard its
state.

`on_message()` never blocks the paho network loop on persistence. It handles
SQLAlchemy errors and unexpected exceptions by returning early so the message
remains unacknowledged and can be redelivered later.

## 3.5 Persistence layer

`server/repositories/telemetry_repository.py` holds the write path for a
single telemetry reading:

- `INSERT_TELEMETRY_SQL` inserts into `telemetry.readings`
  (`message_id`, `replay_session_id`, `replay_cycle_id`, `replay_cycle_number`,
  `line_id`, `event_ts`, `payload`).
- The unique constraint `(replay_cycle_id, message_id)` makes the insert
  idempotent.
- `save_telemetry()` returns either `None` for a duplicate or a record with
  `id`, `received_at`, and any alarm events generated.

Alarm processing is embedded in the repository. For a valid moisture reading
the repository:

1. Inserts the reading.
2. Checks current state from `telemetry.alarm_state` with `FOR UPDATE`.
3. Emits `CLEARED` and/or `ACTIVE` alarm events.
4. Updates alarm state with the new event code, severity, and last reading id.

## 3.6 Read side

- `server/repositories/telemetry_query_repository.py` provides read-only
  queries: latest reading, history, statistics.
- `server/repositories/summary_repository.py` provides the heavy
  `get_hourly_summary_data()` query. It uses a recursive `WITH` clause to
  materialise one row per hour, calculates per-hour aggregates, and tracks
  burner-at-100% duration from consecutive readings where
  `Burner Output Load = 100`.
- `server/repositories/event_repository.py` returns the latest N operational
  events.
- `server/repositories/export_repository.py` provides CSV export row sets.
- `server/repositories/replay_repository.py` classifies replay cycles as
  `COMPLETED`, `INCOMPLETE`, or `UNKNOWN` using metadata, fingerprints, and
  source-row coverage.

## 3.7 Service layer

The service layer converts rows into JSON-safe objects and shapes API
responses.

| Service | Responsibility |
| --- | --- |
| `telemetry_service.py` | parsing, timestamp validation, reading serialization |
| `summary_service.py` | assembles `cycle_id`, `window_start/end`, `hours`, `data`, `statistics` |
| `event_service.py` | serializes alarm and system events |
| `export_service.py` | builds CSV strings for summary, readings, and events |

## 3.8 REST route layer

Routes are thin. Each handler validates parameters, calls one service, and
returns a `jsonify` response or a 400/500 error.

### `GET /api/health`

Returns `status`, `database`, and `mqtt` indicators. It is the dashboard's
system-health signal.

### `GET /api/telemetry/latest`

One newest reading for a line.

### `GET /api/telemetry/history`

Paginated reading history. Accepts `line_id`, `limit`, `before`, and, for
historical drill-down, `cycle_id`, `start`, `end`.

### `GET /api/telemetry/statistics`

Aggregate statistics for one field inside an optional time window.

### `GET /api/summary/hourly`

Hourly summary rows and statistics. Accepts `line_id`, `hours`, and, for the
historical view, `cycle_id` and `hour_start`.

### `GET /api/events`

Operational event history. Accepts `line_id`, `limit`, and optional
`cycle_id`, `start`, `end`.

### `GET /api/history/cycles`

Replay-cycle completion classification. Returns cycle id, status, status
reason, persisted and expected record counts, fingerprints, and time bounds.

### `GET /api/exports/hourly-summary.csv`

Full cycle summary CSV.

### `GET /api/exports/readings.csv`

Persisted reading CSV. Historical exports scope to cycle/hours.

### `GET /api/exports/events.csv`

Operational event CSV. Historical exports scope to cycle/hours.

## 3.9 Socket.IO broadcast layer

`server/sockets/broadcaster.py` never creates events itself. It is a pure
emit helper:

- `broadcast_telemetry(record, payload)` emits `telemetry_update` to
  `room=line:{line_id}`.
- `broadcast_operational_events(record)` emits `operational_event` to each
  consumer room in the record.

`server/sockets/socket_events.py` validates `join_line` and `leave_line`.
Only `line30` is permitted, and it builds the room name
`line:{line_id}`.

`server/mqtt/message_handler.py` calls these helpers after a successful
persist, so live events always follow a successful database write.

## 3.10 Configuration and environment

`server/config.py` validates required configuration at import time. It
refuses to start with an invalid `DATABASE_URL`, missing MQTT details, or an
empty MQTT topic. The backend therefore fails fast instead of starting with a
misconfigured database or MQTT broker.

## 3.11 Design decisions

- **Flask for request/response, Flask-SocketIO for bidirectional streaming**:
  REST handles historical and export work; Socket.IO handles live events.
- **Line-scoped rooms**: `join_room(line:line30)` isolates live broadcasts per
  viewer line.
- **No worker queue**: the single process is enough for this load profile.
  Meant use may require splitting label/publish/broadcast later.
- **Idempotent inserts**: message identity is `(replay_cycle_id,
  message_id)`, so duplicates do not create duplicate readings.
