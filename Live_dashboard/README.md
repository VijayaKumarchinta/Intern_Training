# Line_Speed_30 IIoT Platform — Architecture & Implementation Blueprint

**Project:** Line Speed 30 — Live Industrial Monitoring Dashboard  
**Architecture:** MQTT-driven, event-driven IIoT platform  
**Frontend:** Vue 3, Pinia, ECharts  
**Backend:** Python, Flask, SQLAlchemy  
**Database:** PostgreSQL  
**Messaging:** Eclipse Mosquitto, Paho MQTT  
**Realtime Transport:** WebSockets  
**Deployment Model:** Single application process for the initial deployment

---

# 1. Project Objective

Build a production-oriented IIoT monitoring platform for Line Speed 30.

The platform receives industrial telemetry through MQTT, validates and persists incoming measurements in PostgreSQL, evaluates alarm conditions, and broadcasts committed updates to connected Vue dashboards through WebSockets.

The frontend must reproduce the functionality and visual direction of the supplied HTML dashboard.

### Core requirements

1. MQTT is the ingestion boundary.
2. PostgreSQL is the persistent source of truth.
3. Telemetry is stored in a normalized relational structure.
4. Every valid MQTT message is processed individually.
5. Database persistence happens before WebSocket broadcasting.
6. WebSocket updates drive the dashboard without polling.
7. Replay controls operate bidirectionally.
8. Historical data is retrieved through HTTP.
9. Alarms and events are independently represented.
10. The frontend provides live monitoring, historical analysis and operational controls.

### Data flow

Excel replay fixture → Python replay publisher → Mosquitto broker → Paho subscriber → Validation → Alarm evaluation → PostgreSQL transaction → WebSocket broadcast → Vue dashboard.

**Important:** Excel is a testing fixture. It is not the production data source, and the dashboard never reads Excel directly.

---

# 2. Frontend Reference — Dashboard Structure

The supplied HTML dashboard is the authoritative visual reference.

The Vue implementation must preserve its information hierarchy and operator workflow.

## 2.1 Application layout

The dashboard consists of six major regions.

### A. Application header

Contains:

- PLANTVIEW branding
- Machine/project breadcrumb
- Replay connection status
- Refresh interval indicator
- Current source timestamp
- Received readings / total readings

Example:

`PLANTVIEW | Line_Speed_30 > Process Overview`

`Replay running (simulated) | Refresh 5 s | Source time 12:10:13 | Readings 3/2139`

### B. Dashboard toolbar

Contains:

- Dataset date and source time range
- Pause / Resume button
- Replay speed selector
- Historical window selector
- CSV export button

Replay speed options:

- 1× (5 seconds)
- Additional configured speeds

Historical window options:

- Live
- 15 minutes
- 30 minutes
- 45 minutes
- Full run

The historical window is a viewing control, not a replay-speed control.

### C. KPI row — six cards

| KPI | Signal | Display |
| --- | --- | --- |
| Oil Temperature | Burner PV / oil temperature | Value + °C |
| Delta T | Temperature differential | Value + °C |
| Burner Load | Burner load | Value + % |
| Moisture | Moisture PV | Value + unit |
| Paddle Speed | Paddle speed | Value + unit |
| Oil Level | Oil level | Value + unit |

Each card includes:

- Signal label
- Current measurement
- Unit
- Mini sparkline
- Alarm/normal status
- Observed minimum and maximum

The cards must be driven by the signal metadata and latest telemetry state.

No hardcoded dashboard values.

### D. Chart navigation — five views

1. Delta T
2. Delta T vs Burner SP
3. Delta T vs Oil Level
4. Burner Load
5. Moisture

Each navigation item selects a chart configuration.

The chart panel contains:

- Chart title
- Dataset annotation
- Operator note, where available
- ECharts visualization
- Time axis
- Signal legend
- Current value
- Change from previous sample
- Expandable chart data table

### E. Operational panels

Two side-by-side panels:

**Active Alarms**

