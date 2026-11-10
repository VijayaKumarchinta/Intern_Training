# Line Speed 30 --- IIoT Live Monitoring Dashboard

A real-time industrial monitoring dashboard that replays machine
readings from an Excel dataset, transports telemetry through MQTT,
stores validated readings in PostgreSQL, and displays live machine
information through a Vue.js dashboard.

The Excel file is a simulation input only. The dashboard and backend
read operational data from PostgreSQL and receive live updates through
WebSockets.

------------------------------------------------------------------------

## 1. Technology Stack

  -----------------------------------------------------------------------
  Layer                   Technology              Responsibility
  ----------------------- ----------------------- -----------------------
  Dataset preparation     Python, Pandas          Read, clean, validate
                                                  and order Excel records

  Replay publisher        Python, Paho MQTT       Publish telemetry
                                                  messages

  Message broker          Eclipse Mosquitto       Receive and distribute
                                                  MQTT messages

  MQTT subscriber         Python, Paho MQTT       Receive telemetry from
                                                  the broker

  Backend processing      Python                  Validate readings and
                                                  evaluate alarm
                                                  conditions

  Database                PostgreSQL              Persist telemetry and
                                                  operational records

  Database access         SQLAlchemy              Transactions, sessions
                                                  and connection pooling

  HTTP API                Flask                   Initial data, history,
                                                  statistics and exports

  Real-time communication Flask-Sock, WebSockets  Live updates and
                                                  dashboard commands

  Frontend                Vue.js 3                Dashboard interface

  Frontend state          Pinia                   Manage telemetry,
                                                  alarms, events and
                                                  replay state

  Charts                  Apache ECharts          Display machine trends

  Configuration           python-dotenv           Load environment
                                                  configuration

Logging                 Python logging          Record application
                                                  activity and failures
  -----------------------------------------------------------------------

The initial implementation uses the existing stack. Redis, Kafka, Celery
and additional services are not required for this version.

------------------------------------------------------------------------

## 2. High-Level System Architecture

``` text
Excel Dataset
     |
     v
Python Replay Publisher
     |
     | MQTT QoS 1
     v
Mosquitto MQTT Broker
     |
     v
Paho MQTT Subscriber
     |
     v
Bounded Ingestion Queue
     |
     v
Python Ingestion Worker
     |
     +---- Decode and validate payload
     +---- Check message identity
     +---- Resolve machine and replay session
     +---- Evaluate alarm conditions
     |
     v
SQLAlchemy Ingestion Engine
     |
     v
PostgreSQL
     |
     | Successful commit
     v
In-process WebSocket Hub
     |
     v
Flask-Sock WebSocket
     |
     v
Vue.js Dashboard
```

Flask also provides REST endpoints for initial dashboard data,
historical readings, statistics, machine metadata, alarms and CSV
exports.

### Application structure

The initial deployment is a **single-process modular monolith**. The
process contains separate application components and background threads:

- Flask HTTP and WebSocket server.
- Paho MQTT subscriber network loop.
- Telemetry ingestion worker.
- Python replay publisher worker.
- In-process WebSocket client registry.

Mosquitto and PostgreSQL run as separate services. A single application
process does not mean a single thread or a single database connection.

------------------------------------------------------------------------

## 3. How the System Works

### Step 1 --- Excel Dataset

The Excel workbook is the source for replay simulation.

1. Read the workbook using Pandas.
2. Clean and validate the records.
3. Convert timestamps to a consistent UTC representation.
4. Sort records chronologically.
5. Map workbook headers to the telemetry message fields.
6. Prepare rows for replay.

Excel is not read by the Vue dashboard and is not queried by Flask at
runtime.

### Step 2 --- Python Replay Publisher

The publisher reads the prepared records one at a time.

For each record, it:

1. Builds a JSON telemetry message.
2. Adds a stable message identity and replay metadata.
3. Publishes to the MQTT topic.
4. Waits for the configured replay interval.
5. Moves to the next row.
6. Starts another replay cycle when looping is enabled.

