# 1. End-to-End Application Flow

## 1.1 Purpose

This document describes the complete flow of the PlantView Line 30 dashboard
from startup to live monitoring, historical drill-down, exports, and shutdown.

## 1.2 Runtime order

1. PostgreSQL is up and the schema from `db/schema.sql` has been applied.
2. The MQTT broker is reachable at `MQTT_HOST:MQTT_PORT` (`127.0.0.1:1883`
   by default).
3. The backend entrypoint `server/run.py` is executed. It starts the MQTT
   subscriber, then runs Flask + Flask-SocketIO on port 8000.
4. The frontend development server (`vite`) starts on port 5173.
5. The browser loads `index.html` -> `main.js` -> `App.vue` ->
   `telemetryStore.js`. The store connects its Socket.IO client and, on mount,
   calls `initialize()`.
6. `initialize()` first performs `loadHealth()` and `loadHistory()`, then
   starts a 5-second auto-refresh interval.

## 1.3 Telemetry ingestion path

1. A source system pushes a JSON telemetry payload to MQTT topic
   `factory/line30/telemetry` (QoS 1).
2. `server/mqtt/subscriber.py` creates a paho.mqtt client, connects, subscribes
   to that topic, and starts `loop_start()`.
3. `server/mqtt/message_handler.py` receives the message. It decodes UTF-8,
   parses JSON, validates the payload, and saves it.
4. `server/repositories/telemetry_repository.py.save_telemetry()` inserts the
   reading into `telemetry.readings`, writes one or more alarm events into
   `telemetry.events`, and updates `telemetry.alarm_state`.
5. If the insert is new, the handler acknowledges the MQTT message and emits
   the record over Socket.IO in the `line:line30` room.

## 1.4 Live dashboard path

1. `frontend/src/services/socket.js` creates a Socket.IO client against
   `VITE_SOCKET_URL` (default `http://127.0.0.1:8000`) with
   `transports: ["websocket"]` and auto-connect disabled.
2. `telemetryStore.js` subscribes to:

| Client event | Handler | Effect |
| --- | --- | --- |
| `connect` | `handleSocketConnect` | sets socket status to `connected` and emits `join_line` |
| `disconnect` | `handleSocketDisconnect` | sets status to `reconnecting` |
| `connect_error` | `handleSocketConnectError` | sets status to `reconnecting` and stores the error |
| `telemetry_update` | `handleTelemetryUpdate` | queues the record for live merge |
| `operational_event` | `handleOperationalEvent` | queues the event for the history view |

3. `join_line` sends `{ line_id: "line30" }` and, on success, the server
   calls `join_room("line:line30")`.
4. The server broadcasts live telemetry and operational events only to socket
   clients in the matching line room, so viewers for other lines are not
   affected.

## 1.5 REST API path

The dashboard also loads initial history from HTTP endpoints:

| Endpoint | Controller | Purpose |
| --- | --- | --- |
| `GET /api/health` | `server/api/health_routes.py` | database and MQTT connectivity check |
| `GET /api/telemetry/latest` | `server/api/telemetry_routes.py` | newest reading for a line |
| `GET /api/telemetry/history` | `server/api/telemetry_routes.py` | paginated telemetry history |
| `GET /api/telemetry/statistics` | `server/api/telemetry_routes.py` | min/max/avg for one field |
| `GET /api/summary/hourly` | `server/api/summary_routes.py` | hourly buckets for a cycle |
| `GET /api/events` | `server/api/event_routes.py` | operational/alarm event history |
| `GET /api/history/cycles` | `server/api/replay_routes.py` | replay-cycle completion classification |
| `GET /api/exports/hourly-summary.csv` | `server/api/export_routes.py` | CSV export of the hourly summary |
| `GET /api/exports/readings.csv` | `server/api/export_routes.py` | CSV export of persisted readings |
| `GET /api/exports/events.csv` | `server/api/export_routes.py` | CSV export of operational events |

## 1.6 Historical drill-down path

1. The history view calls `GET /api/history/cycles` and shows the
   `COMPLETED`, `INCOMPLETE`, and legacy `UNKNOWN` cycles.
2. Selecting a cycle calls `GET /api/summary/hourly` scoped to that cycle.
3. Selecting an hourly row calls:
   - `GET /api/summary/hourly?cycle_id=...&hour_start=...`
   - `GET /api/telemetry/history?cycle_id=...&start=...&end=...`
   - `GET /api/events?cycle_id=...&start=...&end=...`

All three responses are rendered in `HourlySummaryView.vue`.

## 1.7 CSV export path

1. The user triggers a download from the configured export button.
2. `telemetryApi.downloadReadings()` / `downloadEvents()` /
   `downloadHourlySummary()` calls `downloadCsv()`.
3. The client fetches the CSV endpoint, creates a Blob, generates a temporary
   `<a download>`, clicks it, and revokes the object URL.

## 1.8 Refresh and view switching

- The overview view refreshes every 5000 ms through
  `telemetryStore.refreshDashboard()`.
- Switching to the history view calls `setActiveView("history")`, which cancels
  the overview timer, flushes pending updates, and reloads cycles, summary,
  readings, and events.
- `onBeforeUnmount` in `App.vue` calls `telemetry.stop()`, which disconnects
  Socket.IO, emits `leave_line`, and clears the refresh timer.

## 1.9 Shutdown path

1. The browser unloads and calls `telemetryStore.stop()`.
2. The Socket.IO client disconnects and leaves the line room.
3. The backend subprocess exits; `main()` stops the MQTT subscriber and lets
   `socketio.run()` tear down.

## 1.10 Data contract

The stable payload fields used by charts, KPIs, and history are defined in
`frontend/src/utils/templates.js`:

- `Burner PV`
- `DeltaT`
- `Burner Output Load`
- `Moisture PV`
- `Paddle Speed`
- `oil Level PV`

The backend stores these raw values as JSONB in `telemetry.readings.payload`.