- Severity
- Alarm message
- Timestamp
- Acknowledgement state
- Operator acknowledgement action

**Event History — Real-time**

- Event timestamp
- Event description
- Severity/category
- Live indicator

Events include:

- Live stream started
- Alarm raised
- Alarm cleared
- Alarm acknowledged
- Replay paused
- Replay resumed
- Replay speed changed
- Connection state changes

### F. Historical and statistical panels

**Historical Readings**

Columns:

- Timestamp
- Burner PV
- Delta T
- Oil Level
- Stack Temperature
- Moisture
- Paddle Speed
- XV6601
- Status

The table supports the selected historical window and pagination or bounded record limits.

**Statistics**

Columns:

- Signal
- Minimum
- Average
- Maximum
- Out-of-limit count/status

Statistics must be calculated from actual persisted readings and applicable signal limits.

---

# 3. Frontend Architecture — Vue 3

## 3.1 Component hierarchy

App.vue is the application composition root.

It should coordinate the page-level state and layout without implementing chart calculations, socket management, or business logic directly.

```text
App.vue
│
├── AppBar.vue
│   ├── Brand
│   ├── Breadcrumb
│   ├── ConnectionIndicator
│   ├── SourceClock
│   └── ReadingCounter
│
├── DashboardToolbar.vue
│   ├── DatasetRange
│   ├── ReplayControls
│   │   ├── PauseResumeButton
│   │   └── ReplaySpeedSelect
│   ├── HistoryWindowSelect
│   └── ExportButton
│
├── KpiRow.vue
│   └── KpiCard.vue × 6
│       └── Sparkline.vue
│
├── ChartNav.vue
│   └── ChartNavItem.vue × 5
│
├── ChartPanel.vue
│   ├── ChartHeader
│   ├── EChartsCanvas
│   ├── CurrentValue
│   ├── ValueDelta
│   └── ChartDataTable
│
├── OperationsGrid.vue
│   ├── AlarmsTable.vue
│   └── EventFeed.vue
│
└── AnalyticsGrid.vue
    ├── HistoryTable.vue
    └── StatsTable.vue
```

## 3.2 Composables — seven responsibilities

| Composable | Responsibility | Main exports |
| --- | --- | --- |
| `useTelemetrySocket.js` | WebSocket connection, authentication, telemetry reception and reconnection | `connected`, `latest`, `connect()`, `disconnect()` |
| `useControlSocket.js` | Send replay/alarm commands and correlate acknowledgements | `sendCommand()`, `pendingCommands`, `lastAck` |
| `useAnimatedValue.js` | Animate KPI value transitions | `animatedValue`, `updateValue()` |
| `useHistoryWindow.js` | Load historical readings for the selected window | `data`, `loading`, `refresh()` |
| `useChartOptions.js` | Construct ECharts configurations from telemetry | `option`, `updateChart()` |
| `useSparkline.js` | Maintain and render individual KPI sparklines | `render()`, `sparklineRef` |
| `useFormatters.js` | Shared time, number, unit and delta formatting | `hms()`, `fmt()`, `delta()` |

## 3.3 Pinia stores

Use Pinia for shared application state.

```text
stores/
├── telemetryStore.js
├── replayStore.js
├── alarmStore.js
├── eventStore.js
└── dashboardStore.js
```

Responsibilities:

- `telemetryStore`: latest frame, signal values and connection state.
- `replayStore`: running/paused state, speed and replay progress.
- `alarmStore`: active alarms and acknowledgement state.
- `eventStore`: bounded real-time event history.
- `dashboardStore`: selected chart and historical window.

Do not duplicate the same telemetry state across components.

## 3.4 Seven mandatory visual activity patterns

1. **Animated KPI values:** all six cards transition when new measurements arrive.
2. **Connection pulse:** the connection indicator reacts to successfully received telemetry frames.
3. **Local clock ticker:** the header clock updates independently of network activity.
4. **Chart transitions:** ECharts uses `animationDurationUpdate: 500`.
5. **Fresh-row highlighting:** newly received history rows receive a temporary visual highlight.
6. **Explicit connection status:** show Live, Reconnecting, Disconnected or Stale.
7. **Live sparklines:** each KPI sparkline redraws as new measurements arrive.