**Telemetry topic**

``` text
factory/line30/telemetry
```

The publisher connects to Mosquitto. It does not connect to PostgreSQL.

**Message identity**

Each message includes:

- `message_id`: globally unique identifier for the telemetry message.
- `replay_session_id`: identifies one replay execution.
- `replay_cycle`: identifies the loop number within that execution.
- `sequence_number`: identifies the row's position in the replay
    stream.
- `machine_code`: identifies the machine.
- `event_timestamp`: timestamp represented by the source reading.
- `signals`: the signal values for that reading.

The publisher must reuse the same `message_id` when retrying the same
message. A new replay cycle receives a new identity. This allows the
database to distinguish a legitimate repeated row in a later cycle from
a duplicate delivery of an earlier message.

The publisher uses MQTT QoS 1. Telemetry messages are not published as
retained messages.

### Step 3 --- Mosquitto MQTT Broker

Mosquitto is the messaging intermediary.

- Receives telemetry from the publisher.
- Delivers messages to subscribed clients.
- Keeps the publisher independent from the database and dashboard.
- Maintains persistent MQTT session state according to broker
    configuration.

For reliable subscriber recovery, enable Mosquitto persistence and
configure a stable subscriber client ID and persistent session. The
exact session settings must match the MQTT protocol version and Paho
client configuration.

### Step 4 --- Paho MQTT Subscriber

The subscriber connects to Mosquitto and subscribes to:

``` text
factory/line30/telemetry
```

The MQTT callback should do minimal work:

1. Receive the message.
2. Capture its topic, payload and MQTT delivery metadata.
3. Place it into a bounded in-memory queue.
4. Return control to the MQTT network loop.

The callback should not perform long database operations directly. A
separate ingestion worker consumes the queue and processes messages
sequentially.

**Backpressure rule:** Messages must never be silently dropped when the
queue is full. The subscriber must stop accepting work and disconnect
without acknowledging the unprocessed QoS 1 delivery. After
reconnection, the broker can redeliver unacknowledged messages from the
persistent session.

### Step 5 --- Python Ingestion Processing

The ingestion worker processes one message at a time.

``` text
MQTT Message
     |
     v
Decode JSON
     |
     v
Validate Required Fields and Types
     |
     v
Validate Message Identity
     |
     v
Resolve Machine and Replay Session
     |
     v
Evaluate Applicable Alarm Thresholds
     |
     v
Persist Reading and Alarm Transitions
```

Processing responsibilities:

- Reject malformed JSON and invalid payload structures.
- Validate required fields, data types and timestamp format.
- Resolve the machine and replay session.
- Detect duplicate message identities.
- Evaluate machine-specific warning and critical thresholds.
- Prepare telemetry and any alarm lifecycle changes for persistence.

Machine metadata, signal metadata and threshold configuration can be
cached to avoid repeated lookup queries. Cache refresh or invalidation
is required when configuration changes.

A single ingestion worker preserves message processing order for this
initial deployment. The database remains the source of truth for
persisted readings and alarm state.

### Step 6 --- PostgreSQL Database

PostgreSQL is the persistent source of truth.

The proposed schema contains **nine tables**:

  -----------------------------------------------------------------------
  Table                               Responsibility
  ----------------------------------- -----------------------------------
  `lines`                             Production line information

  `machines`                          Machine information and line
                                      relationship

  `signal_definitions`                Signal names, codes, units and
                                      telemetry column mapping

  `machine_signal_limits`             Machine-specific warning and
                                      critical thresholds

  `telemetry_readings`                One wide row for each accepted
                                      telemetry message

  `alarms`                            Alarm occurrences, status and
                                      acknowledgement lifecycle

  `event_log`                         Important operational events and
                                      alarm transitions

  `operator_notes`                    Operator annotations

`replay_sessions`                   Replay execution, cycle and control
                                      state
  -----------------------------------------------------------------------

#### Telemetry table design

The dataset has a known signal set, so the initial design uses a **wide
telemetry table**:

- One MQTT message creates one row in `telemetry_readings`.
- Each signal has its own typed database column.
- Signal metadata remains in `signal_definitions`.
- Exact column names, SQL types, units and nullability must be derived
    from the actual Excel headers and signal semantics before creating
    the final DDL. Do not use placeholder signal names in production
    migrations.

The wide design avoids inserting a separate child row for every signal
in every message. It is suitable while the signal catalogue is
relatively fixed. If signals become highly dynamic, reassess the storage
model rather than adding columns without a schema review.

#### Message identity and duplicate protection

The telemetry table must enforce a stable uniqueness rule. For this
replay system, use:

- A unique `message_id`.
- A unique replay identity based on `replay_session_id`,
    `replay_cycle` and `sequence_number` (include `machine_id` if
    sequence numbers are only unique within a machine).

Do not rely only on `(machine_id, event_timestamp)` for deduplication.
Two legitimate readings can share a timestamp, and timestamps alone do
not identify a delivery.

#### Recommended indexes

Start with indexes that support actual dashboard queries:

- Unique index/constraint on `message_id`.
- Unique constraint on the replay identity.
- History index on
    `(machine_id, event_timestamp DESC, reading_id DESC)`.
- Indexes for active alarm queries and event history based on their
    actual filters.

Do not index every signal column by default. Add signal-specific indexes
only when query plans and workload measurements justify them.

#### Latest reading

Do not maintain a separate `telemetry_latest` table initially.

- On application startup, load the latest reading for each machine
    from PostgreSQL.
- Maintain the latest in-memory telemetry frame in the application
    process.
- Update it only when the incoming reading is newer according to the
    defined event-time and tie-break policy.
- Persist out-of-order readings in history, but do not let an older
    reading replace the current latest frame.

A separate latest-reading projection can be introduced later if measured
query cost or machine count justifies it.

### Step 7 --- SQLAlchemy and Database Connections

SQLAlchemy Engines are created once during application startup. They
manage reusable database connection pools.

Use two Engines connected to the same PostgreSQL database:

  -----------------------------------------------------------------------
  Engine                  Used by                 Purpose
  ----------------------- ----------------------- -----------------------
  Ingestion Engine        Telemetry ingestion     Telemetry writes and
                          worker                  alarm/event persistence

Application Engine      Flask REST and          Dashboard reads,
                          operational services    history, statistics,
                                                  replay commands and
                                                  alarm acknowledgement
  -----------------------------------------------------------------------

A practical initial pool configuration for the current single-process,
low-volume replay workload is:

  Setting             Ingestion pool   Application pool
  ----------------- ---------------- ------------------
  `pool_size`                      1                  3
  `max_overflow`                   0                  2
  `pool_timeout`           5 seconds          5 seconds
  `pool_pre_ping`             `True`             `True`

These are starting values, not universal production limits. Adjust them
after measuring connection checkout wait time, query duration,
transaction duration and concurrent request load.

**Connection lifecycle**

- Create each Engine once.
- Create a short-lived SQLAlchemy Session for each unit of database
    work.
- Begin a transaction, execute the required queries and writes, then
    commit or roll back.
- Close the Session so its connection returns to the pool.
- Never share a SQLAlchemy Session between threads.
- Never hold a database transaction open while sending WebSocket
    messages.

A transaction is created for each telemetry message, but the underlying
TCP connection is normally reused from the pool. A new database
connection is not opened for every five-second replay interval.

### Step 8 --- Database Transaction and MQTT Acknowledgement

Telemetry persistence and associated alarm transitions must be atomic.

``` text
Ingestion Worker Receives Queued Message
                  |
                  v
        Validate and Resolve Data
                  |
                  v
       Acquire Ingestion Connection
                  |
                  v
             BEGIN
                  |
                  v
       Insert Telemetry Reading
                  |
                  v
       Check Duplicate Result
                  |
          +-------+-------+
          |               |
       Duplicate       New Reading
          |               |
          |               v
          |        Evaluate Alarm State
          |               |
          |               v
          |        Save Alarm Transitions
          |               |
          |               v
          |        Save Related Events
          |               |
          |               v
          |             COMMIT
          |               |
          +-------+-------+
                  |
                  v
       Acknowledge MQTT Delivery
                  |
                  v
       Broadcast Committed Update
                  |
                  v
          Update Vue Dashboard
```

