# Engineering Training Documentation — August to October 2026

| | |
|---|---|
| **Author** | Chinta Vijayakumar |
| **Company** | Triniti Advanced Software Labs Pvt Ltd |
| **Period** | 17 August 2026 – ongoing (six core weeks 17 Aug – 28 Sep, continuing since) |
| **Mentor** | V. Swaroop, Technical Consultant, High Technology Practice |
| **Last reviewed** | 6 October 2026 — every link and claim below was re-checked against the live tree |

This document records the full training period: what was built, what was
learned, what went wrong, and which engineering habits changed along the way.
Every file reference is a clickable link to the real code in this repository.

The document is written in two layers, like every other doc in this repo:
the summary and the plain-words tables first, the precise technical detail
underneath.

---

## 1. Executive summary

The training moved from language fundamentals to a production-shaped
IIoT-style data pipeline, and is still growing after the core six weeks:

```text
Weeks 1–4   Foundations: OOP, files/CSV, PostgreSQL, first Flask API,
            pandas/Excel, Mosquitto + TLS/mTLS, Paho client mastery
Weeks 5–6   Capstone: Machine Sensor API built, hardened, then rebuilt to
            production standard, reviewed against 8 design principles,
            cleaned up with a versioned-change method (§3.8–§3.10)
Since then  Supporting tracks: rotating JSON logging, SQL command notes,
            table partitioning driven by a scheduler-based cron-jobs project,
            regex practice — plus documentation consolidation (§3.11–§3.13)
```

The capstone is [Machine_Sensor_API](MQTT/Machine_Sensor_API/readme.md): a
layered REST API managing machines and sensor readings, which bulk-imports a
**pickle snapshot of ~55,918 readings across 12 machines** into PostgreSQL
with batch inserts and a duplicate-safe import ledger.

The single biggest shift of the period: from *writing code that runs* to
*designing code that survives requests, failures, and concurrent users* —
pooled database connections returned through context managers, transactions
with rollback, parameterized queries, secrets in `.env`, time-bounded failure
(timeouts), and return-code validation on every external call.

The capstone's own story had three acts:

1. **Built (Sep 15–17):** a working layered API with bulk import (§3.8).
2. **Hardened (Sep 18–21):** honest error semantics — 409/400 instead of
   blanket 500s, real JSON numbers from statistics, row-level import
   validation (§3.9).
3. **Rebuilt, reviewed, cleaned (Sep 22–28):** a real WSGI server, connection
   pooling with timeouts, an import ledger replacing a guessed uniqueness
   rule; then an 8-principles design review (with an independent cross-check
   that caught one wrong claim); then a five-fix cleanup applied by building
   parallel versions first and promoting them only after both chains proved
   identical (§3.10).

After the capstone, the same lessons were deliberately re-applied on smaller
ground: a standalone rotating-log demo (§3.11), a scheduler-driven cron-jobs
project with PostgreSQL range partitioning (§3.12), and regex practice
(§3.13) — each one small enough to finish, documented like production code.

---

## 2. Timeline of assigned work

| Date | Task | Output |
|---|---|---|
| Aug 17 | OOP: 5 inheritance types + encapsulation, exception in every example | [OOP/](OOP/README.md) — 6 files |
| Aug 17 | PostgreSQL: create database, schema, table | [setup.py](Database_Connection/setup.py) |
| Aug 18 | File handling: read/write/append + errors | [Handle.py](File_Handling/Handle.py), [Csv_Handling.py](File_Handling/Csv_Handling.py) |
| Aug 20 | `Postgremanager` class with CRUD + transactions | [setup.py](Database_Connection/setup.py) |
| Aug 20–21 | Excel generation → pandas DataFrame → split strings | [Excel.py](Conversion/Excel.py) |
| Aug 24–26 | Flask API over the employee table | [main.py](Database_Connection/main.py) |
| Aug 26–31 | Mosquitto broker: service control, limits, bridge concepts | [mqtt_readme.md](MQTT/mqtt_readme.md) |
| Sep 3–7 | TLS/SSL certificate chain, SAN, 8883 listener | [mqtt_readme.md](MQTT/mqtt_readme.md) |
| Sep 8–10 | Paho client: 5 callbacks, paho logging, return-code checks | [mqttdemo.py](MQTT/Python/mqttdemo.py) |
| Sep 15–17 | Machine Sensor API + bulk pickle import | [Machine_Sensor_API/](MQTT/Machine_Sensor_API/readme.md) |
| Sep 18–21 | Capstone hardening: 409/400 exception mapping, JSON-number statistics, row-level import validation, conditions-list refactor | §3.9 |
| Sep 22–24 | Production rebuild: waitress, connection pooling, import ledger, `init_db.py`, TIMESTAMPTZ | §3.10 Pass 1 |
| Sep 25–26 | 8-principles design review + independent cross-check | §3.10 Pass 2 |
| Sep 27–28 | Five-fix cleanup built as parallel versions, verified, promoted; docs rewritten in simple + engineer two-layer format | §3.10 Pass 3 |
| Sep 29 | SQL command notes; log-rotation learning progression; `Database_Connection` moved from hard-coded credentials to `.env` | [SQL_readme.md](SQL_Commands/SQL_readme.md), [rotation.py](log_rotation/rotation.py) |
| Sep 30 | Log-rotation demos consolidated into one hybrid JSON + rotating-file handler after lost-log debugging; first range-partitioning demo (`partition_ts`) | [rotation.py](log_rotation/rotation.py), [code_explanation.md](log_rotation/code_explanation.md) |
| Oct 1 | Documentation consolidation (one readme per topic); cron-jobs project rebuilt on a real scheduler; table partitioning with just-in-time partitions and a composite primary key | [cronjobs_readme.md](cron_jobs/cronjobs_readme.md), §3.12 |
| Oct 4–6 | Regular expressions: eight matcher functions + full notes; `Final_zip/` distribution copy assembled | [RegEx/](RegEx/regex_readme.md), §3.13 |

