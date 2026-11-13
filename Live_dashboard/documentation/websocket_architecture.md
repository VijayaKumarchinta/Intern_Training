# 4. WebSocket Architecture and Live Streaming Role

## 4.1 Purpose

This document describes how WebSocket / Socket.IO is used as the live-stream
channel for the PlantView dashboard, from MQTT ingest to the browser chart.

## 4.2 Protocol summary

The frontend does not use bare WebSocket with hand-rolled messages. It uses
the Socket.IO protocol, which adds frames, rooms, acknowledgments, and
reconnection handling on top of WebSocket. In this codebase, the transport is
forced to:

```js
transports: ["websocket"]
```

The backend side is Flask-SocketIO with `async_mode="threading"`.

## 4.3 Component map

```text
MQTT broker
  -> publisher/subscriber -> on_message()
  -> save_telemetry()
  -> broadcast_telemetry(record, payload)
  -> broadcast_operational_events(record)
  -> Socket.IO emit
  -> WebSocket / Socket.IO framing
  -> telemetrySocket (Vue) / socketio endpoint (server)
```

## 4.4 Room model

The backend uses a single logical room per line:

```text
room = line:line30
```

`join_line` emits `{ line_id: "line30" }`. On success the server calls
`join_room("line:line30")`. Only then do live events arrive.

This gives the dashboard an isolation model:

| Subscriber state | Receives live events |
| --- | --- |
| connected, joined the line room | Yes |
| connected, not yet joined | No |
| disconnected | No |
| viewing a different line | No |

## 4.5 Live event types

The Socket.IO stream sends two named channels:

### `telemetry_update`

Framed payload fields:

```json
{
  "id": 123,
  "message_id": "abc",
  "replay_session_id": "...",
  "replay_cycle_id": "...",
  "replay_cycle_number": 42,
  "line_id": "line30",
  "event_ts": "2026-11-13T10:21:00",
  "received_at": "2026-11-13T10:21:01+00:00",
  "payload": { "Burner PV": 42.5, "DeltaT": 6.2, ... }
}
```

`telemetryStore.js` receives this on `telemetry_update`, filters by
`line_id` and `activeView`, and queues the record in `pendingTelemetry`.

### `operational_event`

Framed payload is the raw alarm/operational event. The store filters by
`line_id` and `activeView`, and accepts only events with a valid `id`.

## 4.6 Client-side live streaming flow

```text
App.vue -> telemetryStore.initialize()
  -> telemetrySocket.connect()
  -> on("connect"):
        emit join_line
        -> server joins line:line30
  -> on("disconnect"):
        socketStatus = reconnecting
  -> on("connect_error"):
        socketStatus = reconnecting
        store error = message
  -> on("telemetry_update"):
        handleTelemetryUpdate
        -> queue only if activeView === "overview"
  -> on("operational_event"):
        handleOperationalEvent
        -> queue only if activeView === "history"
```

The store does not merge every incoming packet directly. It aggregates into
pending arrays, then flushes them in one pass. That prevents a fast MQTT
stream from causing many tiny state updates and many small re-renders.

During live ingestion:

```text
flushPendingUpdates()
  -> mergeRecords(telemetryBatch, { live: true })
  -> merge event batch
```

Live records specifically:

1. Keep only records belonging to the current cycle.
2. Deduplicate by `replay_cycle_id:message_id`.
3. Keep the newest `HISTORY_LIMIT` (500) records.
4. Update `latestReading`.

## 4.7 Server-side live streaming flow

```text
paho.mqtt subscriber receives a new MQTT payload
  -> on_message()
  -> validate and save_telemetry()
  -> if save succeeded and record is not a duplicate:
        ack MQTT
        broadcast_telemetry(record, payload)
        broadcast_operational_events(record)
```

Missing or failed persistence:

| Failure | Behavior |
| --- | --- |
| Invalid JSON / malformed UTF-8 | Acknowledge, log, discard |
| Invalid payload structure | Acknowledge, log, discard |
| Database insert is a duplicate | Acknowledge, log, ignore |
| Database persistence failure | Do not acknowledge; retry |
| Broadcast failure | Log warning; do not block the MQTT acknowledgement |

## 4.8 Why WebSocket matters here

The dashboard has three data needs:

1. Live process values — every ~1 second, but reactive only on change.
2. Historical tables — loaded explicitly from REST.
3. Exports — one-shot downloads.

Continuous HTTP polling would work but adds unnecessary request overhead,
larger payloads on repeat, and no subscription semantics. Socket.IO provides:

- **Subscription** to only the relevant line and view.
- **Reconnection** with exponential back-off and unlimited attempts.
- **Frame routing** through named events instead of optimistic GET endpoints.
- **Room filtering** so update traffic stays scoped to the connected line.
- **Auto-connect-off and manual join** so the dashboard opens the stream only
  when the user is on the process page and deliberately connects.

## 4.9 Live streaming state machine

```text
disconnected
  -> connecting
  -> connected (joined line room)
       -> real-time telemetry + events
  -> disconnecting
  -> reconnecting (connection failure or deliberate stop)
```

The overview view is the only place live events are merged. The history view
continues to receive events but discards them; it refreshes data explicitly
through HTTP endpoints.

## 4.10 Scaling considerations

The current socket layer broadcasts to global room listeners but routes
clients only by `line_id`. A larger deployment would consider:

- A shared Socket.IO adapter so multiple server processes stay in sync.
- A Redis adapter for horizontal scaling and sticky sessions.
- Authentication tokens in `join_line` before joining a line room.
- Rate limiting on the MQTT broker for high-frequency producers.
- Backpressure in the store if the MQTT rate exceeds the UI refresh path.
- Audit filtering for `operational_event` so clients only see relevant
  severity states.