A local clock changing does not mean telemetry is healthy. The UI must separately track the timestamp of the last successfully received frame.

---

# 4. Frontend Design System

The supplied HTML uses a light industrial monitoring interface.

Preserve that direction rather than introducing an unrelated dark dashboard.

### Visual characteristics

- Light grey application background
- White content panels
- Dark navy application header
- Blue primary interaction color
- Dark navy text
- Subtle panel borders and shadows
- Compact industrial typography
- Clear table separators
- Consistent spacing
- Minimal decorative elements

### Status colors

| Status | Meaning | Visual treatment |
| --- | --- | --- |
| Green | Normal / connected | Green indicator |
| Amber | Warning | Amber indicator |
| Red | Critical / out of range | Red indicator |
| Grey | No limit / unavailable | Neutral indicator |
| Blue | Active selection / interaction | Blue accent |

### Layout principles

- Six KPI cards across wide desktop screens.
- Five chart navigation items across the chart toolbar.
- Two-column alarm/event layout.
- History and statistics panels arranged according to available width.
- Responsive layouts for smaller screens.
- Tables must remain readable without excessive horizontal compression.
- Avoid unnecessary gradients, oversized typography and decorative cards.

The HTML screenshot is the visual baseline. Vue should improve maintainability and responsiveness without changing the established information architecture.

---

# 5. Frontend Data Loading Strategy

HTTP is responsible for initial data and historical queries.

WebSocket is responsible for live updates and operational commands.

## Initial page load

The frontend makes four initial HTTP requests, which can run concurrently.

| Endpoint | Purpose |
| --- | --- |
| `GET /api/v1/history?window=full&limit=5000` | Initial chart and historical readings |
| `GET /api/v1/stats` | Initial statistics |
| `GET /api/v1/manifest` | Dataset information and reading count |
| `GET /api/v1/alarms?active=true` | Initial active alarm list |

After initial loading:

- No periodic HTTP polling for telemetry.
- No periodic HTTP polling for statistics.
- No periodic HTTP polling for alarm updates.
- Live updates arrive through WebSocket.

A historical-window selection triggers a new HTTP history request.

CSV export is an explicit HTTP operation.

The external monitoring system may call `/health` periodically. That is independent of frontend telemetry polling.

---

# 6. WebSocket Architecture

Endpoint:

`WS /ws/v1`

One bidirectional WebSocket channel handles:

- Live telemetry
- Alarm updates
- Event updates
- Replay state synchronization
- Operator commands
- Command acknowledgements

## 6.1 Server → Client

| Frame | Purpose |
| --- | --- |
| `latest` | New committed telemetry |
| `alarm.raised` | New alarm occurrence |
| `alarm.cleared` | Alarm returned to normal |
| `alarm.acked` | Alarm acknowledgement |
| `event.created` | New event history item |
| `replay.state` | Shared replay state |
| `ack` | Command acknowledgement |
| `error` | Command/protocol failure |
| `session.expired` | Authentication/session expiration |

Example telemetry frame:

```json
{
  "type": "latest",
  "machine_code": "LINE_SPEED_30",
  "ts": "2026-04-17T12:10:13Z",
  "seq": 3,
  "values": {
    "oil_temperature": 184.1,
    "delta_t": 25.3,
    "burner_load": 87.7,
    "moisture": 1.355,
    "paddle_speed": 63.1,
    "oil_level": 177.2
  },
  "status": "warn"
}
```

The values shown above are illustrative. Actual field names and units must follow the dataset's signal catalog.

## 6.2 Client → Server

| Command | Purpose |
| --- | --- |
| `replay.start` | Start or resume replay |
| `replay.pause` | Pause replay |
| `replay.speed` | Change replay speed |
| `replay.reset` | Reset replay position |
| `alarm.ack` | Acknowledge an alarm |