Rules:

1. A duplicate message is not inserted again and does not create
    another alarm transition or live telemetry event.
2. A new reading and its alarm/event changes are committed in one
    transaction.
3. If the transaction fails, roll it back and do not acknowledge the
    MQTT delivery.
4. After a transient database failure, retry with bounded backoff. If
    processing cannot complete, disconnect without acknowledging so the
    broker can redeliver through the persistent session.
5. A permanently invalid payload is rejected, logged with its reason
    and acknowledged so it does not create an endless redelivery loop.
    If rejected-payload audit is required, add a deliberate quarantine
    mechanism.
6. Acknowledge a valid QoS 1 MQTT delivery only after its database
    transaction commits successfully.
7. Broadcast only after commit.

Configure the Paho subscriber for manual acknowledgements
(`manual_ack=True`, where supported by the installed Paho version).
Acknowledge the delivery using its message ID and QoS after successful
persistence. Confirm the installed Paho version supports the selected
manual-ack API before implementation.

This provides at-least-once MQTT delivery with idempotent database
persistence. It does not make MQTT delivery and WebSocket delivery one
distributed transaction.

### Step 9 --- Flask Backend

Flask provides the application interface between PostgreSQL and Vue.js.

#### REST API

REST is used for request/response operations:

  -----------------------------------------------------------------------
  Endpoint                            Purpose
  ----------------------------------- -----------------------------------
  `GET /api/v1/health`                Application and dependency health

  `GET /api/v1/dashboard/bootstrap`   Initial dashboard snapshot and
                                      synchronization cursors

  `GET /api/v1/history`               Historical telemetry

  `GET /api/v1/stats`                 Aggregated statistics

  `GET /api/v1/manifest`              Lines, machines and signal metadata

  `GET /api/v1/alarms`                Active and historical alarms

  `GET /api/v1/events`                Operational event history and
                                      cursor recovery

`GET /api/v1/export`                CSV export
  -----------------------------------------------------------------------

Historical endpoints should support bounded time ranges, limits and
selected signals. Avoid retrieving every signal when a chart needs only
a small subset.

#### WebSocket

Use Flask-Sock for the WebSocket endpoint:

``` text
/ws/v1
```

Server-to-client messages:

- `telemetry.reading`
- `alarm.raised`
- `alarm.cleared`
- `alarm.acknowledged`
- `event.created`
- `replay.state`
- `command.ack`
- `command.error`

Client-to-server commands:

- `subscribe`
- `sync.complete`
- `replay.start`
- `replay.pause`
- `replay.speed`
- `replay.reset`
- `alarm.ack`

Each command should include a unique `command_id`. Validate command
type, payload and authorization before applying it. Return an
acknowledgement or a structured error.

#### WebSocket synchronization and recovery

A WebSocket broadcast is not a durable message queue. A client can
disconnect or miss an update. Use database-backed cursors to recover.

Use two cursors:

- `reading_cursor`: latest processed `telemetry_readings.reading_id`.
- `event_cursor`: latest processed `event_log.event_id`.

Initial dashboard synchronization:

1. Vue opens the WebSocket and sends `subscribe`.
2. The server registers the client in buffering mode before reading the
    snapshot.
3. Vue requests `GET /api/v1/dashboard/bootstrap`.
4. The bootstrap response returns the dashboard snapshot and both
    cursors from one consistent read-only database transaction.
5. Vue applies the snapshot and sends `sync.complete` with the returned
    cursors.
6. The server discards buffered updates at or below those cursors,
    sends newer buffered updates, then switches the client to live
    delivery.

Reconnect synchronization:

1. Vue reconnects and sends its last successfully applied cursors.
2. The server registers the connection in buffering mode.
3. The server retrieves missed telemetry and events from PostgreSQL
    after those cursors.
4. The server sends the missed records, then flushes newer buffered
    messages without duplicating cursor values.
5. The connection switches to live delivery.

The history and event APIs must support cursor-based retrieval. Keep
cursor advancement in the frontend only after the corresponding update
has been successfully applied.

For the initial single-process design, the WebSocket hub can broadcast
directly in-process after database commit. No second MQTT notification
topic is required.

If a WebSocket client misses an update, it can recover from PostgreSQL
using its cursors. If the application restarts, the in-memory WebSocket
registry is rebuilt and the latest telemetry state is recovered from
PostgreSQL.

### Step 10 --- Vue.js Dashboard

Vue.js displays the data received from Flask.

Dashboard features:

- Machine and production-line status.
- Live KPI cards.
- Real-time signal charts.
- Active alarms and alarm history.
- Operational event history.
- Historical readings and time-range selection.
- Replay controls.
- CSV export.

Use REST for the initial snapshot and historical queries. Use WebSockets
for live updates and operational commands. Do not poll the telemetry API
every five seconds to simulate real-time updates.

Recommended frontend responsibilities:

- Pinia stores: telemetry, alarms, events, replay and dashboard state.
- WebSocket composable: connection, reconnect, message validation and
    cursor tracking.
- Chart components: render selected signal series using ECharts.
- History service: request bounded historical windows and selected
    signals.
- Command service: send replay and alarm commands with command IDs.

------------------------------------------------------------------------

## 4. Replay Control Design

The replay publisher and Flask application initially run inside the same
application process, but in separate threads.

Use a thread-safe command queue or equivalent synchronized control
interface between the Flask replay service and the publisher worker.

``` text
Vue Dashboard
     |
     | WebSocket command + command_id
     v
Flask Replay Service
     |
     +---- Validate command
     +---- Persist requested state
     +---- Enqueue publisher command
     |
     v
Thread-safe Replay Command Queue
     |
     v
Python Publisher Worker
     |
     +---- Start
     +---- Pause
     +---- Change speed
     +---- Reset
     |
     v
Persist applied state and event
     |
     v
WebSocket acknowledgement/state update
```

The publisher worker must check for control commands between replay
records and during its wait interval so pause and speed changes do not
have to wait for the full original interval.

Distinguish between a requested command and a command actually applied
by the publisher. Do not report a replay state as active or paused until
the publisher confirms the change.

Persist replay lifecycle information in `replay_sessions`. Use
`command_id` to make command handling idempotent.

If the publisher is moved into a separate process in a future version,
replace the in-process queue with an explicit inter-process control
mechanism. That is not required for the initial deployment.

------------------------------------------------------------------------

## 5. Alarm Lifecycle and Acknowledgement

Alarm evaluation is performed by the Python ingestion processing layer
using machine-specific thresholds.

- Load threshold configuration from PostgreSQL and cache it.
- Evaluate each new valid reading.
- Persist only meaningful alarm lifecycle transitions, not a new alarm
    row for every normal reading.
- Persist the telemetry reading and its alarm transitions atomically.
- Restore active alarm state from PostgreSQL after application
    restart.

Alarm acknowledgement is a separate operator command:

``` text
Vue Dashboard
     |
     v
WebSocket alarm.ack + command_id
     |
     v
Flask Alarm Service
     |
     v
Application SQLAlchemy Pool
     |
     v
BEGIN
     |
     v
Validate and conditionally update alarm
     |
     v
Insert acknowledgement event
     |
     v
COMMIT
     |
     v
WebSocket acknowledgement and state update
```

Acknowledgement must be idempotent. A repeated command must not create
duplicate acknowledgement events or incorrectly change an
already-cleared alarm.

------------------------------------------------------------------------

## 6. Failure Handling and Recovery

  -----------------------------------------------------------------------
  Failure                             Required behaviour
  ----------------------------------- -----------------------------------
  Publisher loses MQTT connection     Reconnect with backoff; do not
                                      silently skip the current record

  Subscriber loses broker connection  Reconnect using the stable client
                                      ID and persistent session

  PostgreSQL is temporarily           Roll back, do not MQTT-ack the
  unavailable                         valid message, retry with bounded
                                      backoff

  MQTT message is redelivered         Detect its stable `message_id`; do
                                      not insert or broadcast it twice

  Ingestion queue is full             Do not drop or acknowledge the
                                      message; apply backpressure and
                                      reconnect for redelivery

  Payload is permanently invalid      Log the validation reason and
                                      acknowledge it to avoid
                                      poison-message loops

  WebSocket client disconnects        Reconnect and recover missed
                                      records using reading and event
                                      cursors

  WebSocket broadcast fails           Do not roll back committed
                                      telemetry; rely on cursor-based
                                      recovery

  Application restarts                Reconnect MQTT, restore latest
                                      readings and active alarms from
                                      PostgreSQL, rebuild WebSocket
                                      connections

Replay command fails                Report failure; do not claim the
                                      requested state was applied
  -----------------------------------------------------------------------

The initial system uses one ingestion worker and one application
process. If the process is unavailable, the MQTT persistent session and
broker persistence help retain unacknowledged QoS 1 deliveries. This
depends on correct Mosquitto persistence and MQTT session configuration
and must be tested.

------------------------------------------------------------------------

## 7. Logging and Monitoring

Use Python logging with structured fields where practical.

Record:

- Application startup and shutdown.
- MQTT connection, disconnection and subscription state.
- Message ID, topic and machine code.
- Payload validation failures and rejection reasons.
- Database transaction success, rollback and retry.
- Duplicate message detection.
- Alarm transitions and acknowledgements.
- WebSocket connections, disconnections and synchronization failures.
- Replay commands and applied state.
- Connection pool checkout timeouts and database errors.

Do not write every telemetry message into `event_log`. Telemetry belongs
in `telemetry_readings`; `event_log` is for meaningful operational
events.

Provide health checks for the Flask process, PostgreSQL connectivity and
MQTT connection state. Keep secrets and credentials out of logs.

------------------------------------------------------------------------

## 8. Data Retention and Performance

Start with a simple retention policy and measure actual data growth.

- Keep the telemetry history needed by the dashboard and project.
- Define a retention period before production deployment.
- Archive or delete old telemetry according to an approved policy.
- Monitor table size, index size, query duration and write latency.
- Introduce time-based partitioning only when volume and retention
    operations justify it.
- Avoid premature tuning of PostgreSQL internals.
- Do not add indexes without a query requirement and query-plan
    evidence.

At one message every five seconds, one machine produces 12 readings per
minute and 17,280 readings per day. Calculate storage and retention
using the actual signal columns, number of machines and replay duration.

------------------------------------------------------------------------

## 9. Suggested Project Structure

``` text
line-speed-30-iiot/
|
+-- backend/
|   +-- app/
|   |   +-- __init__.py
|   |   +-- config.py
|   |   +-- extensions.py
|   |   +-- models/
|   |   +-- repositories/
|   |   +-- services/
|   |   |   +-- ingestion_service.py
|   |   |   +-- alarm_service.py
|   |   |   +-- replay_service.py
|   |   |   +-- websocket_service.py
|   |   +-- mqtt/
|   |   |   +-- subscriber.py
|   |   |   +-- message_queue.py
|   |   +-- api/
|   |   |   +-- routes/
|   |   +-- websocket/
|   |   |   +-- routes.py
|   |   +-- workers/
|   |       +-- ingestion_worker.py
|   |       +-- replay_worker.py
|   +-- migrations/
|   +-- tests/
|   +-- run.py
|
+-- publisher/
|   +-- replay_publisher.py
|   +-- dataset_loader.py
|   +-- payload_builder.py
|   +-- replay_controls.py
|
+-- frontend/
|   +-- src/
|       +-- components/
|       +-- views/
|       +-- stores/
|       +-- composables/
|       +-- services/
|       +-- charts/
|
+-- data/
|   +-- Line_Speed_30.xlsx
|
+-- database/
|   +-- schema.sql
|   +-- seed.sql
|
+-- logs/
|
+-- .env.example
+-- .gitignore
+-- README.md
```

This is a logical structure. Adjust file names to the actual
implementation while keeping responsibilities separated.

------------------------------------------------------------------------

## 10. Implementation Order

Build and verify the system in stages.

1. **Dataset and message contract** --- inspect the actual workbook
    headers, define signal types and units, and finalize the JSON
    payload and message identity.
2. **Database** --- create the nine-table schema, constraints, indexes
    and seed records.
3. **Publisher** --- replay one row at a time with QoS 1, session
    identity, cycle and sequence metadata.
4. **MQTT subscriber** --- establish persistent session configuration,
    manual acknowledgements and reconnect behaviour.
5. **Ingestion worker** --- bounded queue, validation, idempotency,
    transaction handling and alarm persistence.
6. **Flask REST API** --- bootstrap snapshot, history, statistics,
    manifest, alarms, events and export.
7. **WebSocket layer** --- in-process fanout, initial synchronization,
    cursor recovery and command handling.
8. **Vue dashboard** --- initial snapshot, live telemetry, charts,
    alarms, events and history.
9. **Replay controls** --- thread-safe publisher commands and persisted
    replay state.
10. **Hardening** --- test duplicate delivery, database outage, queue
    saturation, broker restart, WebSocket reconnect and application
    restart.

Do not proceed to visual polish before the telemetry pipeline, database
persistence and live update path are reliable.

------------------------------------------------------------------------

## 11. Architecture Rules

1. Excel is only a replay input.
2. The publisher connects to Mosquitto, not PostgreSQL.
3. The subscriber receives MQTT messages; the ingestion worker performs
    database processing.
4. PostgreSQL is the persistent source of truth.
5. Use stable message identity and database uniqueness constraints.
6. Use MQTT QoS 1 and acknowledge valid messages only after successful
    database commit.
7. Persist each reading and its alarm transitions atomically.
8. Use SQLAlchemy Engines and connection pools; do not create an Engine
    per message.
9. Use short-lived Sessions and never share a Session across threads.
10. Keep ingestion and application database pools separate.
11. Commit database changes before WebSocket broadcasts.
12. Use REST for snapshots and historical queries.
13. Use WebSockets for live updates and operational commands.
14. Use database-backed cursors to recover missed WebSocket updates.
15. Replay controls must reach and be confirmed by the actual publisher
    worker.
16. Keep the initial deployment as a single-process modular monolith.
17. Add infrastructure only when a measured requirement justifies it.

------------------------------------------------------------------------

## 12. Final Data Flow

``` text
EXCEL DATASET
     |
     v
PYTHON REPLAY PUBLISHER
     |
     | MQTT QoS 1
     v
MOSQUITTO MQTT BROKER
     |
     v
PAHO MQTT SUBSCRIBER
     |
     v
BOUNDED INGESTION QUEUE
     |
     v
PYTHON INGESTION WORKER
     |
     | Validate + deduplicate + evaluate alarms
     v
SQLALCHEMY INGESTION POOL
     |
     | Transaction: insert reading + alarm/event changes
     v
POSTGRESQL
     |
     | Commit, then acknowledge MQTT delivery
     v
IN-PROCESS WEBSOCKET HUB
     |
     v
FLASK-SOCK WEBSOCKET
     |
     v
VUE.JS + PINIA + ECHARTS DASHBOARD
```

Flask REST endpoints serve initial snapshots and historical data.
WebSockets deliver committed live updates and carry replay and alarm
commands.

**Excel → Publisher → MQTT Broker → Subscriber → Python Processing →
PostgreSQL → Flask → WebSocket → Vue.js Dashboard**

MQTT transports telemetry, Python validates and processes it, PostgreSQL
persists it, SQLAlchemy manages reusable database connections, Flask
exposes the application interface, WebSockets deliver live updates, and
Vue.js presents the industrial monitoring dashboard.
