# Live IIoT Monitoring Web Application — Step-by-Step Architecture

**Built from:** the existing Machine Sensor API, MQTT/Mosquitto broker, Paho client, cron_jobs/partitioning, log_rotation, RegEx log monitor, and training documentation in `/f/Intern_Training/`.

**Audience:** first-time builder who already has sensor readings in PostgreSQL and an API exposing them, and wants the full architecture to add live monitoring.

**Scope:** end-to-end — data source, ingestion, database, API, dashboard, KPIs, alarms, observability, security, testing, deployment, retention. Every layer includes what exists today and what to add.

------------------------------------------------------------------------

## How to read this architecture

This document has two parts:

1. **The plan** — Stage 0 through Stage 10. The generic step-by-step architecture for a live IIoT monitoring web application, written as a reusable blueprint. It says what a live monitoring app is, the stages every such app goes through, and the requirements each stage produces.
2. **How the plan can be implemented in different ways** — one section per stage, comparing real alternatives (simulator vs MQTT, scheduler vs while-true vs tail-f vs queue, APScheduler vs cron, separate worker vs in-process, poll vs SSE vs WebSocket, open API vs API-key vs JWT, etc.). These are decision points, not one prescribed implementation.
3. **Our actual build (w.r.t my learning)** — the `.md` companion file. That file is the record of what was actually built in this repo: the real stack, the real decisions, the real code paths, the real lessons. This `LIVE_MONITORING_ARCHITECTURE.md` is the plan and its implementation options. `.md` is our build.

Do not try to build all the implementation options. Pick the one that matches your target (local learning, MVP dashboard, production deployment) and read that column in each stage.

------------------------------------------------------------------------

## Stage 0 — What we are monitoring (define the operational question)

**What this stage does:** Define the single operational question the dashboard answers. Everything downstream — KPIs, screens, API endpoints, alarm thresholds — follows from this.

**Plan (what a live monitoring app needs here):**
- A defined set of machine states: healthy, warning, critical, offline, stale
- A definition of "stale" (no new reading for N seconds — 60 is a reasonable default)
- A definition of "healthy" (recent reading, in range, no active alarm)
- The list of sensor tags and their units (so the dashboard knows what it is showing)

**How this stage can be implemented in different ways:**

| Decision | Option A | Option B | Option C |
|---|---|---|---|
| Operational question | "Is anything wrong right now?" — status + alarms | "What is the trend?" — historical analysis first | "Both" — overview + history (most dashboards) |
| Machine state model | 5-state enum (healthy/warning/critical/offline/stale) | Binary up/down plus severity | Severity-only, no freshness separate from alarms |
| "Stale" definition | Time-based (no reading for N seconds) | Event-based (no MQTT connection) | Both, combined in a status table |

**Our actual build (w.r.t my learning):** `.md` Stage 0 — the operational question is "Which machines are alive, which are stale, which are in warning or critical state, and what are their current readings?" The existing project (Machine Sensor API capstone) gives the starting point: machines have sensor readings, the API exposes them, and the training record (`TRAINING_DOCUMENTATION.md`, §3.8) documents the capstone as-built. The plan here does not invent a new question — it takes the one the project already implies and makes it explicit.

------------------------------------------------------------------------

## Stage 1 — Data source (what feeds the system)

**What this stage does:** Produce timestamped sensor readings, either from real machines or a simulator for development.

**Plan (what a live monitoring app needs here):**
- Readings carry a timestamp in UTC (ISO 8601 with Z, or Unix time)
- Each reading has machine_id, sensor_tag, numeric sensor_value
- For live MQTT: the payload is validated before persistence (schema_version, machine_id matches topic, sensor_tag is known, value is numeric/finite, measured_at is valid ISO 8601)
- The source of truth for "latest reading" is defined — last row in `sensor_readings` per machine/sensor, or a separate `machine_status` table updated by the ingestion worker

**How this stage can be implemented in different ways:**

