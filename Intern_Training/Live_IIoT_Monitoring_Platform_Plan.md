# Live IIoT Monitoring Platform Plan — Intern Training

**Source:** `Live_IIoT_Monitoring_Platform_Plan.md`

> Proposed architecture to evolve the Machine Sensor API into a reliable, secure, real-time industrial monitoring platform using actual API/database data rather than mocks.

---

## 1. Executive summary

**Goal:** Evolve the existing work (Flask + PostgreSQL Machine Sensor API, Mosquitto + TLS/mTLS, Paho client) into a real-time IIoT monitoring platform.

**Foundation:** Existing Flask + PostgreSQL Machine Sensor API, Mosquitto broker (Windows, 8883, TLS/mTLS), Paho Python client, Machine Log Monitor, MQTT training notes.

**Architecture:** Modular monolith with a separately managed ingestion worker. Do **not** introduce Kafka, Kubernetes, or a large microservice estate before throughput/operational requirements justify it.

**Platform shape:**
- Machines/simulators publish telemetry to Mosquitto over MQTT/TLS (port 8883, TLS/mTLS already configured).
- A dedicated Python ingestion worker validates each message and persists accepted readings through the existing service/database layer.
- The Flask API exposes machine status, latest readings, historical trends, and alarms.
- A web dashboard consumes those endpoints and presents an operations-focused view of machine health.

**Existing MQTT infrastructure:**
- Mosquitto broker: Windows service, listener 8883, `require_certificate true`, `use_identity_as_username true`, `allow_anonymous false`.
- Certificate chain: CA → server cert → client cert, built with OpenSSL; SAN config for IP/DNS.
- Paho client demo: `mqttdemo.py` — Callback API v2, TLS 8883, all five callbacks, return-code checks, `logging.exception` in every error path.

---

## 2. Goals and non-goals

**Goals:**
- Show machine inventory, connectivity, telemetry freshness, and current operating condition.
- Receive sensor telemetry through MQTT with TLS/mTLS.
- Persist measurements in PostgreSQL and query historical ranges efficiently.
- Detect threshold-based conditions and record alarm lifecycle events.
- Expose a stable, validated API to the dashboard.
- Make failures observable and recoverable.
- Preserve existing Machine Sensor API functionality and tests.

**Non-goals for the first release:**
- Predictive maintenance or machine-learning diagnosis.
- PLC/SCADA control commands or remote actuation.
- Multi-region high availability.
- A complex event-streaming platform before it is needed.
- Treating log entries as sensor measurements.

---

## 3. Proposed system architecture

```text
Industrial / Device Layer                  Messaging Layer
Machines and sensors                     Mosquitto MQTT broker
Telemetry simulator for development          CA, server + client certs
                                           Topic ACLs
                     Application Layer
Machine / simulator ──MQTT over TLS/mTLS──▶ Mosquitto
Telemetry simulator ──MQTT over TLS/mTLS──▶ Mosquitto
        ▲                                   ▲
        ▼                                   ▼
Python MQTT ingestion worker ◀─────────────┼─────────────┐
        │                                  │             │
        ▼                                  ▼             ▼
   Validation & normalization   Threshold & alarm evaluation
        │                          DB persistence          │
        ▼                                                  ▼
      Shared backend service/repository layer  (separate pool instance)
                                                      │
                                                      ▼
                                                    PostgreSQL
                                                      ▲
                                                      │
Flask REST API ◀──────────────────────────────────────┘
   ▲
   │
Dashboard ──REST──▶ API
```

**Component responsibilities:**

| Component | Responsibility | Deployment boundary |
|---|---|---|
| Machine / simulator | Produce timestamped telemetry | Device or development process |
| Mosquitto | Route MQTT messages; enforce auth + topic permissions | Independent service |
| MQTT ingestion worker | Subscribe, decode, validate, normalize, handle delivery and persistence failures | Separate process |
| Optional queue | Buffer between arriving messages and slow storage; bound memory | Separate process or in-process with the worker |
| Shared backend service/repository layer | Apply database operations + transaction policy consistently (needs its own db instance in the worker, not the module-level singleton) | Reused Python package |
| PostgreSQL | Store machine metadata, measurements, alarm state | Database service |
| Flask API | Validate HTTP requests and expose current/historical data | Separate web process |
| Dashboard | Display operational status, trends, alarm workflows | Web application |

**Critical constraint (from review):**
- The current `services/*.py` modules import the shared `db = DatabaseManager()` singleton at module level. The ingestion worker **must not** reuse that singleton implicitly — it needs its own `DatabaseManager()` instance (its own connection pool) so a worker restart does not depend on the API process and vice versa. This should be resolved in Phase 0 by making services accept a `db` instance or use a factory.

---

## 4. End-to-end data flow

1. A machine publishes a message to a documented topic, e.g., `factory/line-1/M102/telemetry`.
2. Mosquitto authenticates the client, checks topic permissions, and routes the message to subscribers.
3. The ingestion worker decodes the payload and validates its schema, machine identity, sensor tag, units, value, and timestamp.
4. Invalid messages are counted and logged with safe diagnostic context; they must not crash the consumer.
5. Valid readings are normalized to UTC and checked against the chosen duplicate policy.
6. The worker persists the reading through the shared service/repository layer. If a queue is adopted, the worker drains the queue at the storage pace rather than writing synchronously per message; for the MVP, direct synchronous persistence is acceptable at modest telemetry volume.
7. The alarm evaluator checks configured thresholds and records state transitions. For the MVP this is a simple per-reading threshold check against configured `warning_threshold`/`critical_threshold` values in the `machine_sensors` table; stateful composite conditions (e.g., "N breaches in T minutes") are a later extension.
8. The dashboard fetches current status and recent readings from the API. Historical views query time-bounded data.
9. If the broker or database fails, the worker reconnects and follows an explicit retry/replay policy. Delivery guarantees must be designed end-to-end rather than assumed from MQTT QoS alone.

---

## 5. MQTT contract

**Topic convention:**
```text
factory/{site_id}/{machine_id}/telemetry
factory/{site_id}/{machine_id}/status
factory/{site_id}/{machine_id}/event
```

Start with telemetry and status. Add event topics when the event schema and ownership are defined.

**Example telemetry payload:**
```json
{
  "schema_version": "1.0",
  "message_id": "0192f0c0-4f43-7c3a-a987-123456789abc",
  "machine_id": "M102",
  "sensor_tag": "TEMP",
  "value": 76.4,
  "unit": "degC",
  "measured_at": "2026-10-13T03:35:00Z"
}
```

**Contract rules:**
- `schema_version` is required; only one active schema version is accepted per topic family. Breaking changes get a new version and are evaluated separately.
- `message_id` is a stable identifier used for duplicate detection.
- `machine_id` must match the machine encoded in the topic.
- `sensor_tag` and `unit` must be allowed for that sensor. Units use a controlled vocabulary per sensor type (temperature: `degC`, `degF`; pressure: `bar`, `psi`, `kPa`; the allowed set is defined in the `machine_sensors` table or a reference table, not inferred from the payload).
- `value` must be numeric and finite; define valid operating and engineering ranges.
- `measured_at` must be timezone-aware ISO 8601. Record ingestion time (`received_at`) separately in the `telemetry_messages` table or readings row metadata so message lag can be measured.
- Payload size and accepted schema version should be bounded.
- Never trust topic or payload identity without validation and authorization rules.

**Delivery policy:**
- Begin with **QoS 1** when at-least-once delivery is appropriate.
- Assume duplicate delivery is possible.
- Use a unique message identifier or a well-defined natural key to make persistence idempotent.
- Acknowledge/complete processing only according to the selected Paho callback and QoS flow; do not claim database durability simply because the callback received a message.
- Decide whether a failed message is retried in memory, persisted to a durable local queue, or routed to a dead-letter workflow. Document data-loss behavior for process crashes.

---

## 6. Data model

Retain the existing `machine_schema.machines` and `machine_schema.sensor_readings` tables unless review shows a specific gap.

**Existing core tables:**
- **machines** — `id` (primary key), `machine_name` (unique machine identifier), `created_at` (registration timestamp)
- **sensor_readings** — `id` (primary key), `machine_id` (FK to machines), `sensor_tag` (sensor identifier), `sensor_value` (numeric value), `timestamp` (measured timestamp)

**Recommended additions after migration review:**

- **machine_sensors** — `id`, `machine_id`, `sensor_tag`, `unit`, `display_name`, `warning_threshold`, `critical_threshold`, `enabled`. Unique constraint on `(machine_id, sensor_tag)`.
- **telemetry_messages** (optional, useful if end-to-end traceability is required) — `message_id`, `machine_id`, `received_at`, `processing_status`, `failure_reason`. Unique `message_id`; avoid storing unlimited duplicate raw payloads without a retention policy.
- **machine_status** — `machine_id`, `connection_state`, `last_seen_at`, `last_reading_at`, `updated_at`. Connectivity and telemetry freshness are different signals. A connected MQTT client does not prove that the machine is producing healthy readings.
- **alarm_events** — `id`, `machine_id`, `sensor_tag`, `severity`, `event_type`, `observed_value`, `threshold_value`, `opened_at`, `acknowledged_at`, `resolved_at`, `status`. Keep alarm transitions auditable. Define whether repeated threshold breaches update an existing active alarm or create separate events.

**Indexing and retention:**
- Preserve and verify the existing `(machine_id, timestamp)` and timestamp indexes.
- Add indexes for active alarms and machine/sensor lookups as query patterns require.
- Use UTC consistently.
- Establish a retention and archival policy as soon as `telemetry_messages` and `alarm_events` are added (Phase 3), not deferred to Phase 5. These tables accumulate data from day one; a retroactive retention policy is harder than a designed one.
- Consider time partitioning only after measuring volume and query performance; choose partition keys and uniqueness constraints carefully.

---

## 7. Backend API plan