Example:

```json
{
  "type": "replay.speed",
  "command_id": "01JEXAMPLEULID",
  "speed": 2
}
```

Every command receives an acknowledgement carrying the same `command_id`.

The server must validate commands, handle invalid input and avoid applying duplicate commands.

Acknowledgement must be generated only after the requested operation has been successfully applied or rejected.

**Important:** Replay control must reach the actual replay publisher through a defined control mechanism. Updating a Vue variable or backend state alone does not pause or accelerate an independent simulator process.

For the initial single-process design, the replay service can coordinate the publisher through an in-process control interface. If the simulator becomes an independent process, use a dedicated MQTT control topic or another explicitly defined inter-process command channel.

---

# 7. Backend Architecture — Flask

The backend has five responsibilities:

1. HTTP API
2. WebSocket communication
3. MQTT telemetry ingestion
4. Business rules and alarm processing
5. PostgreSQL persistence

## 7.1 Flask application factory

`api/app.py`

Responsibilities:

- Create Flask application.
- Load configuration.
- Initialize SQLAlchemy.
- Register HTTP blueprints.
- Register WebSocket route.
- Configure error handlers.
- Initialize logging.
- Start the MQTT subscriber through a controlled application lifecycle.

Do not start MQTT background workers during module imports.

Use an explicit startup/shutdown lifecycle to avoid duplicate subscriber connections when the application is imported more than once.

## 7.2 API routes

| Route | Responsibility |
| --- | --- |
| `health.py` | Database, broker and telemetry health |
| `history.py` | Historical telemetry queries |
| `stats.py` | Statistical calculations |
| `manifest.py` | Dataset and replay metadata |
| `alarms.py` | Active and historical alarms |
| `export.py` | CSV export |

Routes must remain thin.

No SQL statements or business rules should be embedded in route handlers.

## 7.3 Services

| Service | Responsibility |
| --- | --- |
| `validation.py` | Validate MQTT payload structure and signal values |
| `alarm_engine.py` | Evaluate limits, debounce and alarm transitions |
| `command_validation.py` | Validate incoming WebSocket commands |
| `replay_service.py` | Manage replay state and publisher controls |
| `alarm_service.py` | Acknowledge and manage alarm occurrences |
| `event_service.py` | Create operational event records |

Services should not import Flask or directly execute SQL.

Use dependency injection or explicit service interfaces to access repositories.

## 7.4 Repositories

| Repository | Responsibility |
| --- | --- |
| `readings_repo.py` | Insert samples, values, retrieve latest/history and statistics |
| `alarms_repo.py` | Create, clear, acknowledge and retrieve alarms |
| `limits_repo.py` | Retrieve active machine-specific limits |
| `machines_repo.py` | Retrieve line and machine information |
| `events_repo.py` | Persist and retrieve event history |

Repositories own SQL/SQLAlchemy persistence operations.

They must not contain HTTP response construction or WebSocket broadcasting.

## 7.5 MQTT subscriber

Processing sequence:

```text
Paho on_message
       |
       v
Decode JSON
       |
       v
Validate message
       |
       v
Resolve machine and signal definitions
       |
       v
Begin database transaction
       |
       v
Insert telemetry sample
       |
       v
Insert individual signal values
       |
       v
Update latest-sample pointer
       |
       v
Evaluate alarm transitions
       |
       v
Persist alarm/event changes
       |
       v
Commit transaction
       |
       v
Broadcast committed updates
```

One message is processed at a time.

No bulk insertion, custom buffer thread or delayed batch processing in the initial design.

A failed database transaction must never produce a successful telemetry broadcast.

Invalid messages must be logged and rejected without terminating the subscriber.

---

# 8. Database Architecture — Normalized Schema

The database is organized into dimensions, telemetry facts, operational state and annotations.

The schema must accommodate additional production lines, machines and signals without adding new columns for every signal.