| Decision | Option A — local learning | Option B — MVP with real broker | Option C — production |
|---|---|---|---|
| Data source | Existing pickle import + replay simulator | Mosquitto broker + Paho subscriber + simulator fallback | Real machines publishing over mTLS, with simulator for dev only |
| Transport | File import (CSV from pickle) | MQTT over TLS (port 8883, mTLS) | MQTT over mTLS, ACLs, QoS 1, retained/last-will where needed |
| Payload shape | Whatever the existing importer accepts | JSON contract (schema_version, message_id, machine_id, sensor_tag, value, unit, measured_at) | Same contract, versioned, with unit vocabulary and range checks |
| Source of truth for "latest" | `SELECT ... ORDER BY timestamp DESC LIMIT 1` per machine/sensor | `machine_status` table updated by ingestion worker | `machine_status` + `telemetry_messages` ledger for traceability |

**Our actual build (w.r.t my learning):** `.md` Stage 1 — the existing project already has:
- Pickle snapshot `all_topics_20250328-114500.pkl` → CSV → PostgreSQL, ~55,918 readings across 12 machines (capstone `readme.md` §3.8, `services/pickle_importer.py`)
- Mosquitto broker on Windows as a service, port 8883, TLS/mTLS with `require_certificate true`, `use_identity_as_username true`, `allow_anonymous false` (`MQTT/mqtt_readme.md`)
- Paho client demo `MQTT/Python/mqttdemo.py` — Callback API v2, 5 callbacks, return-code checks, `logging.exception` on every error path

What is not yet built: a telemetry simulator and a decision on the live payload shape. The IIoT platform plan (`Live_IIoT_Monitoring_Platform_Plan.md` §5) proposes the JSON contract and topic convention `factory/{site_id}/{machine_id}/telemetry`. For a local-learning build, the simulator path (Option A) is the right first move — it lets the dashboard be built before any real MQTT client is attached.

------------------------------------------------------------------------

## Stage 2 — Ingestion (getting data into the database safely)

**What this stage does:** Take incoming messages (MQTT or simulator), validate, normalize, deduplicate, and persist them. This is the gate between "data arrived" and "data trusted."

**Plan (what a live monitoring app needs here):**
- Validation at the boundary, once, centrally — then trust downstream
- UTC everywhere internally; convert to local time only at the edge (dashboard display)
- Parameterized SQL only; f-strings only for identifiers
- Transactions: commit on success, rollback on failure, cleanup in finally
- Bound everything: connection timeout, statement timeout, batch size, retry count, retry backoff

**How this stage can be implemented in different ways:**

| Decision | Option A — file import (existing) | Option B — MQTT ingestion worker (plan) | Option C — queue-buffered |
|---|---|---|---|
| Ingress | `.pkl → CSV → PostgreSQL` via pickle importer | Subscribe → decode → validate → normalize → insert via reading_service | MQTT → consumer → bounded queue → worker → PostgreSQL |
| Dedup | SHA-256 import ledger (`import_batches`) | `message_id` from payload, idempotent skip | Same, plus queue dedup |
| Batch size | 5000 via `execute_values` | Single insert or small batches, depending on rate | Batch drain at storage pace |
| Failure model | Rollback bad file, skip bad rows | `logging.exception`, continue to next message; bounded retries with backoff + jitter | Durable local queue or dead-letter for failed messages |
| Process boundary | In-process with the API (one script) | Separate Python process, its own DB pool | Separate processes, with queue as the buffer |

**Our actual build (w.r.t my learning):** `.md` Stage 2 — the existing project has the pickle importer (`services/pickle_importer.py`) as the ingestion template: two-stage pipeline, row validation, batch inserts, SHA-256 ledger, skip broken rows. The reading service (`services/reading_service.py`, `add_reading()`) shows single-reading insert with parameterized SQL and FK error → 400. The Paho demo shows the callback patterns and the lesson that return-code checks and callback checks both matter. What is not yet built: the MQTT ingestion worker as a separate process. For a local-learning build, Option A is already done; Option B is the next step when you add live MQTT. Option C (queue) is explicitly not an MVP requirement — the IIoT Python guide identifies the queue pattern, but at modest volume direct persistence with bounded retries is acceptable, and the data-loss behavior for process crashes should be documented rather than hidden behind a queue.

------------------------------------------------------------------------

## Stage 3 — Database (what the dashboard queries)

**What this stage does:** Store machines, readings, status, alarms, and (optionally) message-level traceability. Provide indexes for the dashboard's query patterns.