---

## 3. Technical sections

Each section follows the same shape: **Built → Learned → Takeaway.**

### 3.1 Object-oriented programming — [OOP/](OOP/README.md)

**Built:** one runnable file per topic — [Single](OOP/Single_inheritance.py),
[Multiple](OOP/Multiple_inheritance.py), [MultiLevel](OOP/MultiLevel_inheritance.py),
[Hierarchical](OOP/Hierarchical_inheritance.py), [Hybrid](OOP/Hybrid_inheritance.py)
inheritance, and [Encapsulation.py](OOP/Encapsulation.py). Every file guards its
demo calls with `try/except AttributeError`, as required.

**Learned:**

- MRO intuition: with `Son(Mother, Father)`, Python searches parents left to
  right; hybrid trees are just these patterns composed.
- Encapsulation levels: public `name`, protected-by-convention `_Code`,
  private via name-mangling `__battery_health` (reachable only as
  `_Smartphone__battery_health`). Python's "private" is a convention, not a wall.

**Takeaway:** exceptions belong around *plausible* failure points. The OOP
exercise used them as guards for invalid attribute access — exactly where
`AttributeError` actually comes from.

### 3.2 File and CSV handling — [File_Handling/](File_Handling/README.md)

**Built:** [Handle.py](File_Handling/Handle.py) exercising `w` / `x` / `a` /
`r+` with per-mode error handling (`FileExistsError`, `FileNotFoundError`);
[Csv_Handling.py](File_Handling/Csv_Handling.py) wrapping four CSV operations in
a `CSVManager` class built on `csv.DictReader` / `csv.DictWriter`.

**Learned:**

- `x` mode exists specifically to *fail loudly* when a file already exists —
  "create-if-fresh" semantics.
- Dict-based CSV access beats index-based: reordering columns can't silently
  corrupt row handling.
- `append_csv()` re-reads the existing header before writing, so appends never
  drift out of column order.

**Takeaway:** a file-system failure (missing file, permission) and a data
failure (bad row) are different animals and deserve different handling — which
is why `CSVManager` catches `FileNotFoundError` separately from generic
exceptions.

### 3.3 PostgreSQL fundamentals and the manager class — [Database_Connection/](Database_Connection/README.md)

**Built:** [setup.py](Database_Connection/setup.py) — a `Postgremanager` class
covering the full bootstrap (`CREATE DATABASE` → `CREATE SCHEMA` →
`CREATE TABLE`) plus employee CRUD with commit/rollback.

**Learned:**

- `CREATE DATABASE` cannot run inside a transaction — connect to the built-in
  `postgres` database first and set `autocommit = True`.
- Parameterized queries (`%s` placeholders) for every value; f-strings only for
  identifiers like table names, never data.
- Transactions: `commit()` on success, `rollback()` on failure, and
  `cursor.rowcount` to know whether an UPDATE/DELETE actually matched a row.
- Connection **reuse** (check `conn.closed` and `conn.info.dbname` before
  reconnecting) — and its limits (§3.7, §3.10).

**Mistakes corrected:** early versions swallowed "database already exists"
into a generic except with a print; the later projects
([cron_jobs/setup.py](cron_jobs/setup.py), capstone) handle
`psycopg2.errors.DuplicateDatabase` explicitly. The password was hard-coded
here at first — accepted as a stage of learning, replaced by `.env` in the
capstone, and finally back-ported to this project on Sep 29: `setup.py` now
loads `.env` with `python-dotenv` and validates the required variables with a
fail-fast check before touching the database.

### 3.4 First REST API — [main.py](Database_Connection/main.py)

**Built:** a Flask `MethodView` exposing the employee table:

```text
GET /employees   GET /employees/<email>   POST /employees
PUT /employees/<email>   DELETE /employees/<email>
```

Field validation runs before any database call, responses use a consistent
JSON envelope (`status` / `message` / `data`), and
[Screenshots/](Database_Connection/README.md) records each operation: single
insert, batch insert, duplicate-email rejection, update, delete.