## 8.1 Core tables

| Group | Table | Purpose |
| --- | --- | --- |
| Dimension | `lines` | Production line master |
| Dimension | `machines` | Machine master |
| Dimension | `signal_definitions` | Signal names, labels, units and metadata |
| Configuration | `machine_signal_limits` | Machine-specific limits and effective dates |
| Fact | `telemetry_samples` | One record per incoming machine message |
| Fact | `telemetry_values` | One record per signal measurement |
| Cache | `telemetry_latest` | Latest sample pointer for each machine |
| Operations | `alarms` | Alarm occurrences and acknowledgement state |
| Operations | `event_log` | Operational and alarm event history |
| Annotation | `operator_notes` | Dataset and operator annotations |

This is a ten-table design.

`telemetry_latest` is an intentional operational projection, not a replacement for the normalized historical facts.

## 8.2 Table responsibilities

### `lines`

One row per physical production line.

- `id`
- `code`
- `description`
- `effective_from`
- `effective_to`

### `machines`

One row per machine.

- `id`
- `code`
- `line_id`
- `effective_from`
- `effective_to`

### `signal_definitions`

Central catalog of machine signals.

- `id`
- `signal_code`
- `display_name`
- `unit`
- `data_type`
- `decimal_precision`
- `description`

Examples:

- OIL_TEMPERATURE
- DELTA_T
- BURNER_LOAD
- MOISTURE
- PADDLE_SPEED
- OIL_LEVEL
- STACK_TEMPERATURE
- XV6601

### `machine_signal_limits`

Defines machine-specific operational limits.

- `id`
- `machine_id`
- `signal_id`
- `warning_min`
- `warning_max`
- `critical_min`
- `critical_max`
- `effective_from`
- `effective_to`

The applicable limit is determined using the machine, signal and effective timestamp.

Do not store the limit repeatedly in each telemetry record.

### `telemetry_samples`

One row per incoming MQTT telemetry message.

- `machine_id`
- `ts`
- `seq`
- `schema_version`
- `received_at`
- `status`

Composite primary key:

`(machine_id, ts)`

Partition by timestamp when data volume justifies it.

### `telemetry_values`

One row per signal measurement belonging to a telemetry sample.

- `machine_id`
- `ts`
- `signal_id`
- `value`

Composite primary key:

`(machine_id, ts, signal_id)`

Composite foreign key:

`(machine_id, ts) → telemetry_samples`

This is the canonical normalized signal-value storage.

### `telemetry_latest`

One row per machine.

- `machine_id`
- `ts`

This table points to the latest persisted sample.

Retrieve the latest sample's signal values by joining `telemetry_samples` and `telemetry_values`.

### `alarms`

One row per alarm occurrence.

- `id`
- `machine_id`
- `signal_id`
- `opened_at`
- `cleared_at`
- `observed_value`
- `severity`
- `state`
- `acknowledged_by`
- `acknowledged_at`
- `comment`

### `event_log`

Append-only operational event history.

- `id`
- `machine_id`
- `alarm_id`
- `event_type`
- `severity`
- `message`
- `occurred_at`
- `metadata`

### `operator_notes`

Stores the source workbook's annotations and operator notes.

- `id`
- `section_name`
- `note_text`
- `created_at`

## 8.3 Normalization rules

1. Machine identity exists in `machines`, not duplicated in telemetry rows.
2. Signal definitions and units exist in `signal_definitions`.
3. Machine-specific alarm limits exist in `machine_signal_limits`.
4. Historical readings exist in `telemetry_samples` and `telemetry_values`.
5. Latest-state lookup uses a separate pointer table.
6. Alarm occurrences are separate from raw telemetry.
7. Event history is separate from current alarm state.

## 8.4 Operational database guarantees