**Plan (what a live monitoring app needs here):**
- Tables for machines, readings, sensor config, machine status, alarm events, (optional) telemetry messages
- Indexes for the dashboard query patterns: active alarms by severity/age, alarms for one machine, stale machines, latest reading per machine/sensor
- Retention policy decided when the table is added, not later
- Enforce only claims that can be proven (no unprovable unique constraints)

**How this stage can be implemented in different ways:**

| Decision | Option A — MVP schema | Option B — traceable schema | Option C — partitioned production |
|---|---|---|---|
| Status backing | `machine_status` table (connection_state, last_seen_at, last_reading_at) | Same + `telemetry_messages` ledger (message_id, received_at, processing_status) | Same, with time-range partitioning on `sensor_readings` by timestamp |
| Alarm model | `alarm_events` lifecycle table | Same, plus per-transition audit columns | Same, with retention/archival policy enforced |
| Indexes | Minimal: machine_status on last_seen_at, alarm_events on (status, severity, opened_at) | Same + telemetry_messages on message_id | Partitioned indexes, plus the existing (machine_id, timestamp) etc. |
| Retention | Decide per table at creation | Decide + enforce (e.g. 7 days telemetry_messages, 90 days alarm_events active) | Partitioning + drop old partitions |

**Our actual build (w.r.t my learning):** `.md` Stage 3 — the existing project already has `machines`, `sensor_readings`, `import_batches`, the three indexes (`(machine_id, timestamp)`, `(sensor_tag)`, `(timestamp)`), a connection pool (`ThreadedConnectionPool`, min 2/max 10), `connect_timeout=5`, `statement_timeout=15000`, context managers that always return the connection, and schema namespace `machine_schema` (`database/schema.py`, `database/connection.py`, `config.py`). The critical lesson from the training record (`TRAINING_DOCUMENTATION.md` §3.10) is the dropped unique constraint: an unprovable `(machine_id, sensor_tag, timestamp)` constraint multiplied one file ~211× into 11.8M rows; the fix was the import ledger — fingerprint the source, not the business claim. Any new unique constraint (e.g. `machine_sensors (machine_id, sensor_tag)`, `telemetry_messages.message_id`) must be provable. For a local-learning build, Option A is the right start; `telemetry_messages` and partitioning are optional until volume or traceability demands them. The cron_jobs project (`cron_jobs/cronjobs_readme.md`) already demonstrates PostgreSQL range partitioning with just-in-time partition creation and a composite primary key — that is the reference if you need it later.

------------------------------------------------------------------------

## Stage 4 — API (the dashboard's data contract)

**What this stage does:** Expose current status, latest readings, historical ranges, statistics, and alarms to the dashboard through validated HTTP endpoints. The dashboard is a heavy API client — every panel polls, so endpoints must be cheap.

**Plan (what a live monitoring app needs here):**
- Endpoints for overview, machine status, latest readings, historical queries, statistics, alarms
- Versioned namespace (`/api/v1/`) so the dashboard can depend on stable endpoints while existing routes stay backward-compatible
- `generated_at` or `updated_at` on snapshot responses so the dashboard knows how fresh the data is
- Do not expose raw database errors; do not return `Decimal` as strings; paginate everything that can be large
- Auth before write operations (alarm acknowledge), not after

**How this stage can be implemented in different ways:**

| Decision | Option A — extend existing API | Option B — new versioned namespace | Option C — full REST + auth upfront |
|---|---|---|---|
| Endpoint layout | Add new routes alongside `/machines`, `/readings` | Add `/api/v1/` namespace; keep old routes untouched | Same, with auth middleware from the start |
| Auth model | None (local learning, open on purpose) | API key / token for dashboard write ops | JWT / OAuth role-based |
| Error discipline | 8 global error handlers (existing) — keep for new endpoints | Same | Same, plus auth error responses |
| Pagination | Existing default page size (1000) | Reuse; add cursor/offset as needed | Same, with explicit limits |