**Learned:**

- POST accepts a single object **or** a list — one endpoint, batch-capable.
- Validation lives in the route; SQL lives in the manager class. That
  separation grew into the full routes/services/database layering.
- A browser can only speak GET — POST/PUT/DELETE need Postman, `curl`, or JS
  `fetch`. This is why API testing tools exist.

### 3.5 Data conversion with pandas — [Conversion/](Conversion/README.md)

**Built:** [Excel.py](Conversion/Excel.py), a pipeline from
[work.csv](Conversion/work.csv) (ETHUSD hourly OHLCV) to
[Work_sample_processed.xlsx](Conversion/Work_sample_processed.xlsx):
parse dates with an exact format string → split `Symbol` into characters
(`abc → ['a','b','c']`) → Unix timestamp (ms) → Day/Month/Year/Hours/Minutes/
Seconds → `fillna(0)` → format the date back to the source style → Excel export
with auto-sized columns via openpyxl → dictionary records.

**Learned:**

- Date round-trips need the *exact* format string both ways
  (`%Y-%m-%d %I-%p`); approximate parsing is where silent data bugs begin.
- `df.astype("int64") // 10**6` converts datetime64 nanoseconds → Unix
  milliseconds.
- Column-dimension sizing via `ws.column_dimensions[col.column_letter]` makes
  generated spreadsheets actually readable.

**Incident record:** the first shared zip had a `Minues`/`Minute` column typo —
caught in review, fixed (now `Minutes` from `dt.minute`). Lesson: proofread
generated column names against the requirement, not just the code's syntax.

### 3.6 MQTT and the Mosquitto broker — [MQTT/mqtt_readme.md](MQTT/mqtt_readme.md)

(Originally kept as separate `Learning.md` files; consolidated into the one
folder readme on Oct 1.)

**Learned and practiced:**

- Pub/sub model: clients (publishers/subscribers) never talk directly — the
  broker decouples them by topic.
- Service control on Windows (`net start/stop mosquitto`, running with
  `-c mosquitto.conf`), and why editing the real config file beats echoing
  multiline config from a shell (newline loss — a real bug hit, documented).
- Broker limits: `max_connections` (per listener), `global_max_connections`,
  `global_max_clients`.
- **TLS/mTLS end to end** with openssl: CA key + cert → server key + CSR +
  cert → client key + CSR + cert; what each file proves; CSR `-subj` for
  scripting; `san.cnf` (OpenSSL 3.x refuses to verify without SAN — adding
  IPs/DNS there beats regenerating everything when the network changes); the
  broker listener on 8883 with `require_certificate true` and
  `use_identity_as_username true`; client verification with
  `mosquitto_sub/pub --cafile --cert --key`.
- Bridge concepts: connecting two brokers so messages flow between them — the
  use case for multi-site IIoT setups.

### 3.7 Python MQTT client — [mqttdemo.py](MQTT/Python/mqttdemo.py)

**Built:** an `MQTTClient` class using Paho **Callback API v2**, TLS on 8883,
username/password auth, all five callbacks, paho's own logger, INFO-level app
logging, and `logging.exception()` in every error path.

**Learned — the part that took longest to get right:**

- The **immediate return value** of `subscribe()` (`result, mid`) and
  `publish()` (`result.rc` vs `mqtt.MQTT_ERR_SUCCESS`) reports whether the
  *request* was accepted. The **callbacks** (`on_subscribe`, `on_publish`)
  report what the *broker* later did. Both checks matter; they answer
  different questions.
- `loop_forever()` runs the network loop in the foreground with automatic
  reconnect; `loop_start()` is the background-thread variant.
- Safe shutdown: check `is_connected()` before `disconnect()`, and clean up in
  a `finally` block.
- Failure taxonomy actually observed: `ConnectionRefusedError`,
  `ssl.SSLCertVerificationError` (expired/mismatched certs), and MQTT reason
  codes (bad credentials, not authorized, quota exceeded) — all catalogued in
  the [mqtt_readme](MQTT/mqtt_readme.md).

**Takeaway:** `logging.exception()` inside each callback keeps one bad message
from killing the client — resilient handlers are the difference between a demo
and a service.

### 3.8 Capstone: Machine Sensor API — [Machine_Sensor_API/](MQTT/Machine_Sensor_API/readme.md)

**The assignment:** a Flask + PostgreSQL API to manage machine data — add/
retrieve machine details, store sensor readings, import historical data.

> *The diagram and decision table below record the capstone **as first built**
> (Sep 15–17). Rows marked **→ later** were replaced by the Sep 22–28
> production rebuild; see §3.10 for what changed and why.*

**Architecture (layered):**

```text
HTTP request
   ↓
app.py            — factory, error handlers, /health, /readings/import
   ↓
utils/validation.py — shared input validators (added Sep 28)
   ↓
routes/           — MethodViews: HTTP parsing, status codes, JSON
   ↓
services/         — all SQL, one class per domain, commit/rollback each
   ↓
database/connection.py — DatabaseManager: pooled connections + timeouts
   ↓
PostgreSQL (schema: machines 1—N sensor_readings, FK ON DELETE CASCADE,
            import_batches ledger, 3 query indexes)
```

**Key engineering decisions, as first built:**

| Decision (first build) | Why | Later |
|---|---|---|
| Fresh connection per request, closed in `finally` | Flask's threaded dev server made one shared connection risky | **→ later:** `ThreadedConnectionPool` + `with db.cursor()` context managers (§3.10) |
| Secrets in `.env` via `python-dotenv` | Fixing the hard-coded-password habit from §3.3 | kept, extended with fail-fast validation |
| `DatabaseError` custom exception | Routes catch one type; psycopg2 details stay in the database layer | kept |
| `ConflictError` / FK-error subclasses *(the FK one was later renamed `RelatedResourceNotFoundError`)* | Duplicate machine name → **409**, reading for a missing machine → **400** — client errors must not look like server failures | kept |
| Batch inserts of 5000 via `execute_values` | Import runs in bulk instead of row-by-row | kept; duplicate safety moved from `ON CONFLICT DO NOTHING` to the ledger (below) |
| Unique constraint `(machine_id, sensor_tag, timestamp)` | The database as last line of defense against duplicates | **→ later:** dropped — an unprovable business claim; replaced by the `import_batches` hash ledger (§3.10) |
| `BIGSERIAL` + indexes on `(machine_id, timestamp)`, `sensor_tag`, `timestamp` | The readings table grows into tens of millions of rows | kept |
| Return-code + rollback per file | A corrupt pickle file skips/rolls back without killing the whole import | kept, strengthened with row-level validation (§3.9) |

**Bulk import reality:** the snapshot data from 28-03-2025 lives in
[MQTT/Machine_Sensor_API/data/](MQTT/Machine_Sensor_API/data/) — the pickle
snapshot (`all_topics_20250328-114500.pkl`) converts to **55,918 readings
across 12 machines** (verified by counting the generated CSV). The two-stage
pipeline in [pickle_importer.py](MQTT/Machine_Sensor_API/services/pickle_importer.py)
goes `.pkl → CSV → PostgreSQL`, leaving a human-readable CSV artifact and
skipping broken rows. Records carry `ST` (sensor tag), `TS` (Unix time),
`VR[0]` (value); the importer also treats an empty/blank snapshot as 0 records
and continues instead of failing. Endpoints: full CRUD on machines and
readings, filters (`machine_id`, `sensor_tag`, `from`/`to` ISO 8601),
`/readings/statistics` (MIN/MAX/AVG), `/readings/export` (streaming CSV),
`/health`, and `POST /readings/import` — verified endpoint-by-endpoint with
Postman during development; the data folder also carries a tiny
[messy.csv](MQTT/Machine_Sensor_API/data/csv_files_28_03_2025/messy.csv) in
the same four-column schema — a two-row sample that documents the format of
the intermediate CSV stage without loading the full snapshot.

### 3.9 Post-capstone hardening (Sep 18–21)

**The theme:** the API handled the happy path with honest 500s; this pass made
the error *semantics* honest and the responses client-friendly.

- **Typed exception translation** — `ConflictError` and the FK-error subclass
  (both under `DatabaseError`) in
  [connection.py](MQTT/Machine_Sensor_API/database/connection.py); services
  translate driver integrity errors at the source. Duplicate machine name →
  **409**; reading for a nonexistent machine → **400** with an actionable
  message; everything else still 500.
- **Statistics as JSON numbers** — `NUMERIC` aggregates arrived in Python as
  `Decimal`, which Flask serializes as *strings* (`"minimum": "42.0"`).
  Aggregates are now cast `::float8` in SQL, so `/readings/statistics`
  returns real numbers, and `null` when nothing matches.
- **Row-level importer validation** — bad tags/timestamps were already
  skipped, but a single non-numeric `VR` value could abort an entire
  ~56k-row file transaction. `sensor_value` is now validated per row and
  counted in `records_skipped`.
- **Readability refactor** — dynamic filters in
  [reading_service.py](MQTT/Machine_Sensor_API/services/reading_service.py)
  no longer grow out of a `WHERE 1 = 1` string; they are a conditions list
  joined with `" AND "`. Same SQL, easier to read (the Sep 21 change shared
  with Swaroop). *This idea later grew into the single shared
  `_build_reading_filters()` helper (§3.10).*
- **Resolved later that month:** the two Postman assertions that still
  expected 500 for the duplicate-machine and bad-`machine_id` cases were
  updated to 409/400 in the revised collection.

Verified offline with a faked connection layer: 23 route/service checks
(status codes, rollback, importer skip counting) plus 6 SQL-assembly checks
(every filter combination), no live database touched.

### 3.10 Production rebuild, design review, and the versioned-cleanup method (Sep 22–28)

This final stretch turned the capstone from a working API into one that is
reviewed, armored, and documented like production software — in three passes.

#### Pass 1 — the production rebuild (Sep 22–24)

Each fix answered a concrete problem, never "production code should look like X":

| What changed | The problem it solved | In plain words |
|---|---|---|
| Flask dev server with `debug=True` → **waitress** + `wsgi.py` | The dev server's interactive debugger is a remote-code-execution door | A real service gets a real front door |
| Fresh connection per request → **`ThreadedConnectionPool`** with `with db.cursor()` context managers | TCP + auth per request doesn't survive traffic; manual cleanup gets forgotten | Reusable shopping carts instead of buying a new one per customer |
| Unique constraint on `(machine_id, sensor_tag, timestamp)` → **dropped**; duplicates guarded by the **`import_batches` ledger** (SHA-256 file hash, recorded in the same transaction) | The constraint was a business claim nobody could prove — and it once multiplied one file ~211× into 11.8M rows | Fingerprint-stamp the source file; the same content can never be filed twice |
| Server ran DDL at boot → **`init_db.py`** | A restart must never run DDL | Renovation plans are run deliberately, not on every boot |
| `TIMESTAMP` → **`TIMESTAMPTZ`** UTC; fail-fast `config.py` validating `.env` | A reading must mean the same instant worldwide; half-configured boots | Every setting checked at the door before the app wakes up |

#### Pass 2 — the 8-principles review (Sep 25–26)

The whole codebase was reviewed against eight classic principles — cohesion &
single responsibility, encapsulation & abstraction, loose coupling &
modularity, reusability & extensibility, portability, defensibility,
maintainability & testability, and simplicity (KISS · DRY · YAGNI). Full
detail in the project readme's *Design principles review*. The honest headline
scores: **Defensibility 4.5/5** (strongest — fail-fast config, parameterized
SQL everywhere, the import ledger, no information leaks), **Maintainability &
Testability 2.5/5** (weakest at the time — zero automated tests), **overall
≈ 3.4/5**.

Two things made the review more valuable than a scorecard:

- **A second, independent review** (ChatGPT, from an archived snapshot)
  converged on nearly every finding, contributed two adopted ones (the
  CSV-stage KISS question, the admin-rights DB-init portability note), and got
  one claim wrong — it flagged `DROP_LEGACY_*` SQL as live, but a full-text
  search proved the live code has no `DROP` at all. Lesson: **review the live
  tree, not the archive.**
- **A rule was adopted and is now standing policy:** the eight principles are
  *constraints on decisions, not excuses to add layers*. A change justified by
  no concrete problem is rejected — no repositories, no DI frameworks, no ORM
  rewrites "just because production".

#### Pass 3 — the five-fix cleanup, built as versions, then promoted (Sep 27–28)

The top five fixes from the review, applied with a method worth recording:

1. **DB timeouts** — `connect_timeout=5`, `statement_timeout=15000`
   (env-tunable). A hung query or dead database now fails visibly in seconds
   instead of freezing the API forever.
2. **Rotating logs** — `RotatingFileHandler` (10 MB × 5) + `LOG_LEVEL` from
   env. The diary archives itself; the disk can't fill.
3. **Dead code removed** — `count_machines()`, defined and never called
   (YAGNI).
4. **One filter builder** — the WHERE-clause construction that existed in
   three copies (list, export, statistics) is now `_build_reading_filters()`,
   called by all three.
5. **Shared validators** — input checks moved out of one view class's private
   methods into `utils/validation.py`; all views import them; the
   once-triplicated `from ≤ to` check became one `validate_from_to_order()`.

**The method (the transferable lesson):** every fix was first built as a
parallel `*_v3.py` copy while the originals stayed untouched — two complete
runnable chains, verified separately (each built 10 routes; one shared pool
per chain; exception classes aligned; a live `SELECT 1` +
`SHOW statement_timeout` confirmed the server received `15s`). Only after both
chains proved identical in behavior were the v3 files promoted over the
originals and the `_v3` names stripped. Rollback was trivial by construction,
and the promotion itself was re-verified (app builds, pool identity, live DB).

*(The archived comparison that framed this pass, `PRODUCTION_COMPARISON.md`,
and the old root README/LEARNINGS files were consolidated away on Oct 1; the
findings live on in the capstone readme and this document.)*

### 3.11 Standalone rotating-JSON logging — [log_rotation/](log_rotation/code_explanation.md)

**Built:** [rotation.py](log_rotation/rotation.py) — one hybrid handler demo:
every log record is formatted as **one-line JSON** (unix-epoch timestamp,
level, logger name, message, exception block when present) and written both to
a **rotating file chain** (`app.log` → `app.log.1` → … → `app.log.10`) and to
the console. The file is explained line-by-line in
[code_explanation.md](log_rotation/code_explanation.md).

**Learned:**

- `RotatingFileHandler.maxBytes` + `backupCount` = a diary that archives
  itself; the disk can never fill. The demo uses 2 KB so rotation is visible
  in seconds; production code (the capstone's logger, cron_jobs' logging) uses
  10 MB × 5–10 archives.
- `logger.propagate = False` stops records from reaching the root logger —
  without it, console handlers print every line twice.
- `if logger.handlers: return` guards against duplicate handler attachment on
  re-imports.
- JSON-per-line is the format log collectors want to see; free-text logs are
  for humans only.

**Incident record (Sep 30):** earlier log-rotation attempts were split across
multiple demos and log lines went missing between them; the fix was
consolidating into this one hybrid handler and re-documenting the *actual*
function-based code. Lesson: one logging setup per application, wired in one
place — and document the code that really runs, not an earlier draft.

**Takeaway:** this little file is where the capstone's Pass-3 "rotating logs"
fix came from — learning a mechanism in isolation before applying it where it
matters.

### 3.12 Cron jobs, schedulers, and table partitioning — [cron_jobs/](cron_jobs/cronjobs_readme.md)

**Built (restructured Oct 1):** a scheduler-based project that inserts the
current Unix timestamp every minute into a **range-partitioned** PostgreSQL
table and creates partitions just-in-time.

- [setup.py](cron_jobs/setup.py) — bootstrap: `CREATE DATABASE`
  (`autocommit`, `DuplicateDatabase` handled) → `CREATE SCHEMA` → the
  partitioned table `timestamp_data` with **composite primary key
  `(id, unix_ts)`** and a `_default` partition as the safety net.
- [scheduler.py](cron_jobs/scheduler.py) — the two jobs:
  `insert_current_timestamp()` (every 1 minute) and `create_partition()`
  (every 10 minutes, creating the current **and** next 10-minute window so a
  partition always exists before its first insert; `IF NOT EXISTS` makes
  re-runs idempotent).
- [db.py](cron_jobs/db.py) + [config.py](cron_jobs/config.py) —
  `get_connection(database=None)` on `.env` credentials, with an escape hatch
  to the `postgres` maintenance database for `CREATE DATABASE`.
- [logging_config.py](cron_jobs/logging_config.py) — root logger, 10 MB × 10
  rotating file + console, apscheduler quieted to WARNING (the lesson from
  §3.11 applied directly).

**Learned:**

- OS cron vs in-process schedulers: `crontab -e` runs scripts on Linux;
  on Windows, Task Scheduler; in Python, the `schedule` module or APScheduler.
  This project uses **APScheduler's `BlockingScheduler`** with two
  `cron`-trigger jobs (`minute="*/1"`, `minute="*/10"`) — see the
  APScheduler-vs-schedule comparison table in the
  [readme](cron_jobs/cronjobs_readme.md).
- **Partition key rule:** PostgreSQL requires the partition column to be part
  of the primary key — hence the composite `PRIMARY KEY (id, unix_ts)` after
  the first plain-`id` design was rejected by the database (Oct 1 commit).
- **Just-in-time partitioning** (Oct 1 fix): inserts originally failed when
  the matching partition didn't exist yet; the insert job now creates the
  partition *before* inserting, and the `DEFAULT` partition catches anything
  that still slips through.
- Partitioning pays off at deletion time: dropping old data becomes
  `DROP TABLE` on one child partition instead of batched `DELETE`s
  ([SQL_readme.md](SQL_Commands/SQL_readme.md), *Table partitioning*).

**Takeaway:** the pipeline shape — bootstrap script → long-running scheduler →
structured logs → idempotent SQL — is the same skeleton as the capstone's
importer, just time-driven instead of request-driven. Patterns transfer; only
the trigger changes.

### 3.13 Regular expressions — [RegEx/](RegEx/regex_readme.md)

**Built:** [`.py`](RegEx/.py) — eight matcher functions driven by an
interactive `main()`: exact five-digit match with lookarounds
(`(?<!\d)\d{5}(?!\d)`), lowercase-only and uppercase-only scans, grouped
letters + numbers extraction, "starts with A" / "ends with Z" via word
boundaries, digits-only and no-digits scans. Notes in
[regex_readme.md](RegEx/regex_readme.md) cover the meta-characters, anchors,
special sequences, and the `re.search/match/fullmatch/findall/sub/split`
family.

**Learned:**

- `^abc` (anchor) is not `[^abc]` (negation) — one character, opposite
  meaning.
- Lookarounds (`(?<!\d)…(?!\d)`) match a position, not a character — the clean
  way to say "exactly five digits, not part of a longer number".
- Named real uses: input validation, log parsing with groups, `re.sub()` data
  cleaning — the same skills the capstone uses for validating query params.

**Takeaway:** regex is a validation tool, not a puzzle toy — the
extract-and-validate patterns here are exactly what an API's input layer does
daily.

---

## 4. Supporting skills

- **Linux basics** — [Learning_linux.md](Linux/Learning_linux.md): navigation,
  file ops, `grep`/`find`/`wc`, `sort`/`uniq`; why Linux matters for
  servers/gateways in IIoT; the WSL `explorer.exe .` trick.
- **Testing discipline** — Postman collections with chained variables
  (create → read → update → cascade-delete verification), API screenshots per
  operation, and writing the readme *while* testing so docs never drift.
  Plus offline verification with a faked connection layer when a live
  database isn't available (§3.9), and since Sep 28 a real pytest suite (§7).
- **SQL as a working vocabulary** —
  [SQL_readme.md](SQL_Commands/SQL_readme.md): DDL/DQL/DML/DCL/TCL categories,
  the constraint and index toolbox used in the capstone, and an honest
  "not used yet" list (joins, window functions, `EXPLAIN ANALYZE`).
- **Documentation habit** — every folder carries a README with real
  click-through links; notes record *why*, not just *what*; every doc opens
  with a simple version a non-technical reader can follow (the capstone's
  waiter-never-cooks layering analogy, the shopping-cart pool, the diary that
  archives itself) and keeps the engineer detail below —
  see [code_explanation.md](log_rotation/code_explanation.md) for the pattern
  applied to code itself. On Oct 1 the scattered per-topic note files were
  consolidated into one readme per folder, so there is exactly one place each
  topic lives.

---

## 5. Error log (encountered → resolved)

| Error | Root cause | Fix / lesson |
|---|---|---|
| `FileExistsError` while practicing | `"x"` mode on existing file | Intended behavior — guard with try/except |
| `CREATE DATABASE` failing inside transaction block | Postgres disallows it | Connect to `postgres` db + `autocommit = True` |
| Duplicate-email insert rejected | `UNIQUE` constraint | Expected; surfaced as a clean 400 with validation first |
| Broken multiline `mosquitto.conf` written via `echo` | Newline loss in shell redirect | Edit the real config file manually |
| `ssl.SSLCertVerificationError` | Cert without SAN / wrong CN / expired | Add IP/DNS to `san.cnf`, regenerate server cert |
| Callbacks "not firing" | Expecting callbacks to replace return-code checks | Check `subscribe()`/`publish()` results **and** register callbacks |
| `Minues` column typo in Excel output | Manual typo in generated columns | Fixed to `Minutes`; proofread output schema |
| Blank snapshot record sets | First snapshot(s) carried empty dicts | Importer treats empty data as 0 records, continues |
| Duplicate readings on re-import | Overlapping snapshots | First fixed with `ON CONFLICT DO NOTHING` + unique constraint; **final fix (Sep 28):** the `import_batches` hash ledger — content, not constraints |
| Statistics returned as JSON strings | `NUMERIC` → psycopg2 `Decimal` → Flask stringifies | Cast aggregates `::float8` — real numbers at the JSON boundary |
| Duplicate machine / missing FK machine returned 500 | `IntegrityError` never translated | `ConflictError` → 409, FK error (now `RelatedResourceNotFoundError`) → 400 |
| One bad `VR` value aborted a whole pickle file | Value not validated per row | Row-level `float()` check → skip + count in `records_skipped` |
| Fragile `WHERE 1 = 1` concatenation | Appended conditions depended on trailing whitespace | Conditions list + `" AND ".join(...)` — later grew into one shared `_build_reading_filters()` |
| Hung query could hold a pooled worker forever | No connect/statement timeouts | `connect_timeout=5` + `statement_timeout=15000` (env-tunable); verified live via `SHOW statement_timeout` |
| Log file grew without bound | Plain `FileHandler` on a long-running service | `RotatingFileHandler` 10 MB × 5 + `LOG_LEVEL` from env |
| A reviewer's "live code" finding didn't match the tree | Finding came from an archived zip snapshot | Full-text search proved the live code clean; lesson: **review the live tree, not the archive** |
| Log lines went missing between rotation demos | Two parallel logging demos, each with its own handlers | Consolidated into one hybrid JSON + rotating handler (Sep 30); one logging setup per app |
| Inserts failed with "no partition … found" | Row arrived before its 10-minute partition existed | Just-in-time partition creation before each insert + a `DEFAULT` catch-all partition (Oct 1) |
| `CREATE TABLE … PARTITION BY` rejected the plain-`id` primary key | Postgres requires the partition column inside the PK | Composite `PRIMARY KEY (id, unix_ts)` (Oct 1) |
| Two concurrent imports could collide resolving the same machine name | Machine lookup + insert were not atomic — risk caught in review, not a crash observed | Race-safe `INSERT … ON CONFLICT (machine_name) DO UPDATE … RETURNING id` in the importer |

---

## 6. How the period changed my engineering habits

1. **Secrets** — from hard-coded passwords to `.env` + fail-fast `config.py`
   (capstone, cron_jobs, and since Sep 29 back-ported to the early
   `Database_Connection` project too).
2. **Connections** — from one long-lived reused connection, through
   per-request connections with `finally` cleanup, to a pooled manager with
   context managers that always return the connection (and discard broken
   ones).
3. **SQL** — from string concatenation to parameterized queries everywhere;
   identifiers kept out of value positions; filters built in one shared place.
4. **Failure handling** — from printing exceptions to typed exceptions
   (`DatabaseError` and family), rollback, `rowcount` checks, and
   `logging.exception()`.
5. **Time-bounded failure** — a stuck database or runaway query now hits
   `connect_timeout`/`statement_timeout`: fast, visible, logged failure beats
   slow, silent failure.
6. **External calls** — always validate the immediate return code *and*
   handle the async confirmation (Paho lesson; generalizes to any messaging
   system).
7. **Data integrity** — enforce only claims that can be proven; protect the
   rest at ingestion (the hash ledger), so a wrong assumption can't multiply
   into 11.8M rows again.
8. **Structure** — routes/services/database layering, earned after flat
   scripts became hard to navigate.
9. **Readability** — replaced `WHERE 1 = 1` string surgery with a conditions
   list, then a single shared builder; code is read far more often than it is
   written.
10. **Versioned change discipline** — build the fix as a parallel copy, verify
    both chains behave identically, promote only then. Rollback becomes
    trivial by construction.
11. **Review the live tree** — an archived zip is not the codebase; every
    finding gets verified against the live files before acting on it.
12. **Principles over fashion** — the 8-principles checklist runs on every
    change, with the standing override: a change that adds complexity without
    solving a concrete problem is rejected (KISS wins).
13. **Documentation** — if a README would embarrass me in review, the code
    isn't ready.
14. **Explain it simply** — if a non-technical reader can't understand the
    first section of a doc, the doc isn't finished yet.
15. **Consolidate, don't accumulate** — scattered note files drift apart;
    each topic now lives in exactly one readme (Oct 1 consolidation), and this
    document gets re-verified against the live tree before every revision.

---

## 7. What I cannot do yet (honest gaps)

- ~~No automated tests~~ **Closed on Sep 28:** a 53-test pytest suite now
  covers all 8 error-handler branches, the shared validators, the filter
  builder, driver-error → HTTP-code translation, the importer's hash-skip
  and row-skipping, and the main route flows — all against a fake pool,
  ~1.5s, no live database. Bonus: the suite immediately caught a real bug
  (whitespace-only machine names passed validation) and a test-harness
  lesson (services bind the pool at import time, so the fixture must patch
  each service module's `db` name). Still untested: export streaming,
  `init_db.py`, and everything in [cron_jobs/](cron_jobs/cronjobs_readme.md)
  and [log_rotation/](log_rotation/rotation.py).
- No Docker; the app is not yet packaged as an installable (`pyproject.toml`)
  project with lint (ruff) and type hints in CI.
- Migrations (Alembic) — schema changes still rely on idempotent
  `CREATE ... IF NOT EXISTS` instead of versioned, reversible scripts.
- No request correlation IDs in logs; the Blueprint split of `app.py` is
  recorded but not done; the pickle → CSV stage is a decision still open
  (audit artifact vs. direct `.pkl → PostgreSQL` import).
- MQTT bridge was studied conceptually but not yet implemented end-to-end;
  the MQTT demo still needs env-based config, auto-reconnect hardening, and
  real use of QoS/retained messages ([mqtt_readme](MQTT/mqtt_readme.md),
  *not used yet*).
- The cron-jobs scheduler has no test coverage and no graceful-shutdown path
  beyond `KeyboardInterrupt`; `db.py` still reports connection failure with a
  bare `print` instead of the structured logger it configures.
- SQL practice is still short of real-world use of joins, window functions,
  and `EXPLAIN ANALYZE` ([SQL_readme.md](SQL_Commands/SQL_readme.md)).
- The `Final_zip/` distribution copy must be re-exported by hand after every
  change and has already drifted from the live tree — a repeat of the
  "review the live tree" lesson, now with a process fix pending.
- Data visualization/dashboarding on top of the telemetry store is the obvious
  next layer.

## 8. Next month's direction

```text
grow the suite (export streaming, init_db, cron_jobs) + CI  →  pyproject packaging + ruff + type hints
   →  Alembic migrations  →  MQTT client hardening (env config, auto-reconnect, QoS)
   →  joins/window-functions practice  →  dashboard
```

The goal is unchanged: keep moving from "the API works on my machine" toward
"the service behaves correctly when something goes wrong" — the final
capstone week banked the server, pooling, timeouts, and the import ledger,
the automated tests came next, and the post-capstone tracks (logging,
scheduling, partitioning, regex) are each small, finished proofs that the
same patterns generalize.

---

*All file links in this document are relative and verified against the live
tree on 6 October 2026. The capstone's
[readme.md](MQTT/Machine_Sensor_API/readme.md) carries the full simple +
engineer detail; line-by-line code walkthroughs live per-topic, e.g.
[log_rotation/code_explanation.md](log_rotation/code_explanation.md).*