| Guarantee | Implementation |
| --- | --- |
| Duplicate protection | Unique sample key and `ON CONFLICT DO NOTHING` |
| Consistent telemetry | Sample and signal values inserted in one transaction |
| Latest-state consistency | Latest pointer updated in the same transaction |
| No uncommitted broadcast | WebSocket broadcast only after commit |
| Machine expansion | Add dimension records, not new telemetry columns |
| Signal expansion | Add signal definitions, not schema migrations |
| Historical retention | Time-based partitions when required |

A note on partitioning: PostgreSQL requires unique constraints on a partitioned table to include its partition key. The composite `(machine_id, ts)` key satisfies that requirement.

Weekly partitions and a default partition can be introduced as part of the operational hardening stage. Do not introduce partitioning before the actual data volume and retention requirements justify its operational cost.

---

# 9. HTTP API Contract

All endpoints use `/api/v1`.

| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/health` | GET | Operational health |
| `/history` | GET | Historical readings |
| `/stats` | GET | Aggregated signal statistics |
| `/manifest` | GET | Dataset metadata |
| `/alarms` | GET | Alarm occurrences |
| `/export` | GET | CSV download |

### Health response

```json
{
  "status": "ok",
  "database": "ok",
  "broker": "ok",
  "subscriber": "connected",
  "last_message_age_s": 5
}
```

Health must represent actual dependency states, not merely whether the Flask process is running.

### History parameters

- `window=15m`
- `window=30m`
- `window=45m`
- `window=full`
- `limit=5000`
- `machine_code=LINE_SPEED_30`

The backend must validate query parameters and impose a maximum record limit.

### Statistics response

Return minimum, maximum, average, sample count and out-of-limit information for each signal.

All aggregates must use appropriate numeric precision. Avoid integer division and unnecessary conversion of PostgreSQL numeric values into low-precision floating-point values.

---

# 10. WebSocket Hub and Deployment

## WebSocket hub

`api/ws_hub.py`

Responsibilities:

- Maintain connected clients.
- Broadcast committed frames.
- Remove disconnected clients.
- Handle connection failures.
- Serialize outbound messages consistently.

It must not execute SQL or contain alarm business rules.

## Initial deployment model

One application process:

- Flask HTTP API
- Flask-Sock WebSocket endpoint
- Paho MQTT subscriber running in a controlled background thread
- One in-process WebSocket client registry

The subscriber's Paho network loop and the WebSocket server's execution model must be compatible.

Use a WebSocket-capable deployment server. Waitress is not the appropriate server for this Flask-Sock WebSocket architecture.

A suitable initial option is Gevent with a compatible WebSocket configuration.

The single-process client registry is a deliberate initial deployment constraint.

If multiple application processes or machines are introduced later, replace the in-memory fan-out mechanism with Redis Pub/Sub or another shared event-distribution layer.

---

# 11. Error Handling and Logging

### Typed exceptions

- `ValidationError`
- `NotFoundError`
- `DuplicateError`
- `DatabaseError`
- `CommandError`

### HTTP error responses

| Error | HTTP status |
| --- | --- |
| Invalid query/payload | 400 |
| Resource not found | 404 |
| Duplicate operation | Idempotent response |
| Authentication failure | 401/403 |
| Database failure | 500 |

MQTT validation failures are not HTTP responses. They must be logged and rejected at the ingestion boundary.

### Logging requirements

- Structured JSON logging
- UTC timestamps
- Correlation/message identifiers
- Machine code
- MQTT topic
- Validation failure reason
- Database transaction outcome
- WebSocket delivery failures
- Command IDs
- Subscriber connection state

Never log authentication tokens or secrets.

---

# 12. Project Folder Structure

```text
line-speed-30-iiot/
│
├── .env
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DATABASE.md
│   ├── API.md
│   ├── WEBSOCKET.md
│   ├── FRONTEND.md
│   ├── OPERATIONS.md
│   └── DECISIONS.md
│
├── scripts/
│   ├── init_db.py
│   ├── create_partitions.py
│   └── inspect_dataset.py
│
├── simulator/
│   ├── __init__.py
│   ├── replay.py
│   ├── publisher.py
│   └── replay_controller.py
│
├── api/
│   ├── __init__.py
│   ├── app.py
│   ├── config.py
│   ├── db.py
│   ├── errors.py
│   ├── logging_config.py
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── health.py
│   │   ├── history.py
│   │   ├── stats.py
│   │   ├── manifest.py
│   │   ├── alarms.py
│   │   └── export.py
│   │
│   ├── realtime/
│   │   ├── __init__.py
│   │   ├── ws.py
│   │   └── ws_hub.py
│   │
│   ├── subscriber/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   └── handlers.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── validation.py
│   │   ├── alarm_engine.py
│   │   ├── alarm_service.py
│   │   ├── command_validation.py
│   │   ├── replay_service.py
│   │   └── event_service.py
│   │
│   └── repositories/
│       ├── __init__.py
│       ├── readings_repo.py
│       ├── machines_repo.py
│       ├── limits_repo.py
│       ├── alarms_repo.py
│       └── events_repo.py
│
├── app/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   │
│   └── src/
│       ├── main.js
│       ├── App.vue
│       │
│       ├── components/
│       │   ├── layout/
│       │   │   ├── AppBar.vue
│       │   │   └── DashboardToolbar.vue
│       │   │
│       │   ├── kpi/
│       │   │   ├── KpiRow.vue
│       │   │   ├── KpiCard.vue
│       │   │   └── Sparkline.vue
│       │   │
│       │   ├── charts/
│       │   │   ├── ChartNav.vue
│       │   │   ├── ChartPanel.vue
│       │   │   └── ChartDataTable.vue
│       │   │
│       │   ├── operations/
│       │   │   ├── AlarmsTable.vue
│       │   │   └── EventFeed.vue
│       │   │
│       │   └── analytics/
│       │       ├── HistoryTable.vue
│       │       └── StatsTable.vue
│       │
│       ├── composables/
│       │   ├── useTelemetrySocket.js
│       │   ├── useControlSocket.js
│       │   ├── useAnimatedValue.js
│       │   ├── useHistoryWindow.js
│       │   ├── useChartOptions.js
│       │   ├── useSparkline.js
│       │   └── useFormatters.js
│       │
│       ├── stores/
│       │   ├── telemetryStore.js
│       │   ├── replayStore.js
│       │   ├── alarmStore.js
│       │   ├── eventStore.js
│       │   └── dashboardStore.js
│       │
│       ├── services/
│       │   ├── api.js
│       │   └── websocket.js
│       │
│       ├── config/
│       │   ├── signals.js
│       │   └── charts.js
│       │
│       └── styles/
│           ├── App.css
│           ├── variables.css
│           └── components.css
│
├── tests/
│   ├── unit/
│   │   ├── test_validator.py
│   │   ├── test_alarm_engine.py
│   │   └── test_repositories.py
│   │
│   ├── integration/
│   │   ├── test_subscriber.py
│   │   ├── test_api.py
│   │   ├── test_ws_handshake.py
│   │   ├── test_ws_commands.py
│   │   ├── test_ws_broadcast.py
│   │   └── test_reconnect.py
│   │
│   └── conftest.py
│
└── deploy/
    └── systemd/
        └── api.service