**Our actual build (w.r.t my learning):** `.md` Stage 4 — the existing project already has a strong API foundation: CRUD on machines/readings, `GET /readings/statistics` (MIN/MAX/AVG with `::float8` casts so they return real JSON numbers, not strings), `GET /readings/export` (streaming CSV), `GET /health` (200/503), `POST /readings/import`, shared validators (`utils/validation.py`), shared filter builder (`_build_reading_filters` in `services/reading_service.py`), honest status codes (200/201/400/404/405/409/500/503), eight global error handlers in `app.py`, and the factory pattern so waitress/wsgi.py/tests all import cleanly. The training record (`TRAINING_DOCUMENTATION.md` §3.9–§3.10) documents the hardening: 409/400 exception mapping, JSON-number statistics, shared validators, the single filter builder. What is not yet built: the dashboard-specific endpoints (`/api/v1/overview`, `/api/v1/machines/<id>/status`, `/api/v1/alarms`, etc.) and auth for write operations. For a local-learning build, Option A is fine; Option B is the cleaner path when a dashboard will depend on stable contracts; auth (Option C) should be added before or at the same time as the alarm acknowledge endpoint, not as a Phase 5 afterthought — that is the explicit decision recorded in `Live_IIoT_Monitoring_Platform_Plan.md` §14.

------------------------------------------------------------------------

## Stage 5 — Dashboard (what the operator sees)

**What this stage does:** Present operational status, current readings, trends, and alarms in a browser. Consumes the API layer. Does NOT connect directly to MQTT, and does NOT hold its own copy of the database.

**Plan (what a live monitoring app needs here):**
- Four screens: operations overview, machine detail, alarms/events, historical analysis
- Visual direction: industrial operations-console layout, restrained colors, color for severity not decoration, dark/light by environment, charts with labeled units and time axes, no decorative charts
- Live update: poll 2–5s first; SSE/WebSockets only if polling is proven to be the bottleneck
- Handle empty states, stale states, API error states visibly; stale data visibly different from healthy

**How this stage can be implemented in different ways:**

| Decision | Option A — local learning MVP | Option B — full dashboard | Option C — real-time Ops console |
|---|---|---|---|
| Frontend stack | Any — Flask-rendered, Vue, React, plain JS | Vue 3 + TypeScript (as explored in `mqtt_dashboard_changes/`) or React | Same, with component library for dense tables |
| Live update | Poll 2–5s | Poll, then add SSE if load demands | SSE or WebSocket from the start if sub-second is required |
| Charts | One time-series chart per machine, selectable window | Multiple charts, selectable windows (1h/6h/24h/7d) | Same, plus alarm timeline, heatmap, etc. |
| States | Empty/stale/error handled explicitly | Same, plus loading skeletons | Same, plus acknowledge flow, user identity |

**Our actual build (w.r.t my learning):** `.md` Stage 5 — the existing project has nothing dashboard-specific yet; the API is the backend only. The `mqtt_dashboard_changes/` folder contains a Vue 3 + TypeScript dashboard with SSE, but that is a separate exploration, not the basis for this architecture. For a local-learning build, Option A is the right scope: build Screen A first with real database-backed data (that proves the pipeline from database → API → browser), then add Screen B's chart, then C and D. The IIoT platform plan (`Live_IIoT_Monitoring_Platform_Plan.md` §8) restates the four screens and visual direction; this plan repeats that as build guidance, not as a prescription. The live-update decision is explicit: poll first, measure, then add SSE/WebSockets only if needed — never on day one, and never connect the browser directly to MQTT.

------------------------------------------------------------------------

## Stage 6 — KPIs (what to measure and show)

**What this stage does:** Define the numbers the operator sees on the dashboard (operator KPIs) and the numbers you, the builder, use to know the system is healthy (system KPIs).

**Plan (what a live monitoring app needs here):**
- Operator KPIs: total machines, healthy, warning, critical, offline/stale, active alarms, latest reading age, telemetry freshness — all computable from the database and cheap to query
- System KPIs: messages received, accepted, rejected, duplicated, persisted, ingestion latency, database write latency, pool usage, timeouts, API latency, API error rate, stale machine count
- Start with operator KPIs on the dashboard and log the system KPIs; do not build a full Prometheus dashboard on day one
- The first question is "is the data flowing?" — received → accepted → persisted; if those three numbers line up, the pipeline works

**How this stage can be implemented in different ways:**

