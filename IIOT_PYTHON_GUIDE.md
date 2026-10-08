# Python for IIoT — Concepts, Learnings to Adapt, and What to Remember

| | |
|---|---|
| **Author** | Chinta Vijayakumar |
| **Purpose** | Concept guide + habits checklist built from the *Python for IIoT — Production Cheat Sheet* |
| **Scope** | Every layer of the cheat sheet, with extra depth where the cheat sheet says so: **MQTT, SQL, and Python fundamentals** |
| **Companion doc** | [TRAINING_DOCUMENTATION.md](TRAINING_DOCUMENTATION.md) — the actual project history this guide is grounded in |

This document is not a copy of the cheat sheet. It is the version written after
living the topics in real projects: every section says **what the concept is
→ what I have learned to adapt → what I must remember/focus on**. Where a
project in this repository demonstrates the idea, it is linked.

---

## How to read this guide

1. **Concept** — plain words for what the thing is and why it exists.
2. **Learnings to adapt** — the habit or pattern to adopt in code from today.
3. **Things to remember / focus** — the durable rules, traps and mental models.

The mental model behind the whole document:

> IIoT is **not** "Python reads sensor → PostgreSQL."
> It is: *a distributed system that continuously acquires physical-world data,
> transports it reliably, validates it, processes it, persists it, exposes it
> through APIs, and makes its operational state observable.*

Every module in the cheat sheet has a **specific responsibility in that
pipeline**. Once the pipeline is clear, each module becomes easy to slot in.

---

## Table of contents

| § | Layer | § | Layer |
|---|---|---|---|
| 1 | [Communication](#1-communication) | 16 | [Security](#16-security) |
| 2 | [Data handling](#2-data-handling) | 17 | [Configuration](#17-configuration) |
| 3 | [Data validation](#3-data-validation) | 18 | [Logging](#18-logging) |
| 4 | [Database (MQTT + SQL focus)](#4-database--mqtt--sql-focus) | 19 | [Monitoring & metrics](#19-monitoring--metrics) |
| 5 | [SQL concepts to focus on](#5-sql-concepts-to-focus-on) | 20 | [Health checks](#20-health-checks) |
| 6 | [Connection pooling](#6-connection-pooling) | 21 | [File handling](#21-file-handling) |
| 7 | [API layer](#7-api-layer) | 22 | [Serialization formats](#22-serialization-formats) |
| 8 | [Concurrency](#8-concurrency) | 23 | [Python fundamentals to master](#23-python-fundamentals-to-master) |
| 9 | [The queue pattern](#9-the-queue-pattern) | 24 | [Data-processing patterns](#24-data-processing-patterns) |
| 10 | [Reliability: assume failure](#10-reliability-assume-failure) | 25 | [NumPy & pandas](#25-numpy--pandas) |
| 11 | [Exception handling](#11-exception-handling) | 26 | [Testing](#26-testing) |
| 12 | [Scheduling & cron jobs](#12-scheduling--cron-jobs) | 27 | [Module map to memorize](#27-module-map-to-memorize) |
| 13 | [Time & timestamps](#13-time--timestamps) | 28 | [The full pipeline](#28-the-full-pipeline) |
| 14 | [MQTT deep dive (focus topic)](#14-mqtt-deep-dive-focus-topic) | 29 | [Learning order (phases)](#29-learning-order-phases) |
| 15 | [MQTT in this repo](#15-mqtt-in-this-repo) | 30 | [Habit checklist](#30-habit-checklist) |

---

# 1. Communication

**Concept.** IIoT software sits between machines and data systems. It must
talk **down** to devices (Modbus, OPC-UA, vendor SDKs, raw sockets) and
**out** to brokers, APIs and services (MQTT, HTTP). Communication is thus the
first layer: without transport, there is no data to process.

| Module | Key calls | Used for |
|---|---|---|
| `paho-mqtt` | `Client()`, `connect()`, `publish()`, `subscribe()`, `loop_forever()`/`loop_start()`, `username_pw_set()`, `tls_set()`, `will_set()`, callbacks | Broker-first machine messaging |
| `requests` / `httpx` | `get()`, `post()`, `put()`, `delete()`, `raise_for_status()`, `AsyncClient()` | REST calls to services and machines |
| `socket` | `socket()`, `connect()`, `send()`, `recv()` | Low-level TCP/UDP to devices |
| `ssl` | `SSLContext()`, `wrap_socket()` | TLS around any of the above |

**Typical IIoT flow.**

```text
PLC / Gateway
     ↓
Industrial protocol
     ↓
Python edge application
     ↓
MQTT (TLS)
     ↓
MQTT broker
     ↓
Ingestion / storage / API
```

**Learnings to adapt.**

- Choose the transport by *shape of data*: continuous telemetry → MQTT;
  request/response integration → HTTP; legacy PLC → raw protocol libs.
- Always configure authentication **and** transport security together
  (`username_pw_set()` + `tls_set()` is the minimum MQTT pair).
- Wrap external calls in a small wrapper class (e.g. the `MQTTClient` class
  in [mqttdemo.py](MQTT/Python/mqttdemo.py)) so connection, publish,
  subscribe and shutdown each have one honest place to fail.

**Things to remember.**

- `loop_forever()` — processing in the foreground with auto-reconnect.
  `loop_start()` — background thread variant. One of them must always run,
  or no messages are processed at all.
- `raise_for_status()` exists because HTTP's *success* is a lie by default —
  4xx/5xx still return a response object.
- Sockets give bytes; everything above gives structures. Don't parse bytes
  manually when a protocol library exists.

---

# 2. Data handling

**Concept.** Once data arrives it is bytes or text. It must be decoded,
normalized, transformed and enriched before anything downstream can trust it.

| Module | Key calls | Used for |
|---|---|---|
| `json` | `loads()`, `dumps()`, `load()`, `dump()` | Decode/encode payloads |
| `datetime` | `now()`, `fromtimestamp()`, `strftime()`/`strptime()`, `timedelta` | Timestamps everywhere |
| `zoneinfo` | `ZoneInfo()` | Time-zone correctness |
| `statistics` | `mean()`, `median()`, `stdev()` | Quick sensor math |
| `math` | `ceil()`, `floor()`, `isfinite()` | Numeric hygiene |
| `re` | `search()`, `findall()`, `finditer()`, `fullmatch()`, `sub()` | Extract/validate text |
| `pandas` | `read_csv()`, `to_datetime()`, `groupby()`, `resample()`, `fillna()` | Historical/bulk data |

**Typical sensor payload and decode.**

```json
{"machine_id": "M123", "sensor": "temperature", "value": 78.5,
 "unit": "C", "timestamp": "2026-10-08T10:30:00Z"}
```

```python
data = json.loads(message.payload)
machine_id = data["machine_id"]
```

**Learnings to adapt.**

- Decode with an explicit encoding and a fallback
  (`payload.decode("utf-8")` → `UnicodeDecodeError` → `repr()`), exactly as
  `on_message()` does in [mqttdemo.py](MQTT/Python/mqttdemo.py).
- Parse dates with the *exact* format string both ways — the Excel project
  ([Conversion/Excel.py](Conversion/Excel.py)) taught that approximate
  parsing is where silent data bugs begin.
- Prefer tools that make the invalid cases loud (`to_datetime(errors=...)`,
  `float()` per row in the importer) over tools that silently coerce.

**Things to remember.**

- `datetime.utcnow()` is deprecated — prefer `datetime.now(timezone.utc)`.
- Reorder-proof CSV access: read by **header names** (`csv.DictReader`), not
  column position (`File_Handling/Csv_Handling.py`).

---

# 3. Data validation

**Concept.** Production IIoT must not blindly trust sensor data: wrong types,
missing values, out-of-range readings, malformed payloads. Validation is the
gate between *arrived* and *accepted*.

| Tool | Calls | Use |
|---|---|---|
| Built-ins | `isinstance()`, `len()`, `all()`, `any()`, `is None` | Cheap structural checks |
| `pydantic` | `BaseModel`, `Field()`, `model_validate()` | Declarative models + constraints |
| `re` | `fullmatch()` | ID/tag patterns |

```python
from pydantic import BaseModel

class SensorReading(BaseModel):
    machine_id: str
    sensor: str
    value: float
    unit: str
```

**Learnings to adapt.**

- Validate at the **boundary** (route/`on_message`), once, centrally — this
  grew into `utils/validation.py` in the capstone, then into a single shared
  validator module instead of per-view private copies.
- Return **actionable** errors: missing field → 400 saying *which* field,
  not a blanket 500.

**Things to remember.**

- `fullmatch()` = the whole input must match (validation);
  `findall()` = pull out the pieces (extraction). Mixing them up silently
  weakens validation — recorded from the regex review of
  [RegEx/Assigned_Tasks.py](RegEx/Assigned_Tasks.py).
- A validation layer that is repeated in three places will drift. One
  validator, imported everywhere.
- The test suite caught a real bug: whitespace-only names passed validation.
  Validate *and* strip.

---

# 4. Database — MQTT + SQL focus

**Concept.** PostgreSQL is the general-purpose store for machines, sensors,
readings and events. Python reaches it with psycopg (2 or 3) using
connections, cursors, transactions — and in production, a pool.

| Call | Use |
|---|---|
| `connect()` | Open a database connection |
| `cursor()` / `execute()` | Run SQL |
| `executemany()` / `execute_values()` | Bulk insert efficiently |
| `fetchone()` / `fetchmany()` / `fetchall()` | Read results |
| `commit()` / `rollback()` | Transaction control |
| `close()` / `with` blocks | Release resources |

**The transaction skeleton (memorize this shape).**

```python
conn = psycopg.connect(connection_string)
try:
    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO sensor_readings
               (machine_id, sensor_tag, value, ts)
               VALUES (%s, %s, %s, %s)""",
            (machine_id, sensor_tag, value, ts),
        )
    conn.commit()
except Exception:
    conn.rollback()
    logger.exception("Insert failed")
    raise
```

**Learnings — SQL focus (from the capstone, `cron_jobs` and
[SQL_Commands](SQL_Commands/SQL_readme.md)):**

- **Parameterize everything.** `%s` placeholders for every data value.
  F-strings only for *identifiers* (schema/table names), never for data.
- **DDL has different rules.** `CREATE DATABASE` cannot run inside a
  transaction: connect to `postgres`, set `autocommit = True`, and handle
  `DuplicateDatabase` explicitly — not a generic `except print`.
- **Know whether the statement worked.** `cursor.rowcount` after
  UPDATE/DELETE; `RETURNING id` after INSERT when the id matters.
- **Typed driver errors → typed app errors → honest HTTP codes.**
  Duplicate name → `ConflictError` → 409; reading for a missing machine →
  400. A driver message must never leak 500 to the client.
- **Real numbers at the JSON boundary.** `NUMERIC` arrives as `Decimal`,
  which Flask stringifies; cast aggregates `::float8` in SQL.
- **Composite primary keys.** Postgres requires the partition column inside
  the PK: `PRIMARY KEY (id, unix_ts)` on the partitioned table
  (`cron_jobs/setup.py`).
- **Partitioning pays off at deletion time.** Dropping one child partition
  replaces batched `DELETE`s over millions of rows.

**Things to remember (SQL).**

- Transactions: `commit()` on success, `rollback()` on failure, always in a
  `finally`-safe structure.
- Connect timeouts and statement timeouts (`connect_timeout=5`,
  `statement_timeout=15000`) turn a hung query into a fast, visible failure.
- Enforce only proven claims: the unprovable unique constraint multiplied a
  file ~211× into 11.8M rows; a SHA-256 `import_batches` ledger fixed it.
- `schemas` are namespaces: `CREATE SCHEMA IF NOT EXISTS` then
  `schema.table` everywhere, never rely on `search_path`.
- Report SQL categories: DDL / DQL / DML / DCL / TCL — and keep the tool
  list honest ("not used yet: joins, window functions, `EXPLAIN ANALYZE`").

---

# 5. SQL concepts to focus on

Compressed from [SQL_readme.md](SQL_Commands/SQL_readme.md) — the working
SQL vocabulary for IIoT:

| Concept | Rule to remember | Where it bites |
|---|---|---|
| Parameterized queries | Only `%s` data values; identifiers joined from validated names | Everywhere data meets SQL |
| Constraints | `UNIQUE`, `NOT NULL`, FK with `ON DELETE CASCADE` | Duplicates, orphans |
| Indexes | `(machine_id, ts)` composite, plus indexed filters (`sensor_tag`, `ts`) | Slow time queries |
| Constraint/partition interaction | Partition column must be in the PK | `cron_jobs` composite key |
| Time-based partitioning | `PARTITION BY RANGE (ts)`, partitions created just-in-time, `_default` catch-all | Retention scale |
| Aggregates | `MIN/MAX/AVG` + `::float8` casts for honest JSON | `/statistics` endpoint |
| Transactions | Do multi-statement work atomically (import ledger row with file hash) | Import consistency |
| Batch inserts | `execute_values()` with page sizes in the thousands | 56k-row imports |

**Habit:** measure with `EXPLAIN ANALYZE` before optimizing; the honest gap
list is as valuable as the tool list.

---

# 6. Connection pooling

**Concept.** Opening a TCP+auth connection per request does not survive
traffic and drops performance. A pool warms connections and hands them out.

```python
from psycopg_pool import ConnectionPool

pool = ConnectionPool(conninfo=connection_string, min_size=2, max_size=10)

with pool.connection() as conn:
    with conn.cursor() as cur:
        cur.execute(...)
```

**Learnings to adapt.**

- Pool with **context managers that always return the connection**, and
  discard ones broken beyond repair (`database/connection.py` in the
  capstone).
- Serve through a real WSGI server (waitress) so the pool matters — the dev
  server with `debug=True` is a remote-code-execution door.

**Things to remember.**

- A connection that raised may stay broken: check/repair before reuse.
- Bound everything: pool size, connect timeout, statement timeout.
- Reuse-before-reconnect logic (`conn.closed`, `conn.info.dbname`) was a
  learning *stage*, not the destination — the destination is the pool.

---

# 7. API layer

**Concept.** The API is the bridge between stored data and applications.
Flask is fine for simple services and learning; FastAPI is the modern
production choice (declarative validation, DI, async).

**Endpoint shape for a machine-data domain** (matches the capstone exactly):

```text
GET    /health
GET    /machines          POST   /machines
GET    /machines/<id>     PUT    /machines/<id>     DELETE /machines/<id>
GET    /readings          POST   /readings
GET    /readings/statistics
GET    /readings/export (streaming CSV)
GET    /readings/import (bulk ingest)
```

**Learnings to adapt.**

- Layering: **routes** (HTTP parsing, status codes, JSON) → **services**
  (all SQL) → **database** (pool). Field validation in routes, SQL in the
  manager class, and never the other way round.
- Flask `MethodView` gives one view class per resource with clean
  GET/POST/PUT/DELETE — the switch from FastAPI to Flask mid-training was
  itself a lesson: know the *interface*, not just one framework.

**Things to remember.**

- A browser can only speak GET — test POST/PUT/DELETE with Postman/curl.
- One JSON envelope (`status`/`message`/`data`) everywhere; clients should
  only learn it once.
- Batch-capable POST (object or list) costs little and doubles endpoint
  usefulness.

---

# 8. Concurrency

**Concept.** Six machines feed one application. Nothing may wait on a single
slow connection: isolate I/O, share CPU crisply.

| Module | Calls | Use |
|---|---|---|
| `threading` | `Thread()`, `start()`, `join()`, `Lock()`, `Event()` | Background operations |
| `queue` | `Queue()`, `put()`, `get()`, `task_done()`, `join()` | Thread-safe buffer |
| `asyncio` | `async`, `await`, `create_task()`, `gather()` | Concurrent I/O |
| `concurrent.futures` | `ThreadPoolExecutor`, `ProcessPoolExecutor` | Pool-based parallelism |

**Things to remember.**

- I/O-bound → threads/asyncio; CPU-bound → processes.
- Shared mutable state needs a `Lock`; the safest lock is *not having*
  shared mutable state — hence the queue pattern below.
- paho's `loop_start()` is itself a thread: keep the main thread for
  supervision.

---

# 9. The queue pattern

**Concept.** The single most important IIoT ingestion pattern: put a buffer
between *arriving messages* and *slow storage*.

```text
MQTT → Consumer → Queue → Worker(s) → PostgreSQL
                     ↑
              temporary buffer
```

Without it, a temporary DB slowdown blocks the consumer and messages drop.
With it, workers drain at their own pace.

```python
from queue import Queue
data_queue = Queue()
data_queue.put(reading)
reading = data_queue.get()
process(reading)
data_queue.task_done()
```

**Things to remember.**

- `task_done()` after each item — so `queue.join()` is trustworthy.
- Bound the queue; a full unbounded queue is memory exhaustion with extra
  steps.
- Same skeleton, other trigger: the cron-jobs scheduler is this pattern
  time-driven instead of request-driven.

---

# 10. Reliability: assume failure

**Concept.** Production IIoT *will* see: brokers down, networks flaky,
machines disconnecting, DB failures, malformed messages. The software's job
is to fail visibly and recover gracefully.

| Problem | Solution |
|---|---|
| MQTT disconnect | Auto reconnect (paho loops), `reconnect()`, LWT to detect device death |
| DB unavailable | Retry with backoff (`tenacity`) |
| Network timeout | Timeout **and** retry |
| Invalid payload | Reject + log, never crash the consumer |
| Duplicate message | Idempotency: unique keys, message IDs, hash ledger |
| Transaction failure | Rollback, then retry the unit, not the day's work |
| Consumer crash | Durable broker/snapshot (store-and-forward) |
| Out-of-order readings | Timestamp-based ordering, `TIMESTAMPTZ` |

**Learnings to adapt.**

- Check **both** the immediate return code *and* the async confirmation:
  `subscribe()`'s `(result, mid)` and `result.rc == MQTT_ERR_SUCCESS`
  report whether the *request* was accepted; `on_subscribe`/`on_publish`
  report what the *broker* did. This generalizes to every external call.
- Time-bound everything: `connect_timeout`, `statement_timeout` — fast,
  visible, logged failure beats slow silent failure.
- Graceful shutdown: `is_connected()` before `disconnect()`, cleanup in
  `finally`, signal/`atexit` handlers for services.

---

# 11. Exception handling

**Concept.** Exceptions are the *mechanism*; the discipline is: catch
specifically, log with trace, never swallow.

```python
try:
    save_reading(reading)
except ConnectionError:
    logger.exception("Database connection failed")
except ValueError:
    logger.exception("Invalid sensor value")
```

**Things to remember.**

- `except: pass` is how systems hide failures until they explode.
- `logging.exception()` inside every error path — one bad message must not
  kill a consumer.
- Exceptions belong around *plausible* failure points. The OOP demos guard
  calls that cannot fail — that was the exercise's literal requirement, but
  the real habit is guarding what actually breaks.
- `finally` for cleanup regardless of outcome.

---

# 12. Scheduling & cron jobs

**Concept.** Periodic work is everywhere in IIoT: heartbeats, partition
creation, aggregation, retention.

**From the cron-jobs project** ([cron_jobs](cron_jobs/cronjobs_readme.md)):

| Way | Where | Note |
|---|---|---|
| OS cron (`crontab -e`) | Linux | 5-field expression: min hour day-of-month month day-of-week |
| Task Scheduler | Windows | Trigger the Python exe |
| `schedule` | Python, simple scripts | `schedule.every(1).minutes.do(job)` — interval-only |
| **APScheduler** | Python, production | Cron/interval/date triggers, persistence, concurrency |

```python
scheduler = BlockingScheduler()
scheduler.add_job(run_timestamp_job, "cron", minute="*/1", id="insert_timestamp")
scheduler.add_job(run_partition_job, "cron", minute="*/10", id="create_partition")
scheduler.start()
```

**Things to remember.**

- `BlockingScheduler` for standalone scripts; `BackgroundScheduler` to keep
  the main app free.
- Just-in-time partition creation happens **before** insert; the `DEFAULT`
  partition catches what slips through.
- Jobs must be idempotent (`IF NOT EXISTS`) because schedulers re-run.
- Partitioning rule: the partition column must be inside the primary key.

---

# 13. Time & timestamps

**Concept.** Time absolutes, not wall clocks: UTC internally, convert for
humans at the edge of the system.

```python
from datetime import datetime, timezone
ts = datetime.now(timezone.utc)
unix = ts.timestamp()
back = datetime.fromtimestamp(unix, tz=timezone.utc)
```

```text
Machine → UTC timestamp → Database → API → plant/user timezone
```

**Things to remember.**

- `TIMESTAMPTZ`, never `TIMESTAMP`, for readings: a reading must mean the
  same instant worldwide.
- Unix seconds vs milliseconds is a silent killer — `int64` nanoseconds
  divided by `10**6` in the Excel project is the recurring example.
- Unix timestamps drive partition windows: `(ts // 600) * 600` gives the
  10-minute window in `cron_jobs/scheduler.py`.
- Convert every datetime **to** and **from** string with the exact format
  string both ways.

---

# 14. MQTT deep dive — focus topic

This is the layer this training sunk the most hours into, and everything
below is verified in [MQTT/mqtt_readme.md](MQTT/mqtt_readme.md) and
[MQTT/Python/mqttdemo.py](MQTT/Python/mqttdemo.py).

## 14.1 The model

**Concept.** MQTT is publisher/subscriber via a broker. Clients never talk
directly; the broker routes by **topic** and technically **QoS**. The
broker *decouples* producers and consumers in time and space.

| Piece | Meaning | IIoT shape |
|---|---|---|
| Topic | Hierarchical address, e.g. `factory/M001/temperature` | Wildcards: `+` one level, `#` many |
| QoS 0/1/2 | At-most-once / at-least-once / exactly-once | Telemetry 0–1, commands/alarms 1–2 |
| Retained message | Broker keeps last message per topic, delivers at subscribe | Last known sensor value |
| Last Will (LWT) | Message broker publishes if a client dies ungracefully | Machine offline detection |
| Keep-alive | Liveness heartbeat between client and broker | Resources held / dropped fast |
| Session | Durable vs fresh, plus queued QoS 1/2 messages | Reconnect behavior |

## 14.2 The five callbacks and their lessons

- `on_connect` → check `reason_code` for failure, then subscribe *there*.
- `on_subscribe` → broker acknowledged the subscription; publish after this,
  not before.
- `on_message` → decode defensively, never throw out of the callback.
- `on_publish` → broker accepted the message.
- `on_disconnect` → set state; only call `disconnect()` if the client says
  it is connected.

**The central lesson (took the longest to get right):**

> `subscribe()`/`publish()` **return values** report whether the *request*
> was accepted (compare to `mqtt.MQTT_ERR_SUCCESS`).
> The **callbacks** report what the *broker* later did.
> Both checks matter; they answer different questions.

## 14.3 TLS/mTLS and the certificate story

From the Mosquitto work, the full chain:

```text
CA key + cert
   ↓ signs
Server key + CSR + cert (+ SAN for IPs/DNS)
   ↓ (optionally signs)
Client key + CSR + cert   → mTLS: broker validates client too
```

- `san.cnf` matters: OpenSSL 3.x refuses to verify without SAN entries; add
  IPs/DNS there instead of regenerating everything.
- `-des3` on CA creation forces a passphrase — that's what proves the CA
  key is under your control.
- In `mosquitto.conf` use **full paths** (relative paths break when the
  service restarts from a different cwd), listener on 8883,
  `require_certificate true`, `use_identity_as_username true` for mTLS.
- Never write multiline config via shell echo — newline loss created a real
  broken-config incident; edit the real file.

## 14.4 Broker topics and bridges

- Bridges connect two brokers so messages flow between sites — the natural
  multi-factory topology.
- Windows service control: `net start/stop mosquitto`, run with an explicit
  `-c mosquitto.conf`.
- Limits exist and matter: `max_connections` (per listener),
  `global_max_connections`.

**MQTT code habits to adapt** (all present in `mqttdemo.py`):

1. One client class; connect/subscribe/publish/disconnect as named methods
   with their own error paths.
2. `logging.exception()` (paho's `enable_logger()`) in every callback.
3. Return-code validation at every request, plus state checks before
   actions.
4. Cleanup in `finally` on the main path.

---

# 15. MQTT in this repo

| File/directory | What it demonstrates |
|---|---|
| [MQTT/mqtt_readme.md](MQTT/mqtt_readme.md) | Brokers, TLS chain, limits, bridges — the concept vault |
| [MQTT/Python/mqttdemo.py](MQTT/Python/mqttdemo.py) | Paho Callback API v2 client class with TLS 8883, all five callbacks, return codes |
| [MQTT/Machine_Sensor_API/](MQTT/Machine_Sensor_API/readme.md) | What MQTT data becomes: API + PostgreSQL + import pipeline |

**Not learned yet (honest gaps):** QoS/retained real usage, bridges
implemented end-to-end, reconnect hardening, env-based config of the demo.
These stay on the roadmap instead of pretending to be solved.

---

# 16. Security

**Concept.** IIoT runs on industrial systems — security is not optional.
Protect in transit, at the door, and in the code.

| Requirement | Practice |
|---|---|
| Encryption in transit | MQTT over TLS (8883), HTTPS for APIs |
| Device authentication | Client certificates (mTLS) |
| User authN/authZ | JWT/OAuth, roles |
| Secret management | `.env` + fail-fast `os.getenv` checks, never hard-coded |
| Input validation | Pydantic/shared validators → no malformed input |
| SQL injection | Parameterized SQL only |
| Password handling | Hashing (`hashlib.sha256`), hash ledger for files |
| Audit trail | Structured JSON logs |
| Network isolation | OT/IT segmentation |

**Things to remember.**

- TLS doesn't *authorize*, it *encrypts and authenticates the transport* —
  pair it with broker ACLs/app roles.
- Secrets: `.env` in dev, a real secret manager in prod; and the fail-fast
  "validate required env vars before touching anything" pattern from
  `config.py`.
- mTLS = both directions validated. Username/password = one direction.
  Choose by threat model, not habit.

---

# 17. Configuration

Never hard-code production credentials.

```text
BAD:  DB_PASSWORD = "mypassword123"
GOOD: DB_PASSWORD = os.getenv("DB_PASSWORD")   # .env in dev
```

What should always be configurable: DB/MQTT credentials, broker address and
port, TLS paths, API port, log level, retry counts, timeouts.

**Things to remember.**

- Validate the whole config at boot (fail-fast) — half-configured boots are
  worse than no boot.
- Everything time-related (timeouts, pool sizes, retry counts) gets an env
  knob with a sane default.

---

# 18. Logging

`print()` is for debugging; production uses the `logging` module.

```python
logger.info("Machine connected")
logger.warning("Sensor value outside expected range")
logger.error("Database connection failed")
logger.exception("Failed to process reading")   # includes traceback
```

| Level | Meaning | IIoT example |
|---|---|---|
| `DEBUG` | Development detail | MQTT payload contents |
| `INFO` | Normal operation | Machine connected |
| `WARNING` | Potential problem | Sensor high |
| `ERROR` | Operation failed | DB insert failed |
| `CRITICAL` | Severe failure | App cannot start |

**Learnings to adapt** (from [log_rotation](log_rotation/code_explanation.md)
and capstone):

- Rotating files (10 MB × 5–10) so a diary archives itself and disks never
  fill; `logger.propagate = False` and a `if logger.handlers: return` guard
  against the double-print trap.
- One logging setup per application, wired in one place — scattered demos
  losing lines was a real incident (Sep 30).
- JSON-per-line for machine collectors; human text for ad-hoc reading.

---

# 19. Monitoring & metrics

Logging says *what happened*; metrics say *how the system is behaving*.

Typical counters/gauges/histograms: `messages_received`, `messages_failed`,
`mqtt_reconnects`, `db_insert_latency`, `queue_size`, `machine_last_seen`,
`api_error_count`.

| Metric kind | Meaning | Example |
|---|---|---|
| Counter | Monotonic total | MQTT messages received |
| Gauge | Current value | Queue size |
| Histogram | Distribution | DB insert duration |
| Summary | Aggregates | API latency |

**Things to remember.**

- `prometheus_client` is the default Python tool; `Counter`/`Gauge`/
  `Histogram` cover most needs.
- Metrics answer *trends and health*, logs answer *specific incidents* —
  both, not either.

---

# 20. Health checks

Expose more than "is it alive":

```text
/health    → application up?
/readiness → can serve traffic? (PostgreSQL? MQTT? dependencies OK?)
/liveness  → proactively restart if false
```

`/readings/import`, `/health` and friends in the capstone: readiness checks
should verify real dependencies (`SELECT 1`), not just return `200`.

---

# 21. File handling

`pathlib` over string-concatenated paths.

```python
from pathlib import Path
LOG_FILE = Path(__file__).resolve().parent / "logs" / "app.log"
LOG_DIR.mkdir(exist_ok=True)
```

| Calls | Use — IIoT |
|---|---|
| `exists()`, `mkdir()`, `glob()`, `iterdir()` | Certificates, log dirs, snapshots |
| `read_text()`/`write_text()`, `read_bytes()`/`write_bytes()` | Config, TLS material |
| `open()` + `csv` / `pickle` | Telemetry CSV, pickle snapshots |

**Things to remember.**

- Certificates live on disk as files — always from resolved `Path`s, never
  relative paths that break on service restart.
- Pickle is Python-specific and **not** safe from untrusted sources; treat
  snapshots as data to be validated *after* load (the importer does exactly
  that).

---

# 22. Serialization formats

| Format | Best for | IIoT use |
|---|---|---|
| JSON | MQTT, REST, config, inter-service | Payloads, configuration |
| CSV | Exports, reports, bulk import | `readings/export`, snapshots staging |
| Pickle | Python-only snapshots/cache | The `.pkl` phone snapshot — but validate everything |
| Bytes | Raw device protocols | `socket.recv()` |

**Things to remember.**

- Choose per consumer need — CS-comma-separated staging files exist because
  humans audit them better than pickles.
- Everything crossing a trust boundary (network load, file from a source)
  must be validated after deserialization, not before.

---

# 23. Python fundamentals to master

Built-ins that come up daily in IIoT code, and their domain uses:

| Built-in | IIoT use |
|---|---|
| `len()`, `isinstance()`, `type()` | Validation, inspection |
| `int()`, `float()`, `str()`, `bool()` | Coerce then validate |
| `list()`, `dict()`, `set()`, `tuple()` | Payloads, unique machines, immutable config |
| `enumerate()`, `zip()` | Indexed readings, parallel sequences |
| `sorted()`, `min()`, `max()`, `sum()`, `round()` | Reading math |
| `any()`, `all()` | Detect one bad / verify all good |
| `map()`, `filter()` | Transform/filter collections |
| `hasattr()`, `getattr()` | Defensive access |
| `open()` | Files |

Plus the deeper fundamentals to keep sharp: classes
(`__init__`, `repr`, encapsulation — see [OOP/](OOP/README.md)),
exceptions around *plausible* failures, comprehensions, modules/packages,
context managers (the `with` discipline everywhere).

---

# 24. Data-processing patterns

The five shapes the cheat sheet names, with the habits to remember:

```python
average = sum(values) / len(values)                    # NaN-safe? check isfinite()
minimum, maximum = min(values), max(values)
abnormal = [v for v in values if v > threshold]        # list comprehension
if any(v > threshold for v in values):                 # single bad → alarm
    trigger_alarm()
if all(isinstance(v, (int, float)) for v in values):   # all good → proceed
    process(values)
```

**Things to remember.**

- `any()`/`all()` with generator expressions read like sentences and skip
  the intermediate list.
- Aggregates before coercion are a bug farm — compute on validated floats
  only (`::float8` / `float()` at the boundary).
- For real analytics work, prefer `statistics.mean()`/`np.mean()` and let
  the standard library carry the nuance (NaN handling, etc.).

---

# 25. NumPy & pandas

NumPy for numerical heat (vibration analysis, percentiles, NaN checks);
pandas for historical analysis, **not** high-frequency individual message
ingestion.

```python
df.groupby("machine_id")["temperature"].mean()     # per-machine averages
df.resample("5min").mean()                          # time-window aggregation
df.rolling(window=10).mean()                        # moving average
```

**Things to remember.**

- `to_datetime()` with an exact format, `fillna()`/`dropna()` decisions
  recorded openly (the Excel project replaced NaN with 0 deliberately).
- Read from SQL with `read_sql()`, export with `to_excel()` — reports are
  pandas' sweet spot.
- NumPy `isnan()`/`isfinite()` protect sensors that report broken floats.

---

# 26. Testing

The capstone's 53-test suite is the local proof: validation, filter
building, error-code translation, importer hash-skip, route flows — all on
a fake pool, ~4 s, no live DB.

```python
def test_temperature_validation():
    assert validate_temperature(50) is True
```

| Component | Test |
|---|---|
| MQTT consumer | Message processing, malformed payload |
| Validator | Valid/invalid payloads |
| DB service | Insert/update/delete + code translation |
| API | Status codes, JSON shapes |
| Queue | Producer/consumer behavior |
| Scheduler | Job registration and execution |
| Retry logic | Recovery from known failures |

**Things to remember.**

- Test the *error* branches first — they are where systems actually fail.
- Fakes keep tests honest and fast; the earlier offline verification with a
  fake connection layer proved the same value even before pytest.
- A test suite that runs in seconds gets run; one that takes minutes does
  not.

---

# 27. Module map to memorize

| Layer | Technology | Responsibility |
|---|---|---|
| Machine communication | `pymodbus`, OPC-UA, SDKs | Talk to devices |
| Messaging | `paho-mqtt` + broker | MQTT transport |
| HTTP | `requests` / `httpx` | REST |
| Buffer | `queue` | Decouple producer/consumer |
| Validation | `pydantic` | Trust nothing incoming |
| Time | `datetime`, `zoneinfo` | Absolutes (UTC) |
| Text | `re` | Extraction/validation |
| Database | `psycopg` (+ pool) | PostgreSQL |
| Processing | `pandas`, `numpy` | Analytics |
| Scheduling | `APScheduler` | Periodic jobs |
| Retry | `tenacity` | Recoverable failure |
| Logging | `logging` | Operational visibility |
| Config | `os`, `dotenv` | Secrets/settings |
| Security | `ssl`, `secrets`, `cryptography` | Protection |
| API | `FastAPI` (+ Pydantic) | Backend |
| Server | `uvicorn` / `waitress` | Real front door |
| Testing | `pytest` | Verification |
| Metrics | `prometheus_client` | Observability |

---

# 28. The full pipeline

The end-to-end mental model — Machine → Edge gateway (protocol adapter,
validation, normalization, **local buffer**) → MQTT/TLS → Broker (auth, TLS,
QoS, routing) → Python ingestion (paho + json + pydantic + logging) → Queue
→ Worker (normalize/validate/enrich/aggregate/rules) → PostgreSQL (machines,
sensors, readings, events, alarms) → API → Dashboard — with security,
logging, monitoring, testing, retry, configuration, backup and alerting as
cross-cutting concerns, not boxes on the side.

> **The key thing to adapt:** every module has a specific responsibility in
> this pipeline. When a new problem appears, locate the pipeline stage it
> belongs to first — the right tool almost always becomes obvious.

---

# 29. Learning order — phases

Random learning is the failure mode. The project order followed here matches
the cheat sheet's recommended sequence, and the repo's folder layout grew
out of it:

```text
Phase 1: Python foundation      → functions, classes, exceptions,
                                  collections, comprehensions, files
                                  (OOP/, File_Handling/)
Phase 2: Data                   → json, datetime, re, csv, pandas
                                  (Conversion/, RegEx/)
Phase 3: Communication          → HTTP, MQTT, paho, TLS (MQTT/)
Phase 4: Database               → SQL, PostgreSQL, psycopg, transactions,
                                  pooling, indexes, partitioning
                                  (Database_Connection/, MQTT/Machine_Sensor_API/)
Phase 5: Backend                → Flask/FastAPI, Pydantic, REST, auth
Phase 6: Production engineering → logging, config, env vars, queue,
                                  threading, APScheduler, retry, graceful
                                  shutdown (log_rotation/, cron_jobs/)
Phase 7: Operations             → Docker, health checks, metrics,
                                  Prometheus, alerting, CI/CD  ← now
```

**Currently here:** Phase 7 — Docker/packaging, metrics, CI are the standing
gaps in §7 of [TRAINING_DOCUMENTATION.md](TRAINING_DOCUMENTATION.md).

---

# 30. Habit checklist

The one-line habits that covered most of this training's mistakes:

- [ ] Secrets and config in env vars, validated **fail-fast** at boot.
- [ ] One connection pool; context managers that always return resources.
- [ ] Parameterized SQL; timeouts (`connect_timeout`, `statement_timeout`).
- [ ] Transactions: `commit` on success, `rollback` on failure, cleanup in
      `finally`.
- [ ] Validate incoming data once, centrally, at the boundary — then
      trust it downstream.
- [ ] UTC + `TIMESTAMPTZ`; convert at the edge only.
- [ ] Both the return code **and** the callback/async confirmation.
- [ ] `logging.exception()` everywhere an error path exists; rotating
      file; one logging setup per application.
- [ ] Buffer with a queue anything that touches slow I/O.
- [ ] Idempotency for anything that can re-run (jobs, imports, retries) —
      proven claims only (hash ledger, `IF NOT EXISTS`, `ON CONFLICT`).
- [ ] Assume failure: retry with backoff, keep local state for
      store-and-forward, fail gracefully on shutdown.
- [ ] Test the error branches; keep the suite fast enough to actually run.
- [ ] Read the adapt-to-remember triads in this doc before writing the
      next feature — the mental model (§28) decides the tool.