```

The Excel replay fixture should be stored separately from application source code, in a data directory excluded from production deployments.

There is one subscriber implementation, not two.

---

# 13. Seven-Week Implementation Sequence

| Week | Focus | Deliverable |
| --- | --- | --- |
| 1 | Database foundation | Normalized schema, SQLAlchemy connection, repositories and validation |
| 2 | HTTP API | Flask factory, history, statistics, manifest, alarms and export |
| 3 | MQTT ingestion | Mosquitto integration, Paho subscriber, replay publisher and database persistence |
| 4 | WebSocket foundation | WS connection, authentication, telemetry broadcast and reconnect |
| 5 | Frontend dashboard | Vue layout, KPI cards, charts, tables and HTML visual parity |
| 6 | Bidirectional operations | Pause/resume, speed controls, alarm acknowledgement and command synchronization |
| 7 | Production hardening | Logging, monitoring, partitions where justified, testing and deployment |

### Completion criteria

**Week 1:** Telemetry can be persisted using the normalized database design.

**Week 2:** HTTP endpoints return correct historical and statistical data.

**Week 3:** MQTT messages reach PostgreSQL through the subscriber.

**Week 4:** Connected clients receive committed telemetry over WebSockets.

**Week 5:** The Vue dashboard reproduces the supplied HTML layout and responds to real telemetry.

**Week 6:** Dashboard controls operate the actual replay process and synchronize across clients.

**Week 7:** The system handles reconnects, invalid payloads, database failures, logging and operational restarts.

---

# 14. Architecture Rules — Do Not Violate

1. MQTT is the ingestion boundary.
2. PostgreSQL is the historical source of truth.
3. Excel must never become a dashboard data source.
4. Every incoming telemetry message is processed individually.
5. Persist before broadcasting.
6. No frontend telemetry polling.
7. No SQL inside Flask route handlers.
8. No database access inside WebSocket hub code.
9. No Flask dependencies inside business-rule services.
10. No duplicated signal-limit configuration.
11. No hardcoded KPI values in Vue components.
12. No duplicate MQTT subscriber implementations.
13. No independent replay state in individual browser components.
14. No multiple application workers with an in-memory-only WebSocket registry.
15. Do not introduce Redis, Kafka or additional infrastructure until a real architectural requirement justifies it.

---

# Final Architecture Principle

The application is an event-driven IIoT monitoring platform.

The database preserves the telemetry history, the backend enforces the operational rules, MQTT transports incoming machine data, WebSockets distribute committed state, and Vue presents that state to the operator.

The supplied HTML dashboard defines the operator experience. Every frontend component, backend endpoint and database query must have a clear purpose in supporting that experience.

````Websockets````

- Which enables a real-time communication b/w clients and servers
- This allows continuous exchange in bi-directional
- which helps in creating
  - efficient and low-latency systems that handles the real time updates
- unlike http req/res models websockets allows persistent connection after an initial handshake, which allows continuous data-exchange
- which mainly benefits in real-time distributed systems

```Architecture```

- ``client/server communication``:
  - Initial handshake:
    - connection begins with an http-based handshake
  - persistent connection:
    - once the handshake is completed a communication channel is established and will stay there uas long as we needed
  - Bi-directional messaging:
    - after connection is established both client and server can send/receive msg at anytime

- ``Components``:
  - Clients:
    - devices,browsers/applications that needed real-time updates
  - Websocket server:
    - This will manage multiple Websocket connections from various clients
  - Backend services:
    - here these services helps to 
      - process, analyze or store the data before responding back to the client
  - Message broker:
    - for scaling these uses across multiple servers often us msg brokers

- ``Real-time data Synchronization``:
  - BroadCasting:
    - where a msg is sent to all connected clients we sue this because websocket servers often needs to send the same msg to multiple clients simultaneously
  - Event-Driven
    - Websockets-based systems usually handle the incoming msgs through event-driven architecture where it triggers specific-events on the server, then will processes the data and send updates to  other clients services

- ``Message Routing and distributions``
  - Message queuing and brokers:
    - websocket-servers need a medium to communicate instead of direct communication that when brokers took place which allows us to communicate to the appropriate servers

## Flow

Publisher(reads the excel rows and build json payload and publish to mqtt) -> subscriber(on_msg decodes the json and will drop whenever we encounter a bad json, then sub will continue) -> Validation(checks the structure, codes and everything) -> Resolution(Maps every related things) -> Transactions(Insert data row by row into the real telemetry tables through mqtt) -> Alarm engine(loads the limited row that validates at that ts for each and compare the values) -> commit(if anything fails, the transaction rolls back) -> broadcast(where the events will helps to send updates where it applicable to every client) -> Browser on each msg telemetrystore will helps to updates the frontend dashboard