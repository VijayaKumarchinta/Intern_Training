# Line Speed 30 — IIoT Live Monitoring Dashboard

A real-time industrial monitoring dashboard that replays machine readings
from an Excel dataset, transports telemetry through MQTT, stores validated
readings in PostgreSQL, and displays live machine information through a
Vue.js dashboard.

The Excel file is a **simulation input only**. The dashboard and backend
read operational data from PostgreSQL and receive live updates through
WebSockets.

---

## 1. What This Project Is

- **Replay simulator** — a fixed dataset (~2,139 readings from one machine
  on 17 April 2026) is published one record at a time to an MQTT broker,
  mimicking a live telemetry feed.
- **Ingestion pipeline** — a subscriber receives each message, validates it
  against a frozen contract, deduplicates it by deterministic message
  identity, persists it to PostgreSQL and evaluates alarm thresholds,
  atomically, per message.
- **Live dashboard** — Vue 3 + Pinia + ECharts, fed by REST for bootstrap
  and history and by WebSocket for committed live updates. Database-backed
  cursors let a client recover after a disconnect without data loss.

The system is a **single-process modular monolith**: Flask, the MQTT
subscriber, the ingestion worker and the replay worker run as threads in
one Python process. Mosquitto and PostgreSQL run as separate services.
One process does not mean one thread or one database connection.

---

## 2. Technology Stack

| Layer | Technology | Responsibility |
| --- | --- | --- |
| Dataset preparation | Python, Pandas, openpyxl | Read, validate, normalize Excel; emit Parquet once |
| Replay worker | Python, Paho MQTT | Publish Parquet records with stable identity and source-timing pacing |
| Message broker | Eclipse Mosquitto | Topic-based telemetry transport with persistence |
| MQTT subscriber | Python, Paho MQTT | Receive messages, enqueue to a bounded queue, manual ACK |
| Ingestion worker | Python, SQLAlchemy | Validate, deduplicate, persist, evaluate alarms, then ACK and broadcast |
| Database | PostgreSQL | Persistent source of truth for all operational state |
| Database access | SQLAlchemy 2.x | Engine, sessions, transactions, connection pool |
| HTTP API | Flask | Bootstrap, history, stats, manifest, alarms, events, export |
| Real-time transport | Flask-Sock, WebSockets | Live updates and command channel |
| Frontend | Vue 3 | Dashboard interface |
| Frontend state | Pinia | Telemetry, alarms, events, replay state, cursor tracking |
| Charts | Apache ECharts | Time-series rendering on a 5-second scheduler |
| Configuration | python-dotenv | Load `.env` into typed `Settings` |
| Logging | Python logging | Structured logs with message_id and machine context |

Redis, Kafka, Celery and any additional services are **not** used.

---

## 3. Repository Layout

```text
Live_dashboard/
│
├── backend/
│   ├── __init__.py
│   ├── config/
│   │   └── settings.py            # typed .env loader — DONE
│   ├── contract/
│   │   ├── __init__.py
│   │   └── schema.py              # frozen TelemetryRecord — DONE
│   ├── mqtt/
│   │   ├── client.py              # paho wrapper — DONE
│   │   └── subscriber.py          # manual_ack subscriber — PENDING
│   ├── replay/
│   │   ├── worker.py              # Parquet → MQTT — PENDING
│   │   ├── window.py              # 10-min source-window selection — PENDING
│   │   └── identity.py            # deterministic message_id — PENDING
│   ├── ingestion/
│   │   ├── worker.py              # validator + enqueue — DONE
│   │   ├── consumer.py            # queue → Postgres — PENDING
│   │   └── alarms.py              # alarm evaluation — PENDING
│   ├── database/
│   │   ├── engine.py              # one engine — PENDING
│   │   ├── models.py              # 11 models — PENDING
│   │   ├── init_db.py             # schema + seeds — PENDING
│   │   └── repository.py          # queries — PENDING
│   ├── api/
│   │   ├── __init__.py            # Flask factory — PENDING
│   │   └── routes/                # REST endpoints — PENDING
│   ├── realtime/
│   │   ├── hub.py                 # WebSocket registry — PENDING
│   │   └── sync.py                # cursor recovery — PENDING
│   └── services/
│       └── lifecycle.py           # worker startup — PENDING
│
├── frontend/                      # Vue 3
│   └── src/
│       ├── api/                   # REST clients
│       ├── stores/                # Pinia
│       ├── composables/           # WebSocket, cursors
│       ├── charts/                # ECharts wrappers
│       └── views/
│
├── data/
│   ├── raw/Line_Speed_30.xlsx                       # source workbook (never modified)
│   ├── processed/line_speed_30_normalized.parquet   # DONE
│   └── reports/                                     # profiling + preprocessing reports
│
├── docs/
│   ├── contract/signal_contract.md                  # DONE
│   └── architecture/
│       ├── mqtt_topics.md                           # DONE
│       └── system_architecture.md                   # long-form design
│
├── mosquitto/mosquitto.conf       # project copy for reference
├── reference/line_speed_30_design.html
├── tools/
│   ├── profiling/profile_dataset.py        # DONE
│   ├── preprocessing/preprocess_dataset.py # DONE
│   └── smoke/
│       ├── mqtt_smoke.py          # DONE
│       ├── replay_smoke.py        # DONE (v1)
│       ├── ingestion_smoke.py     # DONE (v1)
│       ├── db_connect_smoke.py    # DONE
│       ├── db_schema_smoke.py     # PENDING
│       └── persist_smoke.py       # PENDING
│
├── tests/
│   ├── unit/
│   └── integration/
│
├── logs/
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

Files marked **DONE** are on disk and verified end to end. Files marked
**PENDING** are specified in the architecture but not yet implemented.

---

## 4. High-Level Architecture

```text
Excel Workbook
     │  imported once
     ▼
Preprocessing → data/processed/*.parquet
     │
     ▼
Replay Worker ◄── command queue ◄── Flask replay service ◄── Vue commands
     │  deterministic message_id · source-time pacing · 10-minute windows
     │  MQTT QoS 1, not retained
     ▼
Mosquitto  (factory/line30/telemetry, factory/line30/state)
     │
     ▼
Paho Subscriber (manual_ack=True, bounded queue, backpressure when full)
     │
     ▼
Ingestion Worker (single thread, one transaction per message)
     │  validate → deduplicate → stream offset → INSERT → alarms → COMMIT
     │  then ACK MQTT → broadcast to WebSocket hub
     ▼
PostgreSQL (11 tables)
     │  committed
     ▼
In-process WebSocket Hub (cursors from stream_state)
     │
     ▼
Flask-Sock (live) + Flask REST (bootstrap, history, manifest)
     │
     ▼
Vue 3 + Pinia + ECharts (5-second render scheduler)
```

**One line:** Excel → Parquet → replay worker → MQTT → subscriber → queue →
ingestion → PostgreSQL → WebSocket → Vue.

---

## 5. Key Design Decisions (Frozen)

These were settled during design review. Do not revisit them without a
specific, measured reason.

| Decision | Choice | Rationale |
| --- | --- | --- |
| Source storage | Parquet file, not Postgres | Replay source is immutable; fast to filter; no duplicate table or import pipeline |
| Database schema | **11 tables** | See Section 11 |
| Tables excluded | `replay_records`, `command_receipts`, `stream_offsets` (as a table) | Parquet is the source; command idempotency deferred to Phase 4; offsets collapse into one `stream_state` row |
| SQLAlchemy engines | **One engine**, `pool_size=5`, `max_overflow=2`, `pool_timeout=5`, `pool_pre_ping=True` | Single-user, single ingestion thread; split only if contention is measured |
| Deduplication | `UNIQUE (message_id)` on `telemetry_readings` | `message_id = sha256(dataset_id:session_id:cycle:sequence)[:32]`, stable across retries |
| Replay identity | `UNIQUE (machine_id, replay_session_id, replay_cycle, source_sequence)` | Separates a legitimate later replay from a duplicate delivery |
| Cursor source | `stream_state.last_reading_offset`, `stream_state.last_event_offset` | `MAX(reading_id)` races: `BIGSERIAL` allocates before commit, while `stream_state` increments inside the transaction |
| Timestamps | `TIMESTAMPTZ` everywhere | Portable; source zone recorded in `datasets.source_timezone` with a `timezone_assumed` flag |
| Source timezone | UTC with `timezone_assumed = true` initially | Correctable by one `UPDATE datasets` plus re-import |
| Broker topics | `factory/line30/telemetry`, `factory/line30/state` | Namespaced by domain and machine |
| MQTT QoS | 1 with `manual_ack=True` | At-least-once delivery, ACK only after commit |
| Replay timing | Derived from source timestamp deltas | Preserves original cadence, including irregular gaps |
| Frontend data | REST bootstrap + WebSocket live | No polling; charts render on a 5-second schedule |
| Latest reading | In-memory frame, no `telemetry_latest` table | Loaded from Postgres at startup; only a newer reading may replace it |

---

## 6. Prerequisites

- **Python 3.14** (environment at `F:\Intern_Training\.venv`)
- **PostgreSQL 18** on `localhost:5432`, database `line30` created
- **Mosquitto 2.1.2**, foreground broker config (see
  `docs/architecture/mqtt_topics.md`)
- **Node.js 20+** for the Vue 3 frontend (Phase 5)

Python dependencies (installed):

```text
pandas==3.0.5
pyarrow==26.0.1
openpyxl==3.1.5
python-dotenv==1.2.3
SQLAlchemy==2.1.6
psycopg2-binary==2.9.13
paho-mqtt==2.1.0
Flask            # Phase 4
flask-sock       # Phase 4
```

Confirm the installed Paho version supports the manual-ack API before
implementing the subscriber.

---

## 7. Environment Variables

`.env.example` documents every key. Copy it to `.env` and fill in real
credentials for `DATABASE_URL`. `.env` is git-ignored; `.env.example` is
committed. Secrets never appear in logs.

```dotenv
DATABASE_URL=postgresql+psycopg2://postgres:<password>@localhost:5432/line30

MQTT_HOST=127.0.0.1
MQTT_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=
MQTT_CLIENT_ID_PREFIX=live_dashboard
MQTT_KEEPALIVE_SECONDS=60

MQTT_TOPIC_TELEMETRY=factory/line30/telemetry
MQTT_TOPIC_STATE=factory/line30/state

REPLAY_INTERVAL_SECONDS=10.0
REPLAY_QUEUE_MAXSIZE=100
```

`REPLAY_INTERVAL_SECONDS` is a fallback and override for smoke tests. In
normal replay the delay between records comes from source timestamp
deltas, scaled by the replay speed.

---

## 8. Running the System

### 8.1 Start the MQTT broker

Mosquitto runs in the foreground for development. The Windows service is
installed but does not read the project config and does not bind to 1883.

```powershell
& "C:\Program Files\Mosquitto\mosquitto.exe" `
    -c "C:\Program Files\Mosquitto\mosquitto.conf" -v
```

Leave this window open. Expected output ends with
`mosquitto version 2.1.2 running`.

### 8.2 Set the Python path

```powershell
$env:PYTHONPATH = "F:\Intern_Training\Live_dashboard\backend"
```

### 8.3 Prepare the dataset (once)

```powershell
python .\tools\preprocessing\preprocess_dataset.py
```

Expected: `Records written: 2,139`, `Records rejected: 0`. Produces
`data/processed/line_speed_30_normalized.parquet`.

### 8.4 Initialize the database (once, Phase 3b)

```powershell
python .\tools\smoke\db_schema_smoke.py
```

Expected: `OK: 11 tables created. Seeds: 1 line, 1 machine, 32 signals, 1 dataset.`

### 8.5 Run the replay (Phase 2d)

```powershell
python -m replay --limit 100 --interval 0.5
```

Publishes 100 records from the first 10-minute window at 0.5 s intervals.
The broker window shows one `Received PUBLISH` per record, `r0` (not
retained), on `factory/line30/telemetry`.

### 8.6 Run the ingestion consumer (Phase 3c)

```powershell
python -m ingestion --limit 100
```

Expected: `Ingested 100 records, rejected 0. Stream offset: 100.`

### 8.7 Start the Flask API and WebSocket (Phase 4)

```powershell
python -m backend.api
```

- REST: `http://localhost:5000/api/v1/*`
- WebSocket: `ws://localhost:5000/ws/v1`

### 8.8 Start the frontend (Phase 5)

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

---

## 9. How the System Works

### Step 1 — Dataset preparation

1. Read the workbook with Pandas.
2. Clean and validate the records.
3. Convert timestamps to a consistent representation and record the
   source timezone assumption in `datasets`.
4. Sort chronologically and assign `source_sequence` (the row's position
   in the Parquet file).
5. Map workbook headers to telemetry fields.
6. Write the normalized Parquet file.

Excel is not read by Vue or by Flask at runtime. Importing the same
dataset twice must not create a second `datasets` row.

### Step 2 — Replay worker

The worker reads Parquet records one at a time, in
`(event_timestamp, source_sequence)` order, within a 10-minute source
window. For each record it builds a JSON message, adds identity and
replay metadata, publishes with QoS 1 (never retained), waits according
to the source timestamp delta, and moves on. It starts another replay
cycle when looping is enabled.

The worker connects to Mosquitto. It never connects to PostgreSQL and
never reads Excel.

**Telemetry topic:** `factory/line30/telemetry`

**Message fields**

- `message_id`: deterministic, `sha256(dataset_id:session_id:cycle:sequence)[:32]`.
- `replay_session_id`: one replay execution.
- `replay_cycle`: loop number within that execution.
- `source_sequence`: row position in the Parquet file.
- `machine_code`: machine identifier.
- `event_timestamp`: timestamp of the source reading.
- `signals`: the signal values for that reading.

A retry of the same message reuses the same `message_id`. A new replay
cycle produces a new identity, so the database can tell a legitimate
repeat in a later cycle from a duplicate delivery of an earlier message.

### Step 3 — Mosquitto

- Receives telemetry from the replay worker and delivers it to subscribers.
- Keeps the publisher independent of the database and dashboard.
- Keeps persistent session state for the subscriber.

For reliable recovery, enable Mosquitto persistence, and use a stable
subscriber client ID and persistent session. The session settings must
match the MQTT protocol version and the Paho configuration.

### Step 4 — MQTT subscriber

The subscriber connects with a stable client ID and subscribes to
`factory/line30/telemetry`. The callback does minimal work: receive the
message, capture topic, payload and delivery metadata, place it in the
bounded queue (`maxsize=100`) and return to the network loop. It never
does database work.

**Backpressure rule:** a message is never silently dropped. If the queue
is full, the subscriber stops accepting work and disconnects without
acknowledging the QoS 1 delivery. After reconnecting, the broker
redelivers unacknowledged messages from the persistent session.

### Step 5 — Ingestion worker

A single worker thread processes one message at a time:

```text
Decode JSON
  → Validate required fields, types, timestamp format
  → Validate message identity
  → Resolve machine and replay session
  → Detect duplicate message_id
  → Evaluate applicable alarm thresholds
  → Persist reading and alarm transitions
```

- Malformed JSON and invalid structures are rejected.
- Machine, signal and threshold configuration may be cached. The cache
  must be refreshed or invalidated when configuration changes.
- One worker preserves processing order for this deployment.

### Step 6 — PostgreSQL

PostgreSQL is the persistent source of truth. See Section 11 for the
eleven tables.

**Wide telemetry table.** The signal set is known (32 signals), so one
message creates one `telemetry_readings` row with a typed column per
signal. Signal metadata lives in `signal_definitions`. Column names, SQL
types, units and nullability come from the actual workbook headers; no
placeholder names in migrations. If the signal catalogue becomes dynamic,
reassess the storage model instead of adding columns ad hoc.

**Deduplication**

- `UNIQUE (message_id)` is the primary rule.
- `UNIQUE (machine_id, replay_session_id, replay_cycle, source_sequence)`
  is the secondary rule.
- `(machine_id, event_timestamp)` is never a dedup key: two legitimate
  readings can share a timestamp, and a timestamp does not identify a
  delivery.

**Recommended indexes**

- Unique constraints above.
- History: `(machine_id, event_timestamp DESC, reading_id DESC)`.
- Cursor reads: `stream_offset` on `telemetry_readings`, `event_id` on `event_log`.
- Active alarms and event history, based on actual filters.

Do not index every signal column. Add signal indexes only when query
plans justify them.

**Latest reading.** No `telemetry_latest` table initially. Load the
latest reading per machine at startup, keep it in memory, and replace it
only when an incoming reading is newer by event time and tie-break.
Out-of-order readings are stored in history but never replace the latest
frame.

### Step 7 — SQLAlchemy and connections

One Engine is created at startup and shared by the ingestion worker and
Flask. Settings: `pool_size=5`, `max_overflow=2`, `pool_timeout=5`,
`pool_pre_ping=True`. These are starting values; adjust after measuring
checkout wait, query duration and concurrent load. Split into separate
engines only if contention is observed.

**Connection lifecycle**

- Create the Engine once, never per message.
- Use a short-lived Session per unit of work: begin, query and write,
  commit or roll back, close.
- Never share a Session between threads.
- Never hold a transaction open while sending WebSocket messages.

A transaction per message does not mean a new TCP connection per
message; connections are reused from the pool.

### Step 8 — Transaction, stream offset and MQTT acknowledgement

```text
Dequeue message
   │
   ▼
Validate and resolve data
   │
   ▼
BEGIN
   │
   ▼
Duplicate check (message_id) ──► duplicate: skip insert, no alarm, no broadcast
   │ new
   ▼
UPDATE stream_state SET last_reading_offset = last_reading_offset + 1
   RETURNING last_reading_offset            (allocates stream_offset)
   │
   ▼
INSERT telemetry_readings (with stream_offset)
   │
   ▼
Evaluate alarm state → save alarm transitions → save related events
   │
   ▼
COMMIT
   │
   ▼
ACK MQTT delivery
   │
   ▼
Broadcast committed update to WebSocket hub
```

Rules:

1. A duplicate is not inserted again and creates no alarm transition or
   live event. It is still acknowledged.
2. The reading, its stream offset, and its alarm/event changes commit in
   one transaction. If the `UNIQUE` backstop fires (`IntegrityError`),
   the whole transaction rolls back, offset included.
3. On transaction failure: roll back and do not ACK.
4. On a transient database failure, retry with bounded backoff (3
   attempts: 100 ms, 500 ms, 2 s). If still failing, disconnect without
   ACK so the broker redelivers.
5. A permanently invalid payload is logged with its reason and ACKed to
   avoid a poison-message loop. Add a quarantine mechanism only if
   rejected-payload audit becomes a requirement.
6. ACK a valid QoS 1 delivery only after commit.
7. Broadcast only after commit.

Why `stream_state` and not `MAX(reading_id)`: a `BIGSERIAL` value is
allocated before commit, so a higher `reading_id` can commit before a
lower one and a cursor based on `MAX` can skip rows. `stream_state` is
updated inside the transaction and its row lock serializes writers, so
offset order equals commit order. Any other writer that creates events
(for example alarm acknowledgement from the API) must increment
`last_event_offset` the same way, inside its own transaction.

This gives at-least-once MQTT delivery with idempotent persistence. It
does not make MQTT delivery and WebSocket delivery one distributed
transaction.

### Step 9 — Flask backend

#### REST API

| Endpoint | Purpose |
| --- | --- |
| `GET /api/v1/health` | Application and dependency health (Flask, PostgreSQL, MQTT state) |
| `GET /api/v1/dashboard/bootstrap` | Initial snapshot plus synchronization cursors |
| `GET /api/v1/history` | Historical telemetry (cursor-based, bounded) |
| `GET /api/v1/stats` | Aggregated statistics |
| `GET /api/v1/manifest` | Lines, machines, signal metadata |
| `GET /api/v1/alarms` | Active and historical alarms |
| `GET /api/v1/events` | Event history and cursor recovery |
| `GET /api/v1/export` | CSV export |

History endpoints take bounded time ranges, limits and selected signals.
Avoid returning every signal when a chart needs a few.

#### WebSocket (`/ws/v1`)

Server to client: `telemetry.reading`, `alarm.raised`, `alarm.cleared`,
`alarm.acknowledged`, `event.created`, `replay.state`, `command.ack`,
`command.error`.

Client to server: `subscribe`, `sync.complete`, `replay.start`,
`replay.pause`, `replay.speed`, `replay.reset`, `alarm.ack`.

Every command carries a unique `command_id`. Validate type, payload and
authorization, then return an acknowledgement or a structured error.

#### Synchronization and recovery

A WebSocket broadcast is not a durable queue. Clients recover from
PostgreSQL using two cursors taken from `stream_state`:

- `reading_cursor` — latest applied `telemetry_readings.stream_offset`.
- `event_cursor` — latest applied `event_log.event_id`.

**Initial sync**

1. Vue opens the WebSocket and sends `subscribe`.
2. The server registers the client in buffering mode before the snapshot.
3. Vue calls `GET /api/v1/dashboard/bootstrap`.
4. The response returns the snapshot and both cursors from one consistent
   read-only transaction.
5. Vue applies the snapshot and sends `sync.complete` with those cursors.
6. The server discards buffered updates at or below the cursors, sends
   newer ones, then switches the client to live delivery.

**Reconnect**

1. Vue reconnects and sends its last applied cursors.
2. The server registers the connection in buffering mode.
3. The server reads missed telemetry and events after those cursors.
4. It sends the missed records, flushes newer buffered messages without
   repeating cursor values, and switches to live delivery.

The frontend advances a cursor only after the update has been applied.
Each client has a bounded outbound queue so a slow client cannot block
ingestion. No second MQTT notification topic is needed; the hub
broadcasts in-process after commit. After an application restart the hub
registry is rebuilt and the latest state is restored from PostgreSQL.

### Step 10 — Vue dashboard

Features: machine and line status, live KPI cards, real-time signal
charts, active alarms and history, event history, historical readings
with time-range selection, replay controls, CSV export.

- REST for the initial snapshot and history; WebSocket for live updates
  and commands. Do not poll the telemetry API.
- Pinia stores: telemetry, alarms, events, replay, dashboard state.
- WebSocket composable: connection, reconnect, message validation,
  cursor tracking.
- Chart components: ECharts, updated on a 5-second scheduler.
- History service: bounded windows and selected signals.
- Command service: replay and alarm commands with `command_id`.

---

## 10. Replay Control and Alarms

### Replay control

The replay worker and Flask run in the same process, in separate
threads, connected by a thread-safe command queue.

```text
Vue Dashboard
     │  WebSocket command + command_id
     ▼
Flask Replay Service
     ├── validate command
     ├── persist requested_state
     └── enqueue worker command
     ▼
Replay Command Queue (thread-safe)
     ▼
Replay Worker: start · pause · speed · reset
     ▼
Persist applied_state and event
     ▼
WebSocket command.ack / replay.state
```

- The worker checks for commands between records and during its wait, so
  pause and speed changes do not wait out a long source gap.
- Requested and applied state are distinct. The dashboard shows a state
  as active or paused only after the worker confirms it.
- Lifecycle lives in `replay_sessions` (`requested_state`,
  `applied_state`, `replay_cycle`).
- If the worker later moves to its own process, replace the in-process
  queue with an explicit inter-process control channel.

### Alarm lifecycle

- Thresholds come from `machine_signal_limits`, cached in memory.
- Each valid reading is evaluated; only meaningful transitions are
  persisted (`raised → acknowledged → cleared`), never one row per
  normal reading.
- Reading and alarm transitions commit atomically.
- Active alarms are restored from PostgreSQL after a restart.

Acknowledgement is a separate operator command:

```text
Vue → WebSocket alarm.ack + command_id → Flask alarm service
   → BEGIN → conditionally update alarm → insert acknowledgement event
     (advance last_event_offset) → COMMIT
   → WebSocket alarm.acknowledged
```

It must be idempotent: a repeat creates no duplicate event and never
changes an already-cleared alarm.

---

## 11. Database Schema (11 Tables)

| # | Table | Owner | Purpose |
| --- | --- | --- | --- |
| 1 | `datasets` | Preprocessor | One row per imported workbook; `source_timezone`, `timezone_assumed` |
| 2 | `lines` | Seed | Production lines; seeded `LINE_30` |
| 3 | `machines` | Seed | Machines; seeded `LINE_30` machine linked to its line |
| 4 | `signal_definitions` | Seed | 32 signals: name, section, unit (nullable), column mapping |
| 5 | `machine_signal_limits` | Manual | Warning and critical thresholds per (machine, signal) |
| 6 | `replay_sessions` | Replay worker | `requested_state` vs `applied_state`, `replay_cycle` |
| 7 | `stream_state` | Ingestion worker | Single row: `last_reading_offset`, `last_event_offset` |
| 8 | `telemetry_readings` | Ingestion worker | Wide row per accepted message, with `stream_offset` |
| 9 | `alarms` | Ingestion worker | Lifecycle: raised → acknowledged → cleared |
| 10 | `event_log` | Ingestion worker / API | Operational events with monotonic `event_id` |
| 11 | `operator_notes` | API | Free-form annotations |

DDL is defined by `backend/database/models.py` and applied by
`init_db.create_schema()`. `event_log` holds meaningful operational
events only; telemetry belongs in `telemetry_readings`.

---

## 12. Failure Handling

| Failure | Required behaviour |
| --- | --- |
| Publisher loses MQTT connection | Reconnect with backoff; never silently skip the current record |
| Subscriber loses broker connection | Reconnect with stable client ID and persistent session |
| PostgreSQL temporarily unavailable | Roll back, do not ACK, retry 3 times (100 ms, 500 ms, 2 s), then disconnect |
| MQTT message redelivered | Detect via `message_id`; no duplicate insert, no duplicate broadcast |
| Ingestion queue full (`maxsize=100`) | Do not drop, do not ACK; disconnect for backpressure |
| Payload permanently invalid | Log reason, ACK to prevent a poison-message loop |
| WebSocket client disconnects | Client reconnects with cursors; server sends missed records |
| WebSocket broadcast fails | Do not roll back committed telemetry; rely on cursor recovery |
| Application restarts | Reconnect MQTT; restore latest reading and active alarms from Postgres; rebuild WebSocket registry |
| Replay command fails | Report failure; do not claim the requested state was applied |

Recovery of unacknowledged messages while the process is down depends on
correct Mosquitto persistence and MQTT session configuration, and must
be tested.

---

## 13. Logging, Monitoring and Retention

**Log** (structured, with `message_id`, topic and machine code where
practical): startup and shutdown; MQTT connect, disconnect and
subscription state; validation failures and reasons; transaction
success, rollback and retry; duplicate detection; alarm transitions and
acknowledgements; WebSocket connect, disconnect and sync failures;
replay commands and applied state; pool checkout timeouts and database
errors. Never log secrets.

**Health checks** cover the Flask process, PostgreSQL connectivity and
MQTT connection state.

**Retention and performance**

- The dataset is small (~2,139 readings); repeated replay cycles add
  rows. Define a retention period before any wider deployment.
- Monitor table size, index size, query duration and write latency.
- Add time-based partitioning only when volume justifies it.
- Estimate storage from the real signal columns, machine count and
  replay duration. For reference, a live feed of one message every
  5 seconds would be 12 readings per minute and 17,280 per day.

---

## 14. Verification and Smoke Tests

Each phase has a smoke test under `tools/smoke/`. A phase is complete
only when its smoke test passes cleanly.

| Phase | Smoke test | Expected |
| --- | --- | --- |
| 1 | `python .\tools\smoke\db_connect_smoke.py` | `OK: SELECT 1 -> 1` |
| 2b | `python .\tools\smoke\mqtt_smoke.py` | `OK: published state and telemetry` |
| 2c (v1) | `python .\tools\smoke\replay_smoke.py` | `OK: published 5 records at 0.5s intervals` |
| 2d | `python .\tools\smoke\replay_smoke_v2.py` | 10 messages with correct `message_id`s |
| 3b | `python .\tools\smoke\db_schema_smoke.py` | 11 tables, seeds present |
| 3c | `python .\tools\smoke\persist_smoke.py` | 10 rows, `stream_offset` 1..10, no duplicates on re-replay |
| 4b | `python .\tools\smoke\websocket_smoke.py` | 5 live readings received |

### Acceptance tests

Run before declaring the project complete.

| Test | Expected behaviour |
| --- | --- |
| Import same dataset twice | No duplicate `datasets` row; second import is idempotent |
| Replay a 10-minute window | All eligible records published in `(event_timestamp, source_sequence)` order |
| Replay the same window twice | Cycle 2 produces new rows with new `message_id`s; no duplicates |
| Duplicate MQTT delivery (re-publish) | `UNIQUE (message_id)` catches it; no duplicate row, no duplicate broadcast |
| Kill Postgres mid-replay | Consumer rolls back, does not ACK, retries; no data loss on recovery |
| Fill ingestion queue | Subscriber disconnects; broker redelivers on reconnect |
| Restart broker | Subscriber reconnects; unacked messages redelivered |
| Restart Flask app | WebSocket clients reconnect; cursors catch up; no missing readings |
| Disconnect WebSocket client for 30 s | Reconnect with cursors; missed records delivered; no gap |
| Slow WebSocket client | Isolated by bounded outbound queue; does not block ingestion |
| Chart render interval | ECharts updates on a 5-second schedule; no polling |
| Alarm threshold crossing | `alarm.raised` broadcast; `alarms` row created; chart marker appears |
| Alarm acknowledged twice | One acknowledgement event; no state corruption |
| Replay pause command | `applied_state` changes only after the worker confirms; dashboard reflects confirmed state |

---

## 15. Implementation Status and Order

| Phase | Status | Deliverables |
| --- | --- | --- |
| 1 — Dataset, contract, Parquet | ✅ Complete | `preprocess_dataset.py`, `schema.py`, `signal_contract.md`, `*.parquet` |
| 2a — Broker, topic contract | ✅ Complete | `mosquitto.conf`, `mqtt_topics.md` |
| 2b — MQTT client | ✅ Complete | `backend/mqtt/client.py` |
| 2c — Replay publisher (v1) | ✅ Complete, superseded | `backend/publisher/replay.py`, replaced by `backend/replay/worker.py` |
| 2d — Replay worker, subscriber, bounded queue | ⏳ Next | `backend/replay/*`, `backend/mqtt/subscriber.py`, `replay_smoke_v2.py` |
| 3a — Database engine + models | ⏳ | `engine.py`, `models.py` |
| 3b — Schema + seeds | ⏳ | `init_db.py`, `db_schema_smoke.py` |
| 3c — Ingestion consumer + repository | ⏳ | `consumer.py`, `repository.py`, `persist_smoke.py` |
| 4a — Flask REST API | ⏳ | `backend/api/*` |
| 4b — WebSocket hub + sync | ⏳ | `backend/realtime/*`, `websocket_smoke.py` |
| 5a — Vue scaffold | ⏳ | `frontend/` |
| 5b — Dashboard, charts, alarms | ⏳ | `frontend/src/*` |
| 6 — Replay controls + hardening | ⏳ | `backend/services/lifecycle.py`, `tools/dev/start_all.ps1` |

Phases 1 and 2a–2c are proven end to end; the remaining work starts at
Phase 2d. Do not start visual polish before the telemetry pipeline,
persistence and live update path are reliable.

---

## 16. Architecture Rules

1. Excel is a replay input only, imported once.
2. The replay worker reads Parquet; it does not read Excel or query `telemetry_readings`.
3. The publisher connects to Mosquitto, never to PostgreSQL.
4. The subscriber does not touch the database; the ingestion worker does.
5. PostgreSQL is the persistent source of truth for operational state.
6. `message_id` is deterministic; `UNIQUE (message_id)` is the primary dedup rule.
7. Replay identity `(machine_id, replay_session_id, replay_cycle, source_sequence)` is the secondary dedup rule.
8. Never use `(machine_id, event_timestamp)` as a dedup key.
9. `stream_offset` is allocated inside each transaction via `stream_state UPDATE ... RETURNING`; never `MAX(reading_id)`.
10. MQTT QoS 1 with manual ACK; ACK only after commit.
11. Broadcast only after commit.
12. One engine, one pool; short-lived sessions; never share a session across threads.
13. Persist each reading and its alarm transitions in a single transaction.
14. REST for snapshots and history; WebSocket for live updates and commands.
15. Cursor recovery uses `stream_state.last_reading_offset` and `last_event_offset`.
16. Replay commands are confirmed by the worker (`applied_state`), not by the Flask endpoint.
17. Single-process modular monolith for the initial deployment.
18. Add infrastructure only when a measured requirement justifies it.

---

## 17. Non-Goals

- Multi-machine replay in one deployment (the schema supports it; the deployment does not)
- Authentication and authorisation (development only, loopback broker)
- Horizontal scaling (single process, single Postgres, single Mosquitto)
- Data warehousing or analytics (operational history only)
- Automatic alarm threshold tuning (thresholds are manual)
- Cloud deployment (local development only)

---

## 18. Handoff

Reference documents:

- Architecture: `docs/architecture/system_architecture.md`
- Signal contract: `docs/contract/signal_contract.md`
- MQTT topics: `docs/architecture/mqtt_topics.md`
- Frozen telemetry schema: `backend/contract/schema.py`

For a new developer:

1. Read `docs/architecture/system_architecture.md`, then `docs/contract/signal_contract.md`.
2. Run `python .\tools\smoke\db_connect_smoke.py` to confirm the environment.
3. Run `python .\tools\smoke\mqtt_smoke.py` to confirm the broker.
4. Read `tools/preprocessing/preprocess_dataset.py` for the data path.
5. Follow Section 15 to see where implementation stands.

---

## 19. Final Data Flow

```text
EXCEL → PARQUET → REPLAY WORKER
   │  MQTT QoS 1
   ▼
MOSQUITTO → PAHO SUBSCRIBER → BOUNDED QUEUE → INGESTION WORKER
   │  validate + deduplicate + stream offset + alarms
   ▼
POSTGRESQL (one transaction) → COMMIT → ACK MQTT
   ▼
IN-PROCESS WEBSOCKET HUB → FLASK-SOCK → VUE + PINIA + ECHARTS
```

MQTT transports telemetry, Python validates and processes it, PostgreSQL
persists it, SQLAlchemy manages reusable connections, Flask exposes the
application interface, WebSockets deliver committed live updates, and
Vue presents the industrial monitoring dashboard