| Decision | Option A — minimal | Option B — dashboard + logs | Option C — metrics stack |
|---|---|---|---|
| Operator KPIs | Overview endpoint computes counts from machine_status + alarm state | Same, with latest_reading_age pre-computed in machine_status | Same, with caching if needed |
| System KPIs | Log messages received/accepted/persisted | Structured logs with message_id as correlation key | Prometheus-style metrics (counters, histograms, gauges) + collector |
| Correlation | message_id from MQTT payload | Same, plus request IDs when available | Same, plus trace IDs across services |

**Our actual build (w.r.t my learning):** `.md` Stage 6 — the existing project has nothing dashboard-specific yet for KPIs. The system-facing basis exists: rotating logs (`utils/logger.py`, 10 MB × 5, UTC, `logger.propagate = False`), the `/health` endpoint (200/503), the connection pool with min/max (2/10) which gives pool usage context. The training record (`TRAINING_DOCUMENTATION.md` §3.11) documents the rotating-JSON-logging learning — JSON-per-line is the format log collectors want, free-text is for humans. For a local-learning build, Option A→B is the right sequence: add the operator KPIs to the overview endpoint, log the system KPIs with structured logs and message_id as the correlation key. Option C (Prometheus) is a later step, not day one.

------------------------------------------------------------------------

## Stage 7 — Alarms (when something is wrong)

**What this stage does:** Detect threshold breaches and record the alarm lifecycle: opened → acknowledged → resolved.

**Plan (what a live monitoring app needs here):**
- Threshold configuration per machine/sensor (`warning_threshold`, `critical_threshold`) — configurable, not hard-coded
- Alarm evaluation when a reading arrives: compare value vs thresholds; open/continue critical or warning; resolve when below warning
- Alarm lifecycle table (`alarm_events`): every transition is a row; lifecycle is opened → acknowledged → resolved
- Alarm state decision made explicit: one active alarm per (machine, sensor, severity) at a time; repeated breaches update the existing alarm, not create new ones (avoid alarm spam)
- Survive restarts by storing state in the database, not in the worker's memory
- Acknowledgement is an operator action protected by auth; do not auto-acknowledge

**How this stage can be implemented in different ways:**

| Decision | Option A — simple threshold | Option B — stateful lifecycle | Option C — composite conditions |
|---|---|---|---|
| Trigger | value >= critical_threshold → critical; >= warning_threshold → warning | Same, with one active alarm per (machine, sensor, severity) | Same, plus "N breaches in T minutes" later |
| State storage | In-memory flag (does not survive restart) | `alarm_events` table, state survives restart | Same, plus event history for every transition |
| Resolution | Value < warning_threshold → resolve | Same, or operator action | Same, plus auto-acknowledge rules (later) |
| Spike handling | Every breach opens a new alarm (spam) | Update existing active alarm's observed_value/last_seen_at | Debounce / hysteresis (later) |

**Our actual build (w.r.t my learning):** `.md` Stage 7 — the existing project has nothing alarm-specific yet. The capstone stores readings, not events; the statistics endpoint (min/max/avg) is historical, not real-time. The plan here is Option B (stateful lifecycle in `alarm_events`), because alarms are a state machine and the lifecycle must be persisted so it survives worker restarts — that is the explicit decision, and the reason the lifecycle is stored, not held in memory. For a local-learning build, Option A (simple threshold, in-memory) is the smallest step, but it does not survive restarts; Option B is the one to build when you add the alarm table, because it matches the requirement that alarm state survive a restart. The alarm-spam decision (one active alarm per machine/sensor/severity) is recorded as the recommended MVP rule, flagged as a decision to make explicit rather than leave implicit.

------------------------------------------------------------------------

## Stage 8 — Observability, security, and operations

**What this stage does:** Make the system observable (logs, health, metrics), secure (TLS/mTLS, ACLs, secrets, auth, validation, CORS), and operable (retention, backup/restore, restart/recovery, deployment).

**Plan (what a live monitoring app needs here):**
- Observability: rotating logs extended to ingestion metrics; liveness + readiness health endpoints; metrics when a collector is available (not before the operational dashboard works)
- Security: MQTT mTLS kept; broker ACLs; secrets in env, not source control; dashboard/API auth for write operations; input validation at the boundary for both API and MQTT; CORS/payload/rate limits when exposed beyond localhost
- Operations: retention decided when the table is added; PostgreSQL backup before the dashboard goes live; restart/recovery docs; separate ingestion worker process; document how to run and restart each without affecting the other

**How this stage can be implemented in different ways:**

| Decision | Option A — local learning | Option B — hardened MVP | Option C — production ops |
|---|---|---|---|
| Health endpoints | `/health` (existing, 200/503) | Add `/health/live` + `/health/ready` | Same, plus dependency health (broker, DB) |
| Logs | Rotating file (existing) | Structured logs for ingestion metrics, message_id correlation | JSON-per-line + collector + dashboards |
| MQTT security | mTLS already configured (port 8883, require_certificate, use_identity_as_username, allow_anonymous false) | Keep + add ACLs per topic | Same + cert rotation, monitor expiration |
| API security | Open on purpose (local learning) | API key / token for dashboard write ops | JWT/OAuth, CORS, rate limits, payload caps |
| Deployment | waitress on port 8080 (existing); ingestion worker in-process or as a second script | Separate ingestion worker process; restart/recovery docs | Same + supervisor/systemd/Docker, backup/restore runbooks |

**Our actual build (w.r.t my learning):** `.md` Stage 8 — the existing project already has most of the security and observability foundation: MQTT mTLS (Mosquitto config on port 8883 with `require_certificate true`, `use_identity_as_username true`, `allow_anonymous false` — `MQTT/mqtt_readme.md`), `.env` + fail-fast `config.py`, parameterized SQL everywhere, rotating logs (`utils/logger.py`), `/health` endpoint (200/503), waitress on port 8080 (`app.py`, `wsgi.py`). The training record (`TRAINING_DOCUMENTATION.md` §3.10) documents the production rebuild: Flask dev server → waitress, fresh connection per request → `ThreadedConnectionPool` with context managers, `connect_timeout=5` + `statement_timeout=15000`, rotating logs 10 MB × 5. What is not yet built: liveness/readiness endpoints, dashboard/API auth for write operations, broker ACLs, CORS/payload/rate limits, the separate ingestion worker as its own process, backup/restore, retention policy enforcement. For a local-learning build, Option A is the existing state; Option B is the next step when you expose the dashboard beyond localhost or add alarm acknowledge; Option C is later.

------------------------------------------------------------------------

## Stage 9 — Testing (verify each stage before building the next)

**What this stage does:** Verify each stage before building the next. Keep the existing tests passing throughout. Test error branches first — they are where systems actually fail.

**Plan (what a live monitoring app needs here):**
- Unit tests: payload validation, timestamp normalization, threshold logic, duplicate policy
- Service tests: database transaction and error behavior (fake pool pattern), alarm lifecycle
- API tests: new endpoints, filters, pagination, auth, validation, error responses
- Integration tests: test broker + PostgreSQL for publish-to-persist
- Failure tests: broker unavailable, database unavailable, malformed payload, duplicate delivery, worker restart
- Dashboard tests: loading, empty, stale, error, populated states; polling behavior; alarm acknowledge flow
- End-to-end acceptance: publish a known telemetry message and verify it appears in PostgreSQL, the API response, and the dashboard within the agreed latency target

**How this stage can be implemented in different ways:**

| Decision | Option A — keep existing suite | Option B — add dashboard tests | Option C — full integration + CI |
|---|---|---|---|
| Test DB | Fake pool (existing pattern — patch `db` in each service module) | Same for service tests | Real PostgreSQL for integration tests (separate CI) |
| Broker in tests | Not needed for API/service tests | Mock MQTT for unit tests | Real Mosquitto in integration tests |
| Dashboard tests | Not applicable (no dashboard yet) | State tests (loading/empty/stale/error/populated) + polling | Same + E2E with real backend |
| Speed target | Keep ~1.5s suite fast enough to actually run | Keep fake-pool tests fast; integration tests can be slower | Separate fast suite + slower integration suite |

**Our actual build (w.r.t my learning):** `.md` Stage 9 — the existing project already has 53 pytest tests in `MQTT/Machine_Sensor_API/tests/`, run in ~1.5s against a fake pool with no live database:
- `test_validation.py` (20) — shared validators
- `test_error_handlers.py` (8) — all eight error-handler branches
- `test_services.py` (10) — service logic + filter builder
- `test_app_flow.py` (9) — main route flows
- `test_pickle_importer.py` (6) — hash skip, row skipping, CSV stage

The test pattern uses a fake pool (patch `db` in each service module) so tests run without a live database. The training record (`TRAINING_DOCUMENTATION.md` §3.10, §7) documents that the suite immediately caught a real bug (whitespace-only machine names passed validation) and that services bind the pool at import time, so the fixture must patch each service module's `db` name. What is not yet built: the dashboard tests, the integration tests with a real broker + PostgreSQL, the failure tests, and the E2E acceptance test. For a local-learning build, Option A is already done; Option B is the next step when the dashboard exists; Option C is later. The standing rule: keep the existing 53 tests passing throughout the work — do not break the capstone to build the dashboard.

------------------------------------------------------------------------

## Stage 10 — Build sequence (what to do first, second, third)

**What this stage does:** Order the work so each step proves the pipeline before the next step depends on it. Build Screen A with real data first; that proves database → API → browser. Add charts later.

**Plan (build sequence):**
1. Make the data real — confirm existing readings in DB; add `machine_sensors`, `machine_status`, `alarm_events`; decide retention for any new accumulating table
2. Add the dashboard API endpoints — `/api/v1/overview`, `/api/v1/machines/<id>/status`, reuse `/readings` + `/readings/statistics`; add `/api/v1/alarms` + acknowledge when ready for Screen C; add auth for write ops before or with the acknowledge endpoint
3. Build Screen A — KPI strip + machine status table + active alarms + last-updated timestamp; poll 2–5s; make stale/offline visible and distinct from healthy — this is the minimum viable dashboard
4. Build Screen B — machine detail with current values, units, thresholds; one time-series chart with selectable window (start 1h); recent alarms
5. Build Screen C — alarm list with filters; acknowledge action (auth required); resolution history
6. Build Screen D — historical analysis: selectors, time range, trend chart, min/max/avg, CSV export
7. Add refinements — system KPIs in logs/metrics; retention policy; auth for write ops; SSE/WebSockets only if polling is proven to be the bottleneck; dashboard state tests; production hardening

**How this build sequence can be implemented in different ways:**

| Decision | Option A — local learning MVP | Option B — full dashboard build | Option C — phased production rollout |
|---|---|---|---|
| First deliverable | Screen A with real data, poll 2–5s | Same, plus auth + alarm list | Same, plus failure tests + deployment config |
| MQTT timing | Simulator first; real MQTT after Screen A works | Real MQTT ingestion worker in parallel with Screen A | Real MQTT from the start, with simulator for dev |
| Auth timing | Add when dashboard goes beyond localhost | Add before alarm acknowledge endpoint | Add as part of Phase 0 decision |
| When to add SSE/WebSocket | Only if polling is proven to be the bottleneck | Measure after Screen A/B; add if needed | Decided by update-target requirement (2–5s vs sub-second) |

**Our actual build (w.r.t my learning):** `.md` Stage 10 — the existing project is at "data real" (readings already in DB) and "API exists" (the capstone endpoints). The build sequence for our actual learning path is: Screen A first (proves the pipeline), then B, then C, then D, then refinements. The simulator path (Option A for MQTT timing) is the right first move — the simulator writes through the same `reading_service.add_reading()` path, so you test the real pipeline before any real MQTT client is attached. Auth (Option C timing) should be added before or with the alarm acknowledge endpoint, not as a late hardening item — that is the explicit decision in `Live_IIoT_Monitoring_Platform_Plan.md` §14. SSE/WebSockets are explicitly not day one; measure first.

------------------------------------------------------------------------

## What exists today vs. what to build — summary table