Keep existing endpoints backward-compatible. Add focused endpoints:

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/v1/overview` | Dashboard KPIs and counts |
| `GET` | `/api/v1/machines` | Machine list and metadata |
| `GET` | `/api/v1/machines/{id}/status` | Connectivity, freshness, latest values |
| `GET` | `/api/v1/machines/{id}/readings/latest` | Latest reading per sensor |
| `GET` | `/api/v1/readings` | Filter by machine, sensor, and time range with pagination |
| `GET` | `/api/v1/readings/statistics` | Min/max/avg for a bounded period |
| `GET` | `/api/v1/alarms` | Filter alarms by status, severity, machine, time |
| `POST` | `/api/v1/alarms/{id}/acknowledge` | Acknowledge an alarm, subject to authorization |
| `GET` | `/health/live` | Process liveness |
| `GET` | `/health/ready` | Dependency readiness, including database availability |

These are proposed additions, not claims about current routes. Keep current routes working while a versioned API is introduced. Do not expose raw database errors or credentials in HTTP responses.

---

## 8. Dashboard information architecture

**Screen A — Operations overview:**
- KPI strip: total machines, healthy, warning, critical, offline/stale.
- Machine status table with last-seen time and most important current values.
- Active alarms ordered by severity and age.
- Telemetry freshness indicator.
- A visible timestamp showing when dashboard data was last refreshed.

**Screen B — Machine detail:**
- Machine identity, site/line, connectivity, telemetry freshness.
- Current values for each configured sensor, with units and threshold context.
- Time-series chart with selectable time window.
- Recent alarms and machine events.
- Historical readings table and export action where authorized.

**Screen C — Alarms and events:**
- Active, acknowledged, resolved states.
- Severity, machine, sensor, observed value, threshold, event time.
- Filters by site, machine, severity, status, time range.
- Acknowledgement and resolution history.

**Screen D — Historical analysis:**
- Machine and sensor selectors.
- Time-range selection + server-side pagination.
- Trends, min/max/avg, CSV export.
- Clear empty, loading, stale-data, and API-error states.

**Visual direction:**
- Industrial operations-console layout: compact status cards, dense but readable machine table, prominent alarm severity, restrained colors, dark or light theme based on operator environment, charts with clearly labeled units and time axes. Avoid decorative charts that do not answer an operational question.

---

## 9. Live update strategy

**Release 1:** Poll the API at a controlled interval (e.g., every 2–5 seconds for the overview, subject to database load). Use bounded time windows, efficient latest-reading queries, and request cancellation on navigation.

**Release 2:** Add Server-Sent Events (SSE) or WebSockets if polling latency or request load becomes a measured problem.

Do not connect every browser directly to MQTT or expose broker credentials to the frontend. The backend remains the access-control and data-contract boundary.

---

## 10. Reliability, security, and observability

**Reliability:**
- Use bounded connection and statement timeouts.
- Define transaction boundaries and rollback behavior.
- Make ingestion idempotent.
- Apply bounded retries with backoff and jitter.
- Avoid unbounded in-memory queues.
- Track stale telemetry independently of process health.
- Provide graceful shutdown and close database/MQTT resources.
- Test broker outages, database outages, duplicate messages, and malformed payloads.

**Security:**
- Use TLS/mTLS with certificate validation; never disable hostname verification to work around certificate errors.
- Enforce broker authentication and topic ACLs.
- Store secrets in environment configuration or a secret manager, not source control.
- Rotate credentials exposed in archives.
- Protect dashboard and API write operations with authentication and authorization.
- Restrict CORS, payload sizes, request rates, and sensitive logs.
- Keep control/actuation commands out of the first release.

**Observability:**
Track at minimum:
- MQTT connection state and reconnect count.
- Messages received, accepted, rejected, duplicated, and persisted.
- Ingestion processing latency and database write latency.
- Database pool usage, timeouts, and failures.
- Age of the latest reading per machine.
- Active alarms and alarm-resolution time.
- API latency and HTTP error rates.

Use structured logs with correlation/message IDs where practical. Do not log credentials, private keys, or complete sensitive payloads.

---

## 11. Testing strategy

1. **Unit tests:** payload validation, timestamp normalization, threshold logic, duplicate policy.
2. **Service tests:** database transaction and error behavior, using existing test conventions.
3. **API tests:** filters, pagination, authorization, validation, and error responses.
4. **Integration tests:** a test broker plus PostgreSQL for publish-to-persist behavior.
5. **Failure tests:** broker unavailable, database unavailable, reconnect, malformed payload, duplicate delivery, and worker restart.
6. **Dashboard tests:** loading, empty, stale, error, and populated states.
7. **End-to-end acceptance:** publish a known telemetry message and verify it appears in PostgreSQL, API responses, and the dashboard within the agreed latency target.

Keep the current API tests passing throughout the work.

---

## 12. Phased implementation plan

**Phase 0 — Baseline and cleanup:**
- Review existing routes, services, schema, configuration, and tests.
- Rotate exposed database credentials in the repository `.env` file.
- Confirm development and test database separation.
- Document current behavior and compatibility constraints.
- Refactor services to accept a `db` instance or use a factory so the ingestion worker can run with its own `DatabaseManager()` and connection pool, not the module-level singleton. **Critical-path item from the review.**
- Decide the authentication model for the dashboard API.

**Exit criteria:** baseline tests pass; architecture and current endpoint contracts are documented; services refactored for independent worker use; auth model decision recorded.

**Phase 1 — Telemetry contract and broker:**
- Define topic names and JSON schema.
- Verify certificate validation, broker ACLs, and client authentication.
- Add a repeatable development telemetry publisher.

**Exit criteria:** authorized clients publish valid messages; unauthorized connections/topics are rejected. **QoS note:** the team has not yet used QoS 0/1/2 in practice (current demo runs on the default). Phase 1 exit criteria should include: team can explain QoS 0/1/2 tradeoffs and has tested at least QoS 1 on the broker, since the delivery policy in §2.5 assumes QoS 1.

**Phase 2 — Ingestion worker:**
- Create a separately runnable worker using existing Paho conventions.
- Add validation, normalization, logging, idempotency, and database persistence.
- Add retry/recovery behavior and worker health reporting.
- **Consider repurposing the existing `import_batches` ledger** as a message-level ledger (one row per `message_id` with processing status) for end-to-end traceability, rather than building a new table from scratch. The existing SHA-256 fingerprint pattern translates naturally to a message-level dedup/ack ledger.

**Exit criteria:** a published message is persisted once logically, and failures are observable and recoverable under the documented policy.

**Phase 3 — Status and alarm backend:**
- Add machine freshness/status and sensor configuration as needed.
- Add threshold rules and auditable alarm state transitions.
- Add dashboard-focused API endpoints without breaking existing routes.

**Exit criteria:** status and alarm APIs return real database-backed results with tests.

**Phase 4 — Dashboard MVP:**
- Build overview, machine detail, alarm list, and history views.
- Integrate the existing API.
- Implement loading, stale, empty, and error states.
- Use actual telemetry; do not substitute mock values for live backend data.

**Exit criteria:** an end-to-end published reading is visible in the appropriate dashboard view.

**Phase 5 — Hardening and deployment:**
- Run failure and load tests.
- Establish retention, backup, restore, and operational runbooks.
- Add metrics, alerting, access control, and deployment configuration.
- Measure before introducing queues, caching, or additional infrastructure.

**Exit criteria:** documented operational limits, tested recovery behavior, and a repeatable deployment procedure.

---

## 13. Suggested repository layout

Adapt to the existing repository instead of mechanically renaming working modules.

**Repository restructure approach (from review):**
- The proposed layout implies moving existing modules (`app.py`, `config.py`, `routes/`, `services/`, `database/`, `utils/`, `tests/`) under a `backend/` directory.
- Do **not** do this as a big-bang rename. Prefer an incremental approach: add `ingestion/` alongside the existing flat structure first (Phase 2), keep existing modules where they are until a concrete reason to move them arises, and only restructure when a file's new home is unambiguous. Each move must keep the test suite green.
- The current working copy at `./` and the archive at `/f/Intern_Training/MQTT/Machine_Sensor_API/` are both valid entry points; confirm which tree is authoritative before restructuring.

```text
iiot-platform/
├── backend/
│   ├── app.py
│   ├── config.py
│   ├── routes/
│   ├── services/
│   ├── database/
│   ├── utils/
│   └── tests/
├── ingestion/
│   ├── mqtt_consumer.py
│   ├── payload_schema.py
│   ├── processor.py
│   └── tests/
├── dashboard/
│   ├── src/
│   └── tests/
├── mqtt/
│   ├── mosquitto.conf.example
│   └── acl.example
├── migrations/
├── scripts/
│   └── publish_test_telemetry.py
├── docs/
│   ├── architecture.md
│   ├── telemetry-contract.md
│   └── operations-runbook.md
├── .env.example
├── .gitignore
└── README.md
```

Do not commit real certificates, private keys, passwords, production broker configuration, or real `.env` files.

---

## 14. Key decisions to confirm

- Target environment: local Windows development first, then Linux/server deployment?
- Frontend: Vue 3 + JavaScript + Tailwind, or another existing stack?
- Telemetry rate: messages per machine per second/minute and expected machine count?
- Update target: is a 2–5 second dashboard refresh sufficient, or is sub-second delivery required?
- Alarm ownership: fixed configuration, database-managed thresholds, or operator-configurable thresholds?
- Data retention: how long must raw telemetry and alarm history remain available?
- Access model: single operator, team roles, or multiple sites/tenants?
- **Authentication model (critical, from review):** the current API has no authentication at all ("all endpoints are open on purpose in this local learning setup"). Dashboard write operations (alarm acknowledge) and any production deployment need auth. Decide the auth model **before Phase 3** (status/alarm backend), not as a Phase 5 hardening item, because the alarm acknowledgement endpoint and any write path need an authorization boundary from the start. Options range from simple API-key/token auth for the dashboard to a full JWT/OAuth role-based model; pick the minimum that covers the access model decision above.

Until these are confirmed, the plan assumes a single-site MVP, modest telemetry volume, a 2–5 second initial dashboard refresh, threshold-based alarms, and no remote machine control.

---

## 15. Definition of done

The first usable release is complete when:
- The broker accepts only appropriately authenticated and authorized clients (Mosquitto mTLS + ACLs; current config at `C:/Program Files/Mosquitto/mosquitto.conf`).
- All secrets rotated from the current `.env` in the repository (Phase 0 action).
- Valid MQTT telemetry reaches PostgreSQL through the ingestion worker.
- Invalid and duplicate messages follow documented, tested policies.
- Existing API functionality and tests remain intact.
- The dashboard displays database-backed machine status, current readings, trends, and alarms.
- Stale data is clearly distinguished from healthy data.
- Failures are logged and observable without exposing secrets.
- A restart and recovery procedure is documented and tested.
- Deployment steps, configuration variables, and known limitations are documented.

---

**Source:** `Live_IIoT_Monitoring_Platform_Plan.md`