| Layer | Exists today (our build) | To build for live monitoring (the plan) |
|---|---|---|
| Data source | Pickle import (~55,918 readings, 12 machines), MQTT broker (mTLS, port 8883), Paho client demo (`mqttdemo.py`) | Live simulator or real MQTT clients; decide source of truth for latest reading |
| Ingestion | Pickle importer (validate + normalize + batch insert + dedup via import ledger) | MQTT ingestion worker (subscribe → validate → normalize → insert via reading_service); message_id dedup; retry policy |
| Database | machines, sensor_readings, import_batches; indexes; connection pool with timeouts | machine_sensors, machine_status, alarm_events, (optional) telemetry_messages; retention policy; new indexes for dashboard queries |
| API | CRUD on machines/readings, statistics, export, health, import; shared validators + filter builder; honest status codes; 8 error handlers | /api/v1/overview, /api/v1/machines/<id>/status, /api/v1/machines/<id>/readings/latest, /api/v1/alarms, POST .../acknowledge |
| Dashboard | Nothing yet (API is backend only) | Screen A (overview), B (machine detail), C (alarms), D (historical analysis); poll 2–5s or SSE later |
| KPIs | Nothing dashboard-specific yet | Operator KPIs (total/healthy/warning/critical/offline, active alarms, latest reading age); system KPIs (messages received/accepted/persisted, latencies) |
| Alarms | Nothing alarm-specific yet | Threshold config in machine_sensors; alarm evaluation in ingestion worker; alarm_events lifecycle table; open/acknowledge/resolve transitions |
| Observability | Rotating logs (10 MB × 5), /health endpoint (200/503) | Structured logs for ingestion metrics; liveness/readiness endpoints; metrics when collector available |
| Security | MQTT mTLS (port 8883, require_certificate, use_identity_as_username), .env + fail-fast config, parameterized SQL | Dashboard/API auth for write operations; broker ACLs; CORS/payload/rate limits for exposed API |
| Testing | 53 pytest tests (fake pool, ~1.5s) | Unit tests for payload validation/thresholds/dedup; service tests for alarm lifecycle; API tests for new endpoints; integration tests with test broker + PostgreSQL; failure tests; dashboard state tests |
| Operations | waitress on port 8080; init_db.py for setup; rotating logs | Separate ingestion worker process; restart/recovery docs; backup/restore; retention policy; deployment config |

------------------------------------------------------------------------

## Sources (this plan is built from these real files)

- `MQTT/Machine_Sensor_API/readme.md` — the API layer in full detail (endpoints, config, database, services, design decisions, testing, quick start)
- `Live_IIoT_Monitoring_Platform_Plan.md` — the full platform plan (architecture, MQTT contract, data model, phased implementation, dashboard info architecture, KPIs, reliability/security/observability, testing strategy, key decisions to confirm)
- `MQTT/mqtt_readme.md` — the broker, TLS/mTLS, and Paho client notes
- `MQTT/Python/mqttdemo.py` — the Paho client demo (Callback API v2, 5 callbacks, TLS 8883, return-code checks)
- `services/pickle_importer.py` — the two-stage ingestion template (.pkl → CSV → PostgreSQL, batch inserts, SHA-256 ledger)
- `services/reading_service.py` — the reading service (add_reading, utc_z, _build_reading_filters)
- `database/schema.py` + `database/connection.py` — schema + pooled connection with timeouts
- `config.py` — fail-fast env validation, pool min/max, timeouts, batch size
- `utils/validation.py` + `utils/logger.py` — shared validators + rotating JSON logging
- `TRAINING_DOCUMENTATION.md` — the full training record (what was built, what was learned, what went wrong, what changed)
- `cron_jobs/cronjobs_readme.md` — APScheduler + PostgreSQL range partitioning (for when you need time-based partitioning of the readings table)
- `log_rotation/code_explanation.md` — rotating JSON logging walkthrough (for extending logging to cover ingestion metrics)
- `RegEx/Machine_Log_Monitor/README.md` — end-to-end flow of a scheduler-driven log monitor (read → parse → filter → store → report — same shape as ingestion)
- `RegEx/Machine_Log_Monitor/alternatives.md` — comparison of approaches (APScheduler vs while-true vs tail-f vs queue) — for when you decide how to run the ingestion worker
- `INTERN_TRAINING_CONSOLIDATED.md` — all documentation merged into one file
- `.md` — **our actual build** w.r.t my learning: the real stack, the real decisions, the real code paths, the real lessons. This file is the plan and its implementation options; `.md` is the build.

------------------------------------------------------------------------

## One-line summary

`LIVE_MONITORING_ARCHITECTURE.md` = the plan + the implementation options for each stage. `.md` = our actual build w.r.t my learning. Build Screen A with real data first; add charts, alarms, auth, and SSE/WebSockets in that order; measure before adding infrastructure.
