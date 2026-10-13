# Intern Training — Consolidated Documentation

**Author:** Chinta Vijayakumar  
**Company:** Triniti Advanced Software Labs Pvt Ltd  
**Period:** 17 August 2026 – ongoing  
**Mentor:** V. Swaroop, Technical Consultant, High Technology Practice  
**Last consolidated:** (this file — built from the live tree)  

This is the single consolidated reference for the Intern Training repository at
`/f/Intern_Training/`. It merges the master training record, the IIoT platform
plan, and all per-topic readmes into one document. Dashboard/web application
plans are excluded by design.

------------------------------------------------------------------------

## Table of Contents

1. [Engineering Training Documentation — August to October 2026](#1-engineering-training-documentation--august-to-october-2026)
2. [Live IIoT Monitoring Platform Plan](#2-live-iiot-monitoring-platform-plan)
3. [MQTT — Broker, TLS/mTLS, Paho Client](#3-mqtt--broker-tlsltls-paho-client)
4. [Machine Sensor API (Capstone)](#4-machine-sensor-api-capstone)
5. [OOP Practice](#5-oop-practice)
6. [File Handling Practice](#6-file-handling-practice)
7. [PostgreSQL with Python + Flask](#7-postgresql-with-python--flask)
8. [CSV → pandas → Excel](#8-csv--pandas--excel)
9. [SQL — Working Vocabulary](#9-sql--working-vocabulary)
10. [Cron Jobs, Schedulers, and Table Partitioning](#10-cron-jobs-schedulers-and-table-partitioning)
11. [Rotating JSON Logging — Code Explanation](#11-rotating-json-logging--code-explanation)
12. [Regular Expressions](#12-regular-expressions)
13. [Machine Log Monitor (RegEx)](#13-machine-log-monitor-regex)
14. [Machine Log Monitor v3](#14-machine-log-monitor-v3)
15. [Linux and Unix Basics](#15-linux-and-unix-basics)
16. [High-Level IIoT Pipeline Sketch](#16-high-level-iiot-pipeline-sketch)
17. [Files Removed During Consolidation](#17-files-removed-during-consolidation)

------------------------------------------------------------------------

## 1. Engineering Training Documentation — August to October 2026

**Author:** Chinta Vijayakumar  
**Company:** Triniti Advanced Software Labs Pvt Ltd  
**Period:** 17 August 2026 – ongoing (six core weeks 17 Aug – 28 Sep, continuing since)  
**Mentor:** V. Swaroop, Technical Consultant, High Technology Practice  
**Last reviewed:** 8 October 2026 — full self-review against the mentor email thread (17 Aug – 7 Oct), the live tree, and a re-run of the test suite; verification record in §9

This document records the full training period: what was built, what was
learned, what went wrong, and which engineering habits changed along the way.
Every file reference is a clickable link to the real code in this repository.

The document is written in two layers, like every other doc in this repo:
the summary and the plain-words tables first, the precise technical detail
underneath.

### 1.1 Executive summary

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

The capstone is **Machine Sensor API**: a layered REST API managing machines
and sensor readings, which bulk-imports a **pickle snapshot of ~55,918
readings across 12 machines** into PostgreSQL with batch inserts and a
duplicate-safe import ledger.

The single biggest shift of the period: from *writing code that runs* to
*designing code that survives requests, failures, and concurrent users* —
pooled database connections returned through context managers, transactions
with rollback, parameterized queries, secrets in `.env`, time-bounded failure
(timeouts), and return-code validation on every external call.

The capstone's own story had three acts:

1. **Built (Sep 15–17):** a working layered API with bulk import.
2. **Hardened (Sep 18–21):** honest error semantics — 409/400 instead of
   blanket 500s, real JSON numbers from statistics, row-level import
   validation.
3. **Rebuilt, reviewed, cleaned (Sep 22–28):** a real WSGI server, connection
   pooling with timeouts, an import ledger replacing a guessed uniqueness
   rule; then an 8-principles design review (with an independent cross-check
   that caught one wrong claim); then a five-fix cleanup applied by building
   parallel versions first and promoting them only after both chains proved
   identical.

After the capstone, the same lessons were deliberately re-applied on smaller
ground: a standalone rotating-log demo, a scheduler-driven cron-jobs project
with PostgreSQL range partitioning, and regex practice — each one small enough
to finish, documented like production code.

On 8 October the whole period was self-reviewed against the original email
assignments and the live tree; the verification record is §9.

### 1.2 Timeline of assigned work

| Date | Task | Output |
|---|---|---|
| Aug 17 | OOP: 5 inheritance types + encapsulation, exception in every example | OOP/ — 6 files |
| Aug 17 | PostgreSQL: create database, schema, table | Database_Connection/setup.py |
| Aug 18 | File handling: read/write/append + errors | File_Handling/Handle.py, Csv_Handling.py |
| Aug 20 | `Postgremanager` class with CRUD + transactions | Database_Connection/setup.py |
| Aug 20–21 | Excel generation → pandas DataFrame → split strings | Conversion/Excel.py |
| Aug 24–26 | Flask API over the employee table | Database_Connection/main.py |
| Aug 26–31 | Mosquitto broker: service control, limits, bridge concepts | MQTT/mqtt_readme.md |
| Sep 3–7 | TLS/SSL certificate chain, SAN, 8883 listener | MQTT/mqtt_readme.md |
| Sep 8–10 | Paho client: 5 callbacks, paho logging, return-code checks | MQTT/Python/mqttdemo.py |
| Sep 15–17 | Machine Sensor API + bulk pickle import | MQTT/Machine_Sensor_API/ |
| Sep 18–21 | Capstone hardening: 409/400 exception mapping, JSON-number statistics, row-level import validation, conditions-list refactor | §3.9 |
| Sep 22–24 | Production rebuild: waitress, connection pooling, import ledger, `init_db.py`, TIMESTAMPTZ | §3.10 Pass 1 |
| Sep 25–26 | 8-principles design review + independent cross-check | §3.10 Pass 2 |
| Sep 27–28 | Five-fix cleanup built as parallel versions, verified, promoted; docs rewritten in simple + engineer two-layer format | §3.10 Pass 3 |
| Sep 29 | SQL command notes; log-rotation learning progression; `Database_Connection` moved from hard-coded credentials to `.env` | SQL_Commands/SQL_readme.md, log_rotation/rotation.py |
| Sep 30 | Log-rotation demos consolidated into one hybrid JSON + rotating-file handler after lost-log debugging; first range-partitioning demo | log_rotation/rotation.py, log_rotation/code_explanation.md |
| Oct 1 | Documentation consolidation (one readme per topic); cron-jobs project rebuilt on a real scheduler; table partitioning with just-in-time partitions and a composite primary key | cron_jobs/cronjobs_readme.md |
| Oct 4–6 | Regular expressions: eight matcher functions + full notes; `Final_zip/` distribution copy assembled | RegEx/regex_readme.md |
| Oct 8 | Full self-review: every email-assigned task cross-checked against the live tree; test suite re-run (53 passed); distribution copy verified in sync; doc-drift findings logged | §9 |

### 1.3 Technical sections

Each section follows the same shape: **Built → Learned → Takeaway.**

#### 1.3.1 Object-oriented programming

**Built:** one runnable file per topic — Single, Multiple, MultiLevel,
Hierarchical, Hybrid inheritance, and Encapsulation. Every file guards its
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

#### 1.3.2 File and CSV handling

**Built:** Handle.py exercising `w` / `x` / `a` / `r+` with per-mode error
handling (`FileExistsError`, `FileNotFoundError`);
Csv_Handling.py wrapping four CSV operations in a `CSVManager` class built on
`csv.DictReader` / `csv.DictWriter`.

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

#### 1.3.3 PostgreSQL fundamentals and the manager class

**Built:** setup.py — a `Postgremanager` class covering the full bootstrap
(`CREATE DATABASE` → `CREATE SCHEMA` → `CREATE TABLE`) plus employee CRUD with
commit/rollback.

**Learned:**
- `CREATE DATABASE` cannot run inside a transaction — connect to the built-in
  `postgres` database first and set `autocommit = True`.
- Parameterized queries (`%s` placeholders) for every value; f-strings only for
  identifiers like table names, never data.
- Transactions: `commit()` on success, `rollback()` on failure, and
  `cursor.rowcount` to know whether an UPDATE/DELETE actually matched a row.
- Connection **reuse** (check `conn.closed` and `conn.info.dbname` before
  reconnecting) — and its limits.

**Mistakes corrected:** early versions swallowed "database already exists"
into a generic except with a print; the later projects handle
`psycopg2.errors.DuplicateDatabase` explicitly. The password was hard-coded
here at first — accepted as a stage of learning, replaced by `.env` in the
capstone, and finally back-ported to this project on Sep 29.

#### 1.3.4 First REST API

**Built:** a Flask `MethodView` exposing the employee table:

```text
GET /employees   GET /employees/<email>   POST /employees
PUT /employees/<email>   DELETE /employees/<email>
```

Field validation runs before any database call, responses use a consistent
JSON envelope (`status` / `message` / `data`), and screenshots record each
operation: single insert, batch insert, duplicate-email rejection, update,
delete.

**Learned:**
- POST accepts a single object **or** a list — one endpoint, batch-capable.
- Validation lives in the route; SQL lives in the manager class. That
  separation grew into the full routes/services/database layering.
- A browser can only speak GET — POST/PUT/DELETE need Postman, `curl`, or JS
  `fetch`.

#### 1.3.5 Data conversion with pandas

**Built:** Excel.py, a pipeline from work.csv (ETHUSD hourly OHLCV) to
Work_sample_processed.xlsx: parse dates with an exact format string → split
`Symbol` into characters (`abc → ['a','b','c']`) → Unix timestamp (ms) →
Day/Month/Year/Hours/Minutes/Seconds → `fillna(0)` → format the date back to
the source style → Excel export with auto-sized columns via openpyxl →
dictionary records.

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

#### 1.3.6 MQTT and the Mosquitto broker

See [§3](#3-mqtt--broker-tlsltls-paho-client) for the full MQTT notes.

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

#### 1.3.7 Python MQTT client

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
  codes (bad credentials, not authorized, quota exceeded).

**Takeaway:** `logging.exception()` inside each callback keeps one bad message
from killing the client — resilient handlers are the difference between a demo
and a service.

#### 1.3.8 Capstone: Machine Sensor API

See [§4](#4-machine-sensor-api-capstone) for the full capstone notes.

**The assignment:** a Flask + PostgreSQL API to manage machine data — add/
retrieve machine details, store sensor readings, import historical data.

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

**Bulk import reality:** the snapshot data from 28-03-2025 lives in
MQTT/Machine_Sensor_API/data/ — the pickle snapshot
(`all_topics_20250328-114500.pkl`) converts to **55,918 readings across 12
machines** (verified by counting the generated CSV). The two-stage pipeline in
pickle_importer.py goes `.pkl → CSV → PostgreSQL`, leaving a human-readable CSV
artifact and skipping broken rows.

#### 1.3.9 Post-capstone hardening (Sep 18–21)

**The theme:** the API handled the happy path with honest 500s; this pass made
the error *semantics* honest and the responses client-friendly.

- **Typed exception translation** — `ConflictError` and the FK-error subclass
  (both under `DatabaseError`); services translate driver integrity errors at
  the source. Duplicate machine name → **409**; reading for a nonexistent
  machine → **400** with an actionable message; everything else still 500.
- **Statistics as JSON numbers** — `NUMERIC` aggregates arrived in Python as
  `Decimal`, which Flask serializes as *strings*. Aggregates are now cast
  `::float8` in SQL, so `/readings/statistics` returns real numbers, and
  `null` when nothing matches.
- **Row-level importer validation** — bad tags/timestamps were already
  skipped, but a single non-numeric `VR` value could abort an entire ~56k-row
  file transaction. `sensor_value` is now validated per row and counted in
  `records_skipped`.
- **Readability refactor** — dynamic filters no longer grow out of a
  `WHERE 1 = 1` string; they are a conditions list joined with `" AND "`.
  Same SQL, easier to read. *This idea later grew into the single shared
  `_build_reading_filters()` helper.*

#### 1.3.10 Production rebuild, design review, and the versioned-cleanup method (Sep 22–28)

This final stretch turned the capstone from a working API into one that is
reviewed, armored, and documented like production software — in three passes.

**Pass 1 — the production rebuild (Sep 22–24)**

| What changed | The problem it solved | In plain words |
|---|---|---|
| Flask dev server with `debug=True` → **waitress** + `wsgi.py` | The dev server's interactive debugger is a remote-code-execution door | A real service gets a real front door |
| Fresh connection per request → **`ThreadedConnectionPool`** with `with db.cursor()` context managers | TCP + auth per request doesn't survive traffic; manual cleanup gets forgotten | Reusable shopping carts instead of buying a new one per customer |
| Unique constraint on `(machine_id, sensor_tag, timestamp)` → **dropped**; duplicates guarded by the **`import_batches` ledger** (SHA-256 file hash, recorded in the same transaction) | The constraint was a business claim nobody could prove — and it once multiplied one file ~211× into 11.8M rows | Fingerprint-stamp the source file; the same content can never be filed twice |
| Server ran DDL at boot → **`init_db.py`** | A restart must never run DDL | Renovation plans are run deliberately, not on every boot |
| `TIMESTAMP` → **`TIMESTAMPTZ`** UTC; fail-fast `config.py` validating `.env` | A reading must mean the same instant worldwide; half-configured boots | Every setting checked at the door before the app wakes up |

**Pass 2 — the 8-principles review (Sep 25–26)**

The whole codebase was reviewed against eight classic principles — cohesion &
single responsibility, encapsulation & abstraction, loose coupling & modularity,
reusability & extensibility, portability, defensibility, maintainability &
testability, and simplicity (KISS · DRY · YAGNI). The honest headline scores:
**Defensibility 4.5/5** (strongest), **Maintainability & Testability 2.5/5**
(weakest at the time — zero automated tests), **overall ≈ 3.4/5**.

Two things made the review more valuable than a scorecard:
- **A second, independent review** converged on nearly every finding and got
  one claim wrong — it flagged `DROP_LEGACY_*` SQL as live, but a full-text
  search proved the live code has no `DROP` at all. Lesson: **review the live
  tree, not the archive.**
- **A rule was adopted and is now standing policy:** the eight principles are
  *constraints on decisions, not excuses to add layers*.

**Pass 3 — the five-fix cleanup, built as versions, then promoted (Sep 27–28)**

1. **DB timeouts** — `connect_timeout=5`, `statement_timeout=15000`
   (env-tunable).
2. **Rotating logs** — `RotatingFileHandler` (10 MB × 5) + `LOG_LEVEL` from env.
3. **Dead code removed** — `count_machines()`, defined and never called (YAGNI).
4. **One filter builder** — `_build_reading_filters()`, called by list, export,
   and statistics.
5. **Shared validators** — input checks moved into `utils/validation.py`; the
   once-triplicated `from ≤ to` check became one `validate_from_to_order()`.

**The method (the transferable lesson):** every fix was first built as a
parallel `*_v3.py` copy while the originals stayed untouched. Only after both
chains proved identical in behavior were the v3 files promoted over the
originals and the `_v3` names stripped. Rollback was trivial by construction.

#### 1.3.11 Standalone rotating-JSON logging

**Built:** rotation.py — one hybrid handler demo: every log record is formatted
as **one-line JSON** (unix-epoch timestamp, level, logger name, message,
exception block when present) and written both to a **rotating file chain**
(`app.log` → `app.log.1` → … → `app.log.10`) and to the console.

**Learned:**
- `RotatingFileHandler.maxBytes` + `backupCount` = a diary that archives
  itself; the disk can never fill.
- `logger.propagate = False` stops records from reaching the root logger.
- `if logger.handlers: return` guards against duplicate handler attachment on
  re-imports.
- JSON-per-line is the format log collectors want to see; free-text logs are
  for humans only.

**Incident record (Sep 30):** earlier log-rotation attempts were split across
multiple demos and log lines went missing between them; the fix was
consolidating into this one hybrid handler. Lesson: one logging setup per
application, wired in one place.

#### 1.3.12 Cron jobs, schedulers, and table partitioning

See [§10](#10-cron-jobs-schedulers-and-table-partitioning) for the full notes.

**Built (restructured Oct 1):** a scheduler-based project that inserts the
current Unix timestamp every minute into a **range-partitioned** PostgreSQL
table and creates partitions just-in-time.

**Learned:**
- OS cron vs in-process schedulers: `crontab -e` runs scripts on Linux; on
  Windows, Task Scheduler; in Python, the `schedule` module or APScheduler.
  This project uses **APScheduler's `BlockingScheduler`** with two
  `cron`-trigger jobs.
- **Partition key rule:** PostgreSQL requires the partition column to be part
  of the primary key — hence the composite `PRIMARY KEY (id, unix_ts)`.
- **Just-in-time partitioning:** inserts originally failed when the matching
  partition didn't exist yet; the insert job now creates the partition *before*
  inserting, and the `DEFAULT` partition catches anything that still slips
  through.
- Partitioning pays off at deletion time: dropping old data becomes `DROP TABLE`
  on one child partition instead of batched `DELETE`s.

**Takeaway:** the pipeline shape — bootstrap script → long-running scheduler →
structured logs → idempotent SQL — is the same skeleton as the capstone's
importer, just time-driven instead of request-driven.

#### 1.3.13 Regular expressions

See [§12](#12-regular-expressions) for the full notes.

**Built:** eight matcher functions driven by an interactive `main()`: exact
five-digit match with lookarounds (`(?<!\d)\d{5}(?!\d)`), lowercase-only and
uppercase-only scans, grouped letters + numbers extraction, "starts with A" /
"ends with Z" via word boundaries, digits-only and no-digits scans.

**Known issues (Oct 8 review):** the concepts file is literally named `.py`,
which hides it from most tooling (renaming to `regex_concepts.py` is pending),
and regex_readme.md has drifted from the code: it documents
`match_letters_and_numbers()` with the grouping pattern `([a-zA-Z]+)(\d+)`,
while the implementation actually uses two separate `findall` calls.

**Learned:**
- `^abc` (anchor) is not `[^abc]` (negation) — one character, opposite
  meaning.
- Lookarounds (`(?<!\d)…(?!\\d)`) match a position, not a character — the clean
  way to say "exactly five digits, not part of a longer number".
- Named real uses: input validation, log parsing with groups, `re.sub()` data
  cleaning.

**Takeaway:** regex is a validation tool, not a puzzle toy.

### 1.4 Supporting skills

- **Linux basics** — see [§15](#15-linux-and-unix-basics): navigation, file
  ops, `grep`/`find`/`wc`, `sort`/`uniq`; why Linux matters for servers/gateways
  in IIoT.
- **Testing discipline** — Postman collections with chained variables, API
  screenshots per operation, and writing the readme *while* testing so docs
  never drift. Plus offline verification with a faked connection layer when a
  live database isn't available, and since Sep 28 a real pytest suite.
- **SQL as a working vocabulary** — see [§9](#9-sql--working-vocabulary): DDL/DQL/DML/DCL/TCL
  categories, the constraint and index toolbox used in the capstone, and an
  honest "not used yet" list.
- **Documentation habit** — every folder carries a README with real click-through
  links; notes record *why*, not just *what*; every doc opens with a simple
  version a non-technical reader can follow. On Oct 1 the scattered per-topic
  note files were consolidated into one readme per folder.

### 1.5 Error log (encountered → resolved)

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
| Duplicate readings on re-import | Overlapping snapshots | First fixed with `ON CONFLICT DO NOTHING` + unique constraint; **final fix:** the `import_batches` hash ledger — content, not constraints |
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
| Cron readme still documented `schedule.every(...).do()` calls | The readme kept `schedule`-module remnants after the Oct 1 rewrite to APScheduler | Found in the Oct 8 review; readme to be cleaned |
| Regex readme showed a grouping pattern the code doesn't use | Notes were written before the implementation changed to two `findall` calls | Found in the Oct 8 review; docs drift, code is the source of truth |

### 1.6 How the period changed my engineering habits

1. **Secrets** — from hard-coded passwords to `.env` + fail-fast `config.py`.
2. **Connections** — from one long-lived reused connection, through
   per-request connections with `finally` cleanup, to a pooled manager with
   context managers that always return the connection (and discard broken ones).
3. **SQL** — from string concatenation to parameterized queries everywhere;
   identifiers kept out of value positions; filters built in one shared place.
4. **Failure handling** — from printing exceptions to typed exceptions
   (`DatabaseError` and family), rollback, `rowcount` checks, and
   `logging.exception()`.
5. **Time-bounded failure** — a stuck database or runaway query now hits
   `connect_timeout`/`statement_timeout`: fast, visible, logged failure beats
   slow, silent failure.
6. **External calls** — always validate the immediate return code *and* handle
   the async confirmation (Paho lesson; generalizes to any messaging system).
7. **Data integrity** — enforce only claims that can be proven; protect the rest
   at ingestion (the hash ledger), so a wrong assumption can't multiply into
   11.8M rows again.
8. **Structure** — routes/services/database layering, earned after flat scripts
   became hard to navigate.
9. **Readability** — replaced `WHERE 1 = 1` string surgery with a conditions
   list, then a single shared builder; code is read far more often than it is
   written.
10. **Versioned change discipline** — build the fix as a parallel copy, verify
    both chains behave identically, promote only then. Rollback becomes trivial
    by construction.
11. **Review the live tree** — an archived zip is not the codebase; every
    finding gets verified against the live files before acting on it.
12. **Principles over fashion** — the 8-principles checklist runs on every
    change, with the standing override: a change that adds complexity without
    solving a concrete problem is rejected (KISS wins).
13. **Documentation** — if a README would embarrass me in review, the code isn't
    ready.
14. **Explain it simply** — if a non-technical reader can't understand the first
    section of a doc, the doc isn't finished yet.
15. **Consolidate, don't accumulate** — scattered note files drift apart; each
    topic now lives in exactly one readme (Oct 1 consolidation), and this
    document gets re-verified against the live tree before every revision.

### 1.7 What I cannot do yet (honest gaps)

- ~~No automated tests~~ **Closed on Sep 28:** a 53-test pytest suite now
  covers all 8 error-handler branches, the shared validators, the filter
  builder, driver-error → HTTP-code translation, the importer's hash-skip and
  row-skipping, and the main route flows — all against a fake pool, ~1.5s, no
  live database. Still untested: export streaming, `init_db.py`, and
  everything in cron_jobs/ and log_rotation/.
- No Docker; the app is not yet packaged as an installable (`pyproject.toml`)
  project with lint (ruff) and type hints in CI.
- Migrations (Alembic) — schema changes still rely on idempotent `CREATE ...
  IF NOT EXISTS` instead of versioned, reversible scripts.
- No request correlation IDs in logs; the Blueprint split of `app.py` is
  recorded but not done; the pickle → CSV stage is a decision still open.
- MQTT bridge was studied conceptually but not yet implemented end-to-end; the
  MQTT demo still needs env-based config, auto-reconnect hardening, and real use
  of QoS/retained messages.
- Small portability/cleanliness debts in the early projects, found in the Oct 8
  review: Csv_Handling.py hard-codes an absolute `F:\` path, the OOP demos guard
  calls that cannot fail, and `Encapsulation.py` defines a private method that is
  never used. Recorded here rather than silently rewritten.
- The cron-jobs scheduler has no test coverage and no graceful-shutdown path
  beyond `KeyboardInterrupt`; `db.py` still reports connection failure with a
  bare `print` instead of the structured logger it configures.
- SQL practice is still short of real-world use of joins, window functions, and
  `EXPLAIN ANALYZE`.
- The `Final_zip/` distribution copy is re-exported by hand. The Oct 8 review
  verified it back **in sync** with the live tree (only a runtime log file
  differs). The manual process itself is still the risk.
- Data visualization/dashboarding on top of the telemetry store is the obvious
  next layer.

### 1.8 Next month's direction

```text
grow the suite (export streaming, init_db, cron_jobs) + CI  →  pyproject packaging + ruff + type hints
   →  Alembic migrations  →  MQTT client hardening (env config, auto-reconnect, QoS)
   →  joins/window-functions practice  →  dashboard
```

The goal is unchanged: keep moving from "the API works on my machine" toward
"the service behaves correctly when something goes wrong".

### 1.9 Verification record — 8 October 2026

A full pass comparing this document, the mentor email thread (17 Aug – 7 Oct),
and the live tree.

**Task coverage: 10/10.** Every task assigned by email has a live artifact — OOP
(6 files), the PostgreSQL bootstrap, file/CSV handling, the Excel → DataFrame
pipeline, the first Flask API, Mosquitto + Paho MQTT, the Machine Sensor API
capstone, the cron-jobs/partitioning project, and both regex exercises.

**Checks actually run:**

| Check | Method | Result |
|---|---|---|
| Capstone test suite | `pytest tests` in `MQTT/Machine_Sensor_API` | **53 passed** (~4 s, fake pool, no live DB) |
| Distribution copy sync | `diff -rq` of `Final_zip/` against the live tree | Code identical; only a runtime log file differs |
| Task coverage | Task-by-task cross-check of every email assignment | 10/10 tasks have live artifacts |
| Doc ↔ code spot checks | Pooling, timeouts, import ledger, `_build_reading_filters()`, shared validators | All confirmed in the live files |

**Could not be executed here (verified by inspection only):** live PostgreSQL
behavior (pooling, partition creation) and the MQTT TLS flow — no database or
broker was running; the test suite deliberately runs against a fake pool by
design.

**Open cleanup items found by the review:** the `RegEx/.py` filename, the regex
readme drift, `schedule`-module remnants in cronjobs_readme.md, the `F:\` path in
Csv_Handling.py, and two stale claims in this document itself — which is the
"review the live tree" lesson applying to the documentation too.

------------------------------------------------------------------------

## 2. Live IIoT Monitoring Platform Plan

**Status:** Proposed architecture  
**Foundation:** Existing Flask + PostgreSQL Machine Sensor API (`/f/Intern_Training/MQTT/Machine_Sensor_API/` and the working copy at `./`), Mosquitto MQTT broker (running on Windows, port 8883, TLS/mTLS), Paho Python client (`mqttdemo.py` at `/f/Intern_Training/MQTT/Python/`), Machine Log Monitor, and the MQTT training notes at `/f/Intern_Training/MQTT/mqtt_readme.md`.  
**Goal:** Evolve the existing work into a reliable, secure, real-time industrial monitoring platform using actual API/database data rather than mock data.  
**Plan document:** `/f/Intern_Training/Live_IIoT_Monitoring_Platform_Plan.md`.

### 2.1 Executive Summary

Build the platform incrementally around the existing backend — the Flask +
PostgreSQL Machine Sensor API at `/f/Intern_Training/MQTT/Machine_Sensor_API/`
(working copy at `./`). Machines or a telemetry simulator publish sensor
readings to a Mosquitto broker over MQTT/TLS (port 8883, mTLS already
configured; see `/f/Intern_Training/MQTT/mqtt_readme.md`). A dedicated Python
ingestion worker validates each message and persists accepted readings through
the existing service/database layer. The Flask API exposes machine status,
latest readings, historical trends, and alarms. A web dashboard consumes those
endpoints and presents an operations-focused view of machine health.

The first release should be a **modular monolith with a separately managed
ingestion worker**. Do not introduce Kafka, Kubernetes, or a large microservice
estate before throughput and operational requirements justify them.

**Existing MQTT infrastructure this plan builds on:**
- Mosquitto broker: Windows service, listener 8883, `require_certificate true`,
  `use_identity_as_username true`, `allow_anonymous false`.
- Certificate chain: CA → server cert → client cert, built with OpenSSL; SAN
  config for IP/DNS; see `mqtt_readme.md` for the full chain and `mosquitto.conf`.
- Paho client demo: `mqttdemo.py` — Callback API v2, TLS 8883, all five
  callbacks, return-code checks, `logging.exception` in every error path.
- Open items from training: QoS 0/1/2 in practice, retained messages, last will
  and testament, persistent sessions — studied conceptually, not yet used in
  production.

### 2.2 Goals and Non-goals

**Goals**
- Show machine inventory, connectivity, telemetry freshness, and current
  operating condition.
- Receive sensor telemetry through MQTT with TLS/mTLS.
- Persist measurements in PostgreSQL and query historical ranges efficiently.
- Detect threshold-based conditions and record alarm lifecycle events.
- Expose a stable, validated API to the dashboard.
- Make failures observable and recoverable.
- Preserve existing Machine Sensor API functionality and tests.

**Non-goals for the first release**
- Predictive maintenance or machine-learning diagnosis.
- PLC/SCADA control commands or remote actuation.
- Multi-region high availability.
- A complex event-streaming platform before it is needed.
- Treating log entries as sensor measurements.

### 2.3 Proposed System Architecture

```mermaid
flowchart TB
    subgraph OT["Industrial / Device Layer"]
        M["Machines and sensors"]
        SIM["Telemetry simulator for development"]
    end

    subgraph MSG["Messaging Layer"]
        BROKER["Mosquitto MQTT broker"]
        PKI["CA, server and client certificates"]
        ACL["Topic ACLs"]
    end

    subgraph APP["Application Layer"]
        ING["Python MQTT ingestion worker"]
        QUEUE["Optional: bounded queue between consumer and storage"]
        VAL["Payload validation and normalization"]
        RULES["Threshold and alarm evaluation"]
        API["Existing Flask REST API"]
    end

    subgraph DATA["Persistence Layer"]
        DB[(\"PostgreSQL\")]
        MACH[\"Machines and sensor metadata\"]
        READ[\"Sensor readings\"]
        ALARM[\"Alarm events and state\"]
    end

    subgraph UI[\"Presentation Layer\"]
        DASH[\"IIoT operations dashboard\"]
        HIST[\"Historical trends and reports\"]
    end

    M -->|\"MQTT over TLS/mTLS\"| BROKER
    SIM -->|\"MQTT over TLS/mTLS\"| BROKER
    PKI -. \"trust and identity\" .-> BROKER
    BROKER -->|\"topic subscription\"| ING
    ING --> QUEUE
    QUEUE --> VAL
    VAL -->|\"valid telemetry\"| RULES
    RULES --> DB
    ING -->|\"persist via shared service/repository layer\"| DB
    QUEUE .->|\"drain at storage pace\"| DB
    API <--> DB
    DASH -->|\"REST: status, latest values, alarms\"| API
    HIST -->|\"REST: time-range queries and statistics\"| API
    DB --- MACH
    DB --- READ
    DB --- ALARM
```

**Component responsibilities**

| Component | Responsibility | Deployment boundary |
|---|---|---|
| Machine / simulator | Produce timestamped telemetry | Device or development process |
| Mosquitto | Route MQTT messages; enforce configured authentication and topic permissions | Independent service |
| MQTT ingestion worker | Subscribe, decode, validate, normalize, handle delivery and persistence failures | Separate process |
| Optional queue | Buffer between arriving messages and slow storage; bounds memory | Separate process or in-process with the worker |
| Shared backend service/repository layer | Apply database operations and transaction policy consistently (needs its own db instance in the worker, not the module-level singleton) | Reused Python package |
| PostgreSQL | Store machine metadata, measurements, and alarm state | Database service |
| Flask API | Validate HTTP requests and expose current/historical data | Separate web process |
| Dashboard | Display operational status, trends, and alarm workflows | Web application |

The ingestion worker and API may share application modules, but should not
depend on one another being alive. A dashboard/API restart must not silently
stop MQTT consumption.

**Critical constraint (from review):** the current `services/*.py` modules import
the shared `db = DatabaseManager()` singleton at module level. The ingestion
worker **must not** reuse that singleton implicitly — it needs its own
`DatabaseManager()` instance (its own connection pool) so that a worker restart
does not depend on the API process and vice versa. This should be resolved in
Phase 0 by making services accept a `db` instance or use a factory, rather than
relying on the module-level `db`.

### 2.4 End-to-End Data Flow

1. A machine publishes a message to a documented topic, for example
   `factory/line-1/M102/telemetry`.
2. Mosquitto authenticates the client, checks topic permissions, and routes the
   message to subscribers.
3. The ingestion worker decodes the payload and validates its schema, machine
   identity, sensor tag, units, value, and timestamp.
4. Invalid messages are counted and logged with safe diagnostic context; they
   must not crash the consumer.
5. Valid readings are normalized to UTC and checked against the chosen duplicate
   policy.
6. The worker persists the reading through the shared service/repository layer.
   If a queue is adopted, the worker drains the queue at the storage pace rather
   than writing synchronously per message; for the MVP, direct synchronous
   persistence is acceptable at modest telemetry volume — the queue pattern
   (MQTT → consumer → queue → worker → PostgreSQL) from the IIoT Python guide
   should be revisited when throughput or resilience requirements justify it.
7. The alarm evaluator checks configured thresholds and records state
   transitions. For the MVP this is a simple per-reading threshold check against
   configured `warning_threshold`/`critical_threshold` values in the
   `machine_sensors` table; stateful composite conditions (e.g. "N breaches in
   T minutes") are a later extension, not a Phase 3 requirement.
8. The dashboard fetches current status and recent readings from the API.
   Historical views query time-bounded data.
9. If the broker or database fails, the worker reconnects and follows an explicit
   retry/replay policy. Delivery guarantees must be designed end-to-end rather
   than assumed from MQTT QoS alone.

### 2.5 MQTT Contract

**Topic convention**

```text
factory/{site_id}/{machine_id}/telemetry
factory/{site_id}/{machine_id}/status
factory/{site_id}/{machine_id}/event
```

Start with telemetry and status. Add event topics when the event schema and
ownership are defined.

**Example telemetry payload**

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
- `schema_version` is required; only one active schema version is accepted per
  topic family. Breaking changes get a new version and are evaluated separately.
- `message_id` is a stable identifier used for duplicate detection.
- `machine_id` must match the machine encoded in the topic.
- `sensor_tag` and `unit` must be allowed for that sensor. Units use a controlled
  vocabulary per sensor type (e.g. temperature: `degC`, `degF`; pressure: `bar`,
  `psi`, `kPa`; the allowed set is defined in the `machine_sensors` table or a
  reference table, not inferred from the payload).
- `value` must be numeric and finite; define valid operating and engineering
  ranges.
- `measured_at` must be timezone-aware ISO 8601. Record ingestion time
  (`received_at`) separately in the `telemetry_messages` table or the readings
  row metadata so message lag can be measured.
- Payload size and accepted schema version should be bounded.
- Never trust topic or payload identity without validation and authorization
  rules.

**Delivery policy**
- Begin with QoS 1 when at-least-once delivery is appropriate.
- Assume duplicate delivery is possible.
- Use a unique message identifier or a well-defined natural key to make
  persistence idempotent.
- Acknowledge/complete processing only according to the selected Paho callback
  and QoS flow; do not claim database durability simply because the callback
  received a message.
- Decide whether a failed message is retried in memory, persisted to a durable
  local queue, or routed to a dead-letter workflow. Document data-loss behavior
  for process crashes.

### 2.6 Data Model

Retain the existing `machine_schema.machines` and
`machine_schema.sensor_readings` tables unless review shows a specific gap.

**Existing core tables**

**machines** — `id` (primary key), `machine_name` (unique machine identifier),
`created_at` (registration timestamp)

**sensor_readings** — `id` (primary key), `machine_id` (foreign key to
`machines`), `sensor_tag` (sensor identifier), `sensor_value` (numeric value),
`timestamp` (measured timestamp)

**Recommended additions after migration review**

**machine_sensors** — `id`, `machine_id`, `sensor_tag`, `unit`, `display_name`,
`warning_threshold`, `critical_threshold`, `enabled`. Unique constraint on
`(machine_id, sensor_tag)`.

**telemetry_messages** (optional, useful if end-to-end traceability is required)
— `message_id`, `machine_id`, `received_at`, `processing_status`,
`failure_reason`. Unique `message_id`; avoid storing unlimited duplicate raw
payloads without a retention policy.

**machine_status** — `machine_id`, `connection_state`, `last_seen_at`,
`last_reading_at`, `updated_at`. Connectivity and telemetry freshness are
different signals. A connected MQTT client does not prove that the machine is
producing healthy readings.

**alarm_events** — `id`, `machine_id`, `sensor_tag`, `severity`, `event_type`,
`observed_value`, `threshold_value`, `opened_at`, `acknowledged_at`,
`resolved_at`, `status`. Keep alarm transitions auditable. Define whether
repeated threshold breaches update an existing active alarm or create separate
events.

**Indexing and retention**
- Preserve and verify the existing `(machine_id, timestamp)` and timestamp
  indexes.
- Add indexes for active alarms and machine/sensor lookups as query patterns
  require.
- Use UTC consistently.
- **Establish a retention and archival policy as soon as the `telemetry_messages`
  and `alarm_events` tables are added (Phase 3), not deferred to Phase 5.** These
  tables accumulate data from day one and a retroactive retention policy is harder
  than a designed one.
- Consider time partitioning only after measuring volume and query performance;
  choose partition keys and uniqueness constraints carefully.

### 2.7 Backend API Plan

Keep existing endpoints backward-compatible. Add focused endpoints such as:

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/v1/overview` | Dashboard KPIs and counts |
| `GET` | `/api/v1/machines` | Machine list and metadata |
| `GET` | `/api/v1/machines/{id}/status` | Connectivity, freshness, and latest values |
| `GET` | `/api/v1/machines/{id}/readings/latest` | Latest reading per sensor |
| `GET` | `/api/v1/readings` | Filter by machine, sensor, and time range with pagination |
| `GET` | `/api/v1/readings/statistics` | Min/max/average for a bounded period |
| `GET` | `/api/v1/alarms` | Filter alarms by status, severity, machine, and time |
| `POST` | `/api/v1/alarms/{id}/acknowledge` | Acknowledge an alarm, subject to authorization |
| `GET` | `/health/live` | Process liveness |
| `GET` | `/health/ready` | Dependency readiness, including database availability |

These are proposed additions, not claims about current routes. Keep current routes
working while a versioned API is introduced. Do not expose raw database errors or
credentials in HTTP responses.

### 2.8 Dashboard Information Architecture

**Screen A — Operations overview**
- KPI strip: total machines, healthy, warning, critical, offline/stale.
- Machine status table with last-seen time and most important current values.
- Active alarms ordered by severity and age.
- Telemetry freshness indicator.
- A visible timestamp showing when dashboard data was last refreshed.

**Screen B — Machine detail**
- Machine identity, site/line, connectivity, and telemetry freshness.
- Current values for each configured sensor, with units and threshold context.
- Time-series chart with selectable time window.
- Recent alarms and machine events.
- Historical readings table and export action where authorized.

**Screen C — Alarms and events**
- Active, acknowledged, and resolved states.
- Severity, machine, sensor, observed value, threshold, and event time.
- Filters by site, machine, severity, status, and time range.
- Acknowledgement and resolution history.

**Screen D — Historical analysis**
- Machine and sensor selectors.
- Time-range selection and server-side pagination.
- Trends, minimum/maximum/average, and CSV export.
- Clear empty, loading, stale-data, and API-error states.

**Visual direction**
Use an industrial operations-console layout: compact status cards, a dense but
readable machine table, prominent alarm severity, restrained colors, dark or
light theme based on operator environment, and charts with clearly labeled units
and time axes. Avoid decorative charts that do not answer an operational
question.

### 2.9 Live Update Strategy

**Release 1:** Poll the API at a controlled interval (for example, every 2–5
seconds for the overview, subject to database load). Use bounded time windows,
efficient latest-reading queries, and request cancellation on navigation.

**Release 2:** Add Server-Sent Events (SSE) or WebSockets if polling latency or
request load becomes a measured problem.

Do not connect every browser directly to MQTT or expose broker credentials to the
frontend. The backend remains the access-control and data-contract boundary.

### 2.10 Reliability, Security, and Observability

**Reliability**
- Use bounded connection and statement timeouts.
- Define transaction boundaries and rollback behavior.
- Make ingestion idempotent.
- Apply bounded retries with backoff and jitter.
- Avoid unbounded in-memory queues.
- Track stale telemetry independently of process health.
- Provide graceful shutdown and close database/MQTT resources.
- Test broker outages, database outages, duplicate messages, and malformed
  payloads.

**Security**
- Use TLS/mTLS with certificate validation; never disable hostname verification
  to work around certificate errors.
- Enforce broker authentication and topic ACLs.
- Store secrets in environment configuration or a secret manager, not source
  control.
- Rotate credentials exposed in archives.
- Protect dashboard and API write operations with authentication and
  authorization.
- Restrict CORS, payload sizes, request rates, and sensitive logs.
- Keep control/actuation commands out of the first release.

**Observability**
Track at minimum: MQTT connection state and reconnect count; messages received,
accepted, rejected, duplicated, and persisted; ingestion processing latency and
database write latency; database pool usage, timeouts, and failures; age of the
latest reading per machine; active alarms and alarm-resolution time; API latency
and HTTP error rates.

Use structured logs with correlation/message IDs where practical. Do not log
credentials, private keys, or complete sensitive payloads.

### 2.11 Testing Strategy

1. **Unit tests:** payload validation, timestamp normalization, threshold logic,
   duplicate policy.
2. **Service tests:** database transaction and error behavior, using the existing
   test conventions.
3. **API tests:** filters, pagination, authorization, validation, and error
   responses.
4. **Integration tests:** a test broker plus PostgreSQL for publish-to-persist
   behavior.
5. **Failure tests:** broker unavailable, database unavailable, reconnect,
   malformed payload, duplicate delivery, and worker restart.
6. **Dashboard tests:** loading, empty, stale, error, and populated states.
7. **End-to-end acceptance:** publish a known telemetry message and verify it
   appears in PostgreSQL, API responses, and the dashboard within the agreed
   latency target.

Keep the current API tests passing throughout the work.

### 2.12 Phased Implementation Plan

**Phase 0 — Baseline and cleanup**
- Review existing routes, services, schema, configuration, and tests.
- **Rotate exposed database credentials** in the repository `.env` file.
- Confirm development and test database separation.
- Document current behavior and compatibility constraints.
- **Refactor services to accept a `db` instance or use a factory** so the
  ingestion worker can run with its own `DatabaseManager()` and connection pool,
  not the module-level singleton. This is the critical-path item from the review.
- Decide the authentication model for the dashboard API (see §2.14).

**Exit criteria:** baseline tests pass; architecture and current endpoint
contracts are documented; services are refactored for independent worker use;
auth model decision recorded.

**Phase 1 — Telemetry contract and broker**
- Define topic names and JSON schema.
- Verify certificate validation, broker ACLs, and client authentication.
- Add a repeatable development telemetry publisher.

**Exit criteria:** authorized clients publish valid messages; unauthorized
connections/topics are rejected. **QoS note:** the team has not yet used QoS
0/1/2 in practice (current demo runs on the default). Phase 1 exit criteria
should include: team can explain QoS 0/1/2 tradeoffs and has tested at least QoS
1 on the broker, since the delivery policy in §2.5 assumes QoS 1.

**Phase 2 — Ingestion worker**
- Create a separately runnable worker using the existing Paho conventions.
- Add validation, normalization, logging, idempotency, and database
  persistence.
- Add retry/recovery behavior and worker health reporting.
- **Consider repurposing the existing `import_batches` ledger** as a
  message-level ledger (one row per `message_id` with processing status) for
  end-to-end traceability, rather than building a new table from scratch. The
  existing SHA-256 fingerprint pattern translates naturally to a message-level
  dedup/ack ledger.

**Exit criteria:** a published message is persisted once logically, and failures
are observable and recoverable under the documented policy.

**Phase 3 — Status and alarm backend**
- Add machine freshness/status and sensor configuration as needed.
- Add threshold rules and auditable alarm state transitions.
- Add dashboard-focused API endpoints without breaking existing routes.

**Exit criteria:** status and alarm APIs return real database-backed results with
tests.

**Phase 4 — Dashboard MVP**
- Build overview, machine detail, alarm list, and history views.
- Integrate the existing API.
- Implement loading, stale, empty, and error states.
- Use actual telemetry; do not substitute mock values for live backend data.

**Exit criteria:** an end-to-end published reading is visible in the appropriate
dashboard view.

**Phase 5 — Hardening and deployment**
- Run failure and load tests.
- Establish retention, backup, restore, and operational runbooks.
- Add metrics, alerting, access control, and deployment configuration.
- Measure before introducing queues, caching, or additional infrastructure.

**Exit criteria:** documented operational limits, tested recovery behavior, and a
repeatable deployment procedure.

### 2.13 Suggested Repository Layout

Adapt this to the existing repository instead of mechanically renaming working
modules.

**Repository restructure approach (from review):** the proposed layout implies
moving existing modules (`app.py`, `config.py`, `routes/`, `services/`,
`database/`, `utils/`, `tests/`) under a `backend/` directory. Do not do this as
a big-bang rename. Prefer an incremental approach: add `ingestion/` alongside the
existing flat structure first (Phase 2), keep the existing modules where they are
until a concrete reason to move them arises, and only restructure when a file's
new home is unambiguous. Each move must keep the test suite green. The current
working copy at `./` and the archive at
`/f/Intern_Training/MQTT/Machine_Sensor_API/` are both valid entry points;
confirm which tree is authoritative before restructuring.

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

Do not commit real certificates, private keys, passwords, production broker
configuration, or real `.env` files.

### 2.14 Key Decisions to Confirm

- Target environment: local Windows development first, then Linux/server
  deployment?
- Frontend: Vue 3 + JavaScript + Tailwind, or another existing stack?
- Telemetry rate: messages per machine per second/minute and expected machine
  count?
- Update target: is a 2–5 second dashboard refresh sufficient, or is sub-second
  delivery required?
- Alarm ownership: fixed configuration, database-managed thresholds, or
  operator-configurable thresholds?
- Data retention: how long must raw telemetry and alarm history remain available?
- Access model: single operator, team roles, or multiple sites/tenants?
- **Authentication model (critical, from review):** the current API has no
  authentication at all ("all endpoints are open on purpose in this local learning
  setup"). Dashboard write operations (alarm acknowledge) and any production
  deployment need auth. Decide the auth model **before Phase 3** (status/alarm
  backend), not as a Phase 5 hardening item, because the alarm acknowledgement
  endpoint and any write path need an authorization boundary from the start.
  Options range from simple API-key / token auth for the dashboard to a full
  JWT/OAuth role-based model; pick the minimum that covers the access model
  decision above.

Until these are confirmed, the plan assumes a single-site MVP, modest telemetry
volume, a 2–5 second initial dashboard refresh, threshold-based alarms, and no
remote machine control.

### 2.15 Definition of Done

The first usable release is complete when:
- The broker accepts only appropriately authenticated and authorized clients
  (Mosquitto mTLS + ACLs; current config at `C:/Program Files/Mosquitto/mosquitto.conf`).
- All secrets rotated from the current `.env` in the repository (Phase 0 action).
- Valid MQTT telemetry reaches PostgreSQL through the ingestion worker.
- Invalid and duplicate messages follow documented, tested policies.
- Existing API functionality and tests remain intact.
- The dashboard displays database-backed machine status, current readings, trends,
  and alarms.
- Stale data is clearly distinguished from healthy data.
- Failures are logged and observable without exposing secrets.
- A restart and recovery procedure is documented and tested.
- Deployment steps, configuration variables, and known limitations are documented.

------------------------------------------------------------------------

## 3. MQTT — Broker, TLS/mTLS, Paho Client

Source: `/f/Intern_Training/MQTT/mqtt_readme.md`.

MQTT - a lightweight, low bandwidth message queuing transport where it uses
pub/sub to deliver the messages
- publisher - the client that sends a msg to a topic
- subscriber - the client that receives a msg from a topic
- broker - a server where it sends/receives the msgs from/to the clients, nobody
  talks directly, the broker stands in the middle
- topic - the channel name the msgs travel on, pub and sub must point at the same one

### 3.1 What was done in this track in short

- Ran and secured a mosquitto broker on windows (service cmds, conf file,
  connection limits).
- Built the full TLS/mTLS certificate chain with openssl (CA, server, client) and
  wired it into mosquitto.conf.
- Wrote a paho python client (mqttdemo.py) that does the complete pub/sub round
  trip over TLS.
- Put the whole concept to work in the Machine_Sensor_API capstone.

### 3.2 Broker basics — how mosquitto was run on windows

Common cmds:
- `net start mosquitto` — starts the broker as a windows service
- `mosquitto -c mosquitto.conf` — runs it in the foreground with my conf file
- `net stop mosquitto` — stops the service (or Ctrl + c for the foreground run)
- `net stop mosquitto && net start mosquitto` — the restart, needed after every
  conf edit

Default install files — mosquitto.conf and the certs live in
`C:/Program Files/Mosquitto/`, edit the conf as admin and save, never generate it
with echo (it erases the new lines, do the changes manually).

Connection limits:
- `max_connections` — total connections allowed per listener (one port)
- `global_max_connections` — total connections allowed per broker (all listeners
  together)
- `global_max_clients` — how many devices the broker can remember

### 3.3 TLS/mTLS — the full certificate chain built with openssl

Why — plain mqtt sends everything readable on the wire, TLS encrypts it and mTLS
makes both sides prove who they are.

What each file is for:
- `ca.key` — the CA private key, created encrypted with -des3 (self-signed root)
- `ca.crt` — the CA certificate, signs both server and client certs and verifies
  both sides
- `server.key` / `server.csr` / `server.crt` — the broker identity, the CSR
  carries CN=ip_or_domain
- `client.key` / `client.csr` / `client.crt` — the client identity, the CSR
  carries CN=client1; with `use_identity_as_username=true` the CN becomes the
  username (client1)

The cmds in order:
1. `openssl genrsa -des3 -out ca.key 2048` — creates the encrypted CA key
2. `openssl req -new -x509 -out ca.crt -key ca.key -days 365` — creates the CA
   cert from that key
3. `openssl genrsa -out server.key 2048` — server key for the broker
4. `openssl req -new -out server.csr -key server.key -subj "/CN=domain"` — server
   CSR, the -subj flag skips the interactive prompts
5. `openssl x509 -req -out server.crt -in server.csr -CA ca.crt -CAkey ca.key
   -CAcreateserial -days 365 -extfile san.cnf -extensions v3_req` — signs the
   server cert with the CA; -CAcreateserial makes the .srl file openssl uses to
   track our CA; SAN comes from san.cnf
6. `openssl genrsa -out client.key 2048` — client key
7. `openssl req -new -out client.csr -key client.key -subj "/CN=client1"` — client
   CSR
8. `openssl x509 -req -out client.crt -in client.csr -CA ca.crt -CAkey ca.key
   -CAcreateserial -days 360` — signs the client cert

The -subj flag works for BOTH server and client CSRs, format
`"/C=IN/ST=State/L=City/O=Org/CN=identity"` (CN is must at least), essential for
scripting certs for multiple clients.

When the ip changes (different wifi router) — no need to regenerate everything,
just add the new ip in san.cnf and regenerate server.crt; that is why the SAN
entry saves you.

### 3.4 SAN — subject alternative name (san.cnf)

What — an extra field in the server certificate listing every ip/domain the
server accepts connections on. OpenSSL 3.x REQUIRES it — without SAN the
certificate verify simply fails.

san.cnf:
- `[v3_req]` — the section for X.509 v3 extensions
- `subjectAltName = @alt_names` — the field, pointing at the `[alt_names]` section
- `IP.1` / `IP.2` — the valid ip addresses (10.58.166.132 and 127.0.0.1)
- `DNS.1 = localhost` — the valid domain name

Rule learned — with an ip in the SAN a new ip only needs a san.cnf edit + server.crt
regen, with a domain/localhost it is the same idea, either way the CA and client
certs never change.

### 3.5 mosquitto.conf — the real TLS listener

Where — `C:/Program Files/Mosquitto/mosquitto.conf`, edited as admin, certs stored
in the same install folder.

The conf:
- `listener 8883` — the TLS port (8883 is the default for mqtt over TLS)
- `cafile` — the CA cert, verifies both server and client
- `certfile` — the server cert, proves the broker identity
- `keyfile` — the server private key for the handshake
- `require_certificate true` — forces every client to present a cert (mTLS)
- `use_identity_as_username true` — takes the CN from the client cert as the
  username
- `allow_anonymous false` — rejects clients without a valid cert
- `password_file` — NOT needed when require_certificate is on, the cert is the identity

Server side and client side must agree — the conf paths on the server, the tls_set
paths on the python client, and the same port 8883 on both, or you get an
SSLCertVerificationError. ca.crt also has to be placed in the windows Trusted Root
Certification Authorities store so the system trusts our CA.

### 3.6 Testing through the terminal

- `mosquitto_sub --cafile ca.crt --cert client.crt --key client.key -h
  10.58.166.132 -p 8883 -t test` — subscriber with the full cert trio
- `mosquitto_pub --cafile ca.crt --cert client.crt --key client.key -h
  10.58.166.132 -p 8883 -t test -m "hello there"` — publisher with the same trio
- Always send msgs through --cafile/--cert/--key, a plain connect is refused by
  the listener.

### 3.7 Python client — paho (mqttdemo.py)

Till paho 2.x the callback api defaulted to version 1, since the 2.0 release we
have to assign it ourselves to version 2 explicitly, otherwise we silently get
the legacy api.

One MQTTClient class where `__init__` sets everything up (broker, port, topic, msg,
client_id, tls certs, callbacks) so the methods stay small.

The demo choreography — on_connect() calls subscribe() and on_subscribe() calls
publish(), so all five callbacks fire in one run and the subscriber gets the ack
from the server before the publish; it is a demo flow on purpose, a real IIoT
client would subscribe to device topics and process whatever arrives.

### 3.8 The five callbacks — predefined functions we register, paho runs them automatically

- `on_connect(client, userdata, flags, reason_code, properties)` — runs whenever
  the connection happens, checks reason_code.is_failure and then subscribes
- `on_subscribe(client, userdata, mid, reason_codes, properties)` — ack from the
  server for the subscribe, then triggers the publish
- `on_publish(client, userdata, mid, reason_code, properties)` — ack that the
  publish went out
- `on_message(client, userdata, message)` — runs whenever a msg arrives, decodes
  message.payload and logs topic + payload
- `on_disconnect(client, userdata, disconnect_flags, reason_code, properties)` —
  runs when the connection drops

Every callback is wrapped in its own try/except with logging.exception so one bad
callback never kills the loop silently.

### 3.9 Loops — how the mqtt communication runs in the background

- `loop_forever()` — blocks the main thread, keeps the connection alive and
  reconnects automatically; use it when we only do pub/sub
- `loop_start()` — runs the loop on a background thread; use it when we manage
  multiple clients
- `connect()` opens the tcp connection, the loop then keeps it alive while the
  callbacks do their work

### 3.10 Return codes vs callbacks — both checks matter

- The immediate return answers "did my request go out" — subscribe() gives back
  (res, mid) and publish() gives back an object with .rc, both checked against
  mqtt.MQTT_ERR_SUCCESS.
- The callbacks answer "what did the broker actually do" — that is why
  on_connect checks reason_code.is_failure before subscribing.

### 3.11 Error types encountered

- `ConnectionRefusedError` — broker not running/wrong port
- `ssl.SSLCertVerificationError` — expired/unmatched cert or key files, or server
  side and client side don't agree
- reason_code 0 — connection success
- 1 — unacceptable protocol version, broker doesn't support our mqtt ver
- 2 — identifier rejected, the client_id is not acceptable to the broker
- 3 — server unavailable, refusing connection
- 4 — bad username/password, invalid or wrong credentials
- 5 — not authorized, not allowed
- 7 — alternative authentication required, wants a different auth method
- 8 — flow control, sending the messages too fast
- 9 — quota exceeded, too many connections
- 14 — server error, internal error
- `MQTT_ERR_NO_CONN` / `MQTT_ERR_PROTOCOL` — protocol errors on the wire
- `MQTT_ERR_SUCCESS` — the success return code for sub/pub
- `UnicodeDecodeError` — payload is not utf-8, fall back to
  `repr(message.payload)`

Enabling the paho logger (enable_logger) shows the packets in the terminal, drop
to DEBUG to watch the raw traffic.

### 3.12 Key functions used throughout

**Broker/openssl side**
- `net start/stop mosquitto` — the service control
- `openssl genrsa / req / x509` — key creation, CSR/cert signing, the whole chain
- `mosquitto_sub` / `mosquitto_pub` — terminal testing with --cafile/--cert/--key

**Paho side**
- `mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="P1")` — the client
  object, v2 callbacks asked for explicitly
- `enable_logger()` — pipes paho's own logs into our logging
- `tls_set(ca_certs=, certfile=, keyfile=)` — the client side of TLS in one setter
- `username_pw_set("user", "userpass")` — credentials without the terminal cmd dance
- `connect(host, port)` — opens the connection to the broker
- `subscribe(topic)` — returns (res, mid), checked against MQTT_ERR_SUCCESS
- `publish(topic, msg)` — returns an object with .rc, checked the same way
- `loop_forever()` — the blocking background loop with auto reconnect
- `is_connected()` — checked before disconnect() so we never disconnect twice
- `disconnect()` — clean goodbye from the broker

**Logging side**
- `logging.getLogger(__name__)` — the named logger per module
- `logging.basicConfig(level, format)` — the one-time setup in __main__
- `logger.exception("...")` — logs the message WITH the full traceback, used in
  every except block
- `logger.info("...")` — the normal flow messages

**Message handling side**
- `message.payload.decode("utf-8")` — bytes to string, with the
  UnicodeDecodeError fallback
- `message.topic` — which topic the msg came in on

### 3.13 Where it leads — Machine_Sensor_API

The capstone of this folder, a Flask + PostgreSQL API for machines and sensor
readings with bulk import of mqtt snapshot pickles; it uses the same pub/sub
thinking, honest status codes and tls habits end to end; code lives in
Machine_Sensor_API/.

### 3.14 Not used yet — next to learn

- QoS levels in practice — 0 at most once, 1 at least once, 2 exactly once; the
  demo runs on the default
- Retained messages — the broker keeps the last msg on a topic for new subscribers
- Last will and testament — the broker announces a client that died unexpectedly
- Persistent sessions — queueing msgs for a disconnected subscriber
- MQTT 5 properties/features — the properties parameter the callbacks already
  receive but never use

------------------------------------------------------------------------

## 4. Machine Sensor API (Capstone)

Source: `/f/Intern_Training/MQTT/Machine_Sensor_API/readme.md` (working copy at `./readme.md`).

Machine Sensor API: a small Flask REST api that stores and queries industrial
machine sensor readings in postgres, the capstone where mqtt thinking becomes a
full production-style service. machines --- have ---> sensor readings ("Machine A"
has TEMP 72.1 at 10:00). a client (postman, a script, an mqtt pipeline) sends
http requests, the api validates them, talks to postgres and returns json.

### 4.1 Where this is going — live IIoT monitoring platform

This api is the backend foundation for a real-time IIoT monitoring platform (see
Live_IIoT_Monitoring_Platform_Plan.md for the full plan):
- **mqtt ingestion** — machines or a telemetry simulator publish sensor readings
  to a mosquitto broker over tls/mtls (port 8883), a separate python ingestion
  worker subscribes, validates, normalizes, and persists readings through this
  same service/database layer
- **topic convention** — `factory/{site_id}/{machine_id}/telemetry` with a json
  payload carrying message_id, machine_id, sensor_tag, value, unit, measured_at
  (iso 8601 utc)
- **delivery policy** — begin with qos 1 (at-least-once), assume duplicates, use
  message_id for idempotent persistence, never claim database durability just
  because the mqtt callback fired
- **alarms** — threshold-based alarm evaluation with auditable lifecycle
  (opened/acknowledged/resolved) stored in new alarm_events table
- **dashboard** — a web dashboard polls the api (2-5s refresh initially) for
  machine status, current readings, trends, and alarms; no browser connects
  directly to mqtt, the api remains the access-control and data-contract boundary
- **deployment shape** — modular monolith: the flask api and the mqtt ingestion
  worker are separate processes that share application modules (services,
  database, validation) but do not depend on each other being alive

### 4.2 What was done in this project in short

- Built a three layer api (routes → services → database) where each layer has one
  job, the golden rule: the waiter never cooks and the kitchen never takes orders.
- Rebuilt it to production standard: waitress instead of the dev server,
  connection pool with timeouts, global json error handlers, honest status codes,
  rotating logs.
- Moved duplicate protection to ingestion with a sha-256 import ledger after
  learning that one file imported ~211 times bloated the db to ~11.8M rows for
  ~56k real readings.
- Added a shared validators module and one shared sql filter builder after a
  design review flagged the same logic copy-pasted in three places.
- Wrote 53 pytest tests that run in ~1.5s against a fake pool with no live
  database.

### 4.3 Project layout

- `.env` — stores the secrets (db credentials), never in code
- `config.py` — reads .env, validates it, fails fast at boot if something is
  missing or broken
- `app.py` — the flask app: urls, global error handlers, health check, import
  endpoint
- `wsgi.py` — one line: from app import app, the production server loads the app
  from here
- `init_db.py` — one-time setup: creates database, schema and tables, safe to
  re-run
- `database/connection.py` — the connection pool + with db.cursor() context
  managers + timeouts
- `database/schema.py` — the sql ddl: tables, indexes, the import ledger
- `utils/logger.py` — structured utc logging with automatic file rotation
- `utils/validation.py` — the shared input validators used by every view
- `routes/machine_routes.py` — receives the machine api calls
- `routes/reading_routes.py` — receives the reading api calls
  (query/create/update/delete/export/statistics)
- `services/machine_service.py` — all machine operations, the sql lives here
- `services/reading_service.py` — all reading operations + statistics + one shared
  filter builder
- `services/pickle_importer.py` — converts the pickle file to csv, then bulk-loads
  the csv into the database
- `errors.py` — shared exceptions (ValidationError etc.)
- `tests/` — the pytest suite (53 tests, no live database needed)

### 4.4 config.py — fail-fast settings

Reads .env and refuses to start if something is missing, better to fail loudly at
boot than mysteriously at request 50.

`_get_int(name, default=None)` turns an env variable into an integer and names the
exact variable in the error.

What it produces:
- `DB_HOST/PORT/NAME/USER/PASSWORD/SCHEMA` — the database credentials
- `DB_POOL_MIN=2` / `DB_POOL_MAX=10` — pool size, checked so min ≥ 1 and min ≤ max
- `DATA_DIR` — defaults to the project's data/ folder
- `IMPORT_BATCH_SIZE=5000` — rows per batch insert
- `IMPORT_FILE_NAME` — the pickle to import, resolved relative to DATA_DIR
- `DEFAULT_PAGE_SIZE=1000` — the page size and the limit cap
- `GENERIC_DB_ERROR` — the one message clients see when the database fails,
  details stay on the server

The resilience knobs, all env-tunable and validated fail-fast:
- `DB_CONNECT_TIMEOUT=5` — seconds a connection attempt may take
- `DB_STATEMENT_TIMEOUT_MS=15000` — postgres itself cancels any single query
  longer than this
- `LOG_LEVEL=INFO` — must be one of the five standard levels

### 4.5 utils/logger.py — one shared logger

Named logger "machine_sensor_api", propagate = False so records aren't printed
twice. UTC timestamps — formatter.converter = time.gmtime, log lines end in Z and
match the timestamps stored in the database. Two handlers — console (StreamHandler)
and file (RotatingFileHandler at 10 MB, five archives kept, oldest dropped). If not
logger.handlers — handlers attached only once, re-imports can't duplicate log lines.

### 4.6 database/connection.py — the pool and the three errors

The three errors:
- `DatabaseError` — unexpected database trouble, client sees 500 with a generic
  message
- `ConflictError` — a uniqueness rule was hit, client sees 409 (inherits from
  DatabaseError)
- `RelatedResourceNotFoundError` — a referenced row is missing, client sees 400
  (inherits from DatabaseError)

DatabaseManager:
- `__init__` — copies settings, sets _pool = None, connects to nothing yet
- `_ensure_pool` — creates the ThreadedConnectionPool lazily on first use
- `connection(commit=True)` — context manager: borrow → commit/rollback → return
- `cursor(commit=True)` — same guarantees but yields a cursor and closes it
- `get_connection(database=None)` — one raw connection outside the pool
- `create_database` / `create_schema` / `create_tables` — all idempotent

`db = DatabaseManager()` — the single shared instance every service imports.

### 4.7 database/schema.py — what the tables claim

- `machine_schema` — the only schema namespace
- `machines` — id SERIAL PK, machine_name UNIQUE NOT NULL, created_at TIMESTAMPTZ
- `sensor_readings` — id BIGSERIAL PK, machine_id FK with ON DELETE CASCADE,
  sensor_tag, sensor_value NUMERIC, timestamp TIMESTAMPTZ, no uniqueness beyond the
  PK
- `import_batches` — the import ledger: file_hash CHAR(64) UNIQUE (sha-256),
  file_name, records_inserted, records_skipped, imported_at
- Three indexes — (machine_id, timestamp), (sensor_tag), (timestamp)

Why readings have no uniqueness rule — we used to enforce
`(machine_id, sensor_tag, timestamp)` as unique, then asked the question that
matters: does the source guarantee that? the data happens to satisfy it but nothing
promises it always will, uniqueness is a business claim, enforce only what you can
verify, duplicate protection now lives in ingestion instead.

### 4.8 services/ — the only place sql lives

Every method follows the same skeleton: try → with db.cursor() → execute → return,
UniqueViolation becomes ConflictError (409), anything else becomes DatabaseError
(500).

**machine_service.py**
- `add_machine` — INSERT ... RETURNING, duplicate name → 409
- `get_all_machines` / `get_machine` / `update_machine` / `delete_machine` —
  turning None into 404 is the route's job, delete returns True/False from rowcount
  and the database cascades to the readings

**reading_service.py**
- `add_reading` — missing machine (ForeignKeyViolation) → 400, no duplicate check
  on purpose
- `get_readings` — builds the WHERE via `_build_reading_filters()` and always ends
  with ORDER BY timestamp, id LIMIT %s OFFSET %s
- `iter_all_readings` — generator over every matching row using a named
  (server-side) cursor with itersize inside a commit=False connection
- `get_statistics` — same filters, query is MIN/MAX/AVG, no matches → JSON nulls
- `_build_reading_filters` — the one place the standard reading filters become a
  WHERE clause plus values
- `_format_reading` — the single place a db row becomes the json shape
- `utc_z` — normalizes any aware datetime to UTC and renders iso 8601 with a Z
  suffix

**pickle_importer.py** — the two-stage pipeline: .pkl → csv → postgres. Why csv
first — it leaves a human-readable artifact next to the raw pickle, separates "parse
the weird source format" from "insert into postgres" and makes the import debuggable.
Source records look like `{"ID": ..., "ST": "TEMP", "TS": 1743157500, "VR": [72.1]}`.
Import_file resets the machine cache, checks the file exists, hashes it, refuses if
already imported, converts to csv, imports in one transaction. `_convert_to_csv`
uses pickle.load, skips broken rows, unix time → utc iso string, written to a .tmp
file first then replace()d into place. `_import_csv` uses csv.DictReader, rejects
missing columns, skips and counts broken rows, resolves the machine from the cache or
with one race-safe statement: INSERT ... ON CONFLICT (machine_name) DO UPDATE ...
RETURNING id. `_insert_batch` uses execute_values multi-row insert, one round-trip
per 5000 rows. `_record_import` catches UniqueViolation so a concurrent import rolls
back the whole transaction. `_get_file_hash` is sha-256 read in 64 KB chunks.

### 4.9 utils/validation.py — one set of rules at one door

The validators used to be private methods inside one view class; now they are plain
importable functions used by every view. They raise instead of returning error
tuples, one global handler converts any raise into a json 400.
- `validate_machine_id` — positive integer or raise
- `validate_sensor_tag` — non-empty, stripped
- `validate_timestamp` — iso 8601 in, aware datetime out, Z suffix allowed
- `machine_id_from_query` / `timestamp_from_query` — absent query param → None
- `pagination_from_query` — limit/offset parsing, raises on non-integers or
  negatives, caps limit at DEFAULT_PAGE_SIZE
- `validate_from_to_order` — rejects from later than to

### 4.10 routes/ — http handling only

Routes never write sql, services never touch http, each route follows validate →
call service → shape response.
- `MachineView` — one MethodView class for all machine urls
- `ReadingView` — one reading or a filtered list, create (requires all four fields),
  partial update, delete
- `ReadingExportView` — same filters as the list but no limit/offset, returns a
  streaming csv Response
- `ReadingStatisticsView` — same filters and the same from/to check, returns
  minimum/maximum/average

Endpoints:
- `GET /` — api index: name, status and list of all endpoints
- `GET /health` — service + db status, 200 if postgres answers, 503 if not
- `GET/POST /machines` — list / create machines
- `GET/PUT/DELETE /machines/<id>` — read / rename / delete (deletes its readings too)
- `GET/POST /readings` — query with machine_id, sensor_tag, from, to, limit, offset
  / create
- `GET/PUT/DELETE /readings/<id>` — read / update / delete one reading
- `GET /readings/statistics` — min/max/avg with the same filters
- `GET /readings/export` — download all filtered readings as a csv file
- `POST /readings/import` — convert the configured pickle to csv then bulk import it

### 4.11 app.py — the factory and the eight handlers

`create_app()` — the app is built inside a function so importing the module stays
side-effect-free. Request logging — before_request stores the start time,
after_request logs HTTP method path status duration_ms.

The eight error handlers, every possible failure becomes json:
- `handle_404` / `handle_405` / `handle_400`
- `handle_validation_error` — ValidationError → 400
- `handle_conflict_error` — ConflictError → 409
- `handle_related_resource_not_found` — RelatedResourceNotFoundError → 400
- `handle_database_error` — DatabaseError → 500 with the generic message only
- `handle_unexpected_error` — Exception → 500 generic

The __main__ block logs the startup banner and runs waitress (default port 8080).

### 4.12 Honest status codes

- 200/201 — success
- 400 — the client's mistake
- 404/405 — unknown url / wrong method, json not an html page
- 409 — duplicate machine name is a conflict, not a server error
- 503 — database down (health check)
- 500 — anything unexpected, generic message only

### 4.13 Key functions used throughout

**Config side** — load_dotenv(), os.getenv(), _get_int.

**Database side** — psycopg2.connect(), ThreadedConnectionPool,
contextmanager, connection.cursor() / cursor.execute(), cursor.rowcount,
psycopg2.extras.execute_values, psycopg2.errors.UniqueViolation /
ForeignKeyViolation / DuplicateDatabase.

**Import side** — pickle.load(), hashlib.sha256(), csv.DictReader / csv.writer,
os.replace().

**API side** — Flask / MethodView / add_url_rule, request.get_json(silent=True),
jsonify, app.errorhandler(), Response(generate(), ...).

**Logging side** — logging.getLogger(), RotatingFileHandler, time.gmtime.

### 4.14 Design decisions — the why in short

- A real server, never the dev server — waitress.
- The factory pattern — an app that imports with no side effects is an app that
  can be tested.
- Setup lives in init_db.py, not at server boot — a restart must never run ddl.
- Connection pool + context managers + timeouts — fast, visible failure with a log
  entry beats slow, silent failure every time.
- One global error handler — validation helpers raise, one handler converts.
- Uniqueness only where it is a fact — machines.machine_name UNIQUE, readings have
  no unverified rule.
- The import ledger — duplicate protection moved to ingestion where it belongs.
- Pagination everywhere — GET /readings never dumps the whole table.
- One shared validators module, one shared filter builder — the one-edit guarantee.
- The eight principles are constraints on decisions, not excuses to add layers.

### 4.15 Testing

53 pytest tests in tests/, run in ~1.5s with no live database (a fake pool in place
of the real thing):
- test_validation.py (20) — the shared validators
- test_error_handlers.py (8) — all eight error-handler branches
- test_services.py (10) — service logic + the filter builder
- test_app_flow.py (9) — the main route flows
- test_pickle_importer.py (6) — hash skip, row skipping, the csv stage

The alarms caught a real bug the first week: whitespace-only machine names slipped
through validation. The lesson that bit once: services grab db at import time, so the
test fixture must patch it in each service module. Run with: `python -m pytest
tests/ -q`.

### 4.16 Quick start

```bash
pip install -r requirements.txt
copy .env.example .env and fill in the database credentials
python init_db.py - one-time setup, safe to re-run
python app.py - the server on http://localhost:8080
curl -X POST http://localhost:8080/readings/import - load the sample data once
```

### 4.17 Not used yet — next to learn

- Blueprints — app.py still carries factory + handlers + health + import + index in
  one file.
- Formatted streaming — iter_all_readings yields raw db tuples.
- The csv stage decision — keep .pkl → csv → postgres or go direct.
- Tests for the export generator and init_db.py.
- Authentication — all endpoints are open on purpose in this local learning setup.
- MQTT ingestion worker — planned Phase 2 of the IIoT platform.
- Alarm evaluation and lifecycle — planned Phase 3.
- Dashboard — planned Phase 4.
- Authentication and authorization — queued for hardening.
- Queue-based ingestion — revisit when throughput or resilience requirements justify
  a queue.
- Telemetry retention policy — decision needed before telemetry volume grows, not
  after.

### 4.18 MQTT / IIoT platform — current status

- Mosquitto broker — running on windows as a service on port 8883 with tls/mtls
  (ca, server cert, client cert), require_certificate true, use_identity_as_username
  true, allow_anonymous false; certs built with openssl.
- Paho python client — mqttdemo.py demonstrates the full pub/sub round trip over tls
  with all five callbacks, return-code checks, and logging.exception in every error
  path.
- Ingestion worker — not yet built; planned as a separate process in the IIoT
  platform plan (Phase 2), reusing this project's services/database/validation
  layers with its own database manager instance.
- MQTT contract — not yet enforced; planned topic convention and json schema in the
  IIoT platform plan (Phase 1).
- QoS/retained/LWT/persistent sessions — studied conceptually, not yet used in
  practice.

### 4.19 Data model — planned additions for the IIoT platform

These tables are proposed in the live IIoT monitoring platform plan, not yet created:
- **machine_sensors** — machine_id + sensor_tag unique, with unit, display_name,
  warning_threshold, critical_threshold, enabled
- **telemetry_messages** — message_id unique, machine_id, received_at,
  processing_status, failure_reason
- **machine_status** — machine_id, connection_state, last_seen_at, last_reading_at,
  updated_at
- **alarm_events** — id, machine_id, sensor_tag, severity, event_type,
  observed_value, threshold_value, opened_at, acknowledged_at, resolved_at, status

### 4.20 Dashboard — planned next layer

- **Screen A** — operations overview: kpi strip, machine status table, active
  alarms, telemetry freshness indicator, last-refresh timestamp
- **Screen B** — machine detail: identity, connectivity, current values per sensor,
  time-series chart, recent alarms, historical readings table and export
- **Screen C** — alarms and events: active/acknowledged/resolved states, filters,
  acknowledgement and resolution history
- **Screen D** — historical analysis: machine/sensor selectors, time-range,
  trends and min/max/avg, csv export, clear empty/loading/stale/error states
- **Visual direction** — industrial operations-console layout: compact status cards,
  dense readable table, prominent alarm severity, restrained colors, charts with
  labeled units and time axes
- **Live update** — release 1 polls the api at 2-5s intervals; release 2 adds sse
  or websockets only if polling latency or request load becomes a measured problem

------------------------------------------------------------------------

## 5. OOP Practice

Source: `/f/Intern_Training/OOP/README.md`.

Six small Python files — one for each topic that was asked for on day one of
training: single, multiple, multilevel, hierarchical and hybrid inheritance, plus
encapsulation.

Every file runs on its own: `python Single_inheritance.py` and so on.

| File | What it shows |
|---|---|
| Single_inheritance.py | `Son` inherits from `Father` and reuses `fun1()` |
| Multiple_inheritance.py | `Son(Mother, Father)` — two parents, one child |
| MultiLevel_inheritance.py | GrandFather → Father → Son, three levels deep |
| Hierarchical_inheritance.py | Two children sharing one `Father` |
| Hybrid_inheritance.py | A mix: multiple + multilevel in one tree |
| Encapsulation.py | Public, protected (`_Code`) and private (`__battery_health`) members |

### 5.1 Why everything is wrapped in try/except

The instruction was "use an exception in every example", so each file ends with
something like:

```python
try:
    obj.fun1()
    obj.fun2()
except AttributeError as e:
    print("Error:", e)
```

In these examples the calls normally succeed — the try/except is there to show how
to guard attribute access. To actually see it fire, call a method that does not exist
(try `obj.fun3()` in Single_inheritance.py) and watch the `AttributeError` get caught
instead of crashing the script.

### 5.2 One thing worth remembering

In `Encapsulation.py` the private attribute `__battery_health` gets name-mangled to
`_Smartphone__battery_health`. It is not truly invisible — it just can't be reached by
its original name from outside. Python's "private" is a convention, not a wall, and it
took a while to accept that.

------------------------------------------------------------------------

## 6. File Handling Practice

Source: `/f/Intern_Training/File_Handling/README.md`.

Two scripts covering everyday file work in Python — opening files in different modes,
dealing with the errors that come with it, and handling structured CSV data.

### 6.1 Handle.py — text files and modes

| Mode | What it does | Error it can raise |
|---|---|---|
| `w` | write / overwrite | — |
| `x` | create-only | `FileExistsError` if the file is already there |
| `a` | append at the end | — |
| `r+` | read and write | `FileNotFoundError` if missing |

Each block sits in its own try/except, so a failure in one mode does not stop the next
one. Running it creates `note.txt` in this folder.

One thing this taught the hard way: `"x"` is the only mode whose whole job is to fail
loudly when the file already exists. It feels annoying until you need "make sure this
file is fresh" semantics.

### 6.2 Csv_Handling.py — CSV through a class

`CSVManager` wraps the four operations:
- `write_csv()` — writes a list of dicts, header taken from the first dict's keys
- `read_csv()` — returns rows as dicts
- `append_csv()` — re-reads the header first, so appends never drift out of column
  order
- `count_rows()` — quick row count

It uses `csv.DictReader` / `csv.DictWriter`, so everything is keyed by column name
instead of index positions — much harder to break by reordering columns.

The practice file is called `dataaaa.csv` — three a's, an old typo that stuck.
Renaming it is a one-line change in `CSVManager.__init__`.

### 6.3 Supporting files

- `note.txt` — output created by Handle.py
- `dataaaa.csv` — CSV written and extended by Csv_Handling.py

------------------------------------------------------------------------

## 7. PostgreSQL with Python + Flask

Source: `/f/Intern_Training/Database_Connection/README.md`.

This folder holds two stages of the same learning path:
1. setup.py — talk to PostgreSQL directly with psycopg2
2. main.py — put a Flask REST API in front of it

### 7.1 setup.py — `Postgremanager`

One class that does the full bootstrap:
- `create_db()` — connects to the built-in `postgres` database first, sets
  `autocommit`, then creates `main`
- `create_schema()` / `create_table()` — `main_schema.main_table` with employee
  columns: first_name, last_name, email (UNIQUE), phone, hire_date
- `insert_employee()`, `update_employee()`, `delete_employee()` — parameterized
  queries, commit on success, rollback on failure
- `fetch_all_employees()`

The connection handling is **reuse, not pooling**: `connect()` checks whether the
current connection is open and pointed at the right database, and only reconnects when
needed.

### 7.2 main.py — the API

Flask `MethodView` on top of `Postgremanager`:

```text
GET     /employees            list all
GET     /employees/<email>    one employee
POST    /employees            insert one or a whole batch
PUT     /employees/<email>    update
DELETE  /employees/<email>    delete
```

POST validates required fields before touching the database, and every answer uses the
same JSON shape (`status` / `message` / `data`).

### 7.3 Honest notes

- Credentials now load from a `.env` file — the same pattern the later Machine Sensor
  API uses. Originally the password was hard-coded in `setup.py`; it was moved to
  environment variables before the repo was pushed to GitHub.
- `create_db()` here folds "database already exists" into a generic except and just
  prints it. The newer API handles `DuplicateDatabase` explicitly.

------------------------------------------------------------------------

## 8. CSV → pandas → Excel

Source: `/f/Intern_Training/Conversion/README.md`.

One script, Excel.py, that takes the raw crypto OHLCV data in work.csv (ETHUSD hourly
rows) through a cleaning and enrichment pipeline and saves the result as
Work_sample_processed.xlsx.

### 8.1 The pipeline

```text
read work.csv
  ↓
parse "Date" with format "%Y-%m-%d %I-%p"  (e.g. 2020-03-13 08-PM)
  ↓
split "Symbol" into characters  →  abc becomes ['a', 'b', 'c']
  ↓
unix timestamp (ms) from the parsed date
  ↓
pull out Day / Month / Year / Hours / Minutes / seconds
  ↓
fillna(0) for missing values
  ↓
format Date back to "%Y-%m-%d %I-%p" so the output matches the input style
  ↓
write the Excel file with auto-sized columns (openpyxl)
  ↓
print every row as a dict — df.to_dict(orient="records")
```

### 8.2 Stories from this file

- **The typo incident:** an earlier version had a column called `Minues` instead of
  `Minute` — caught and called out when the zip was shared. Fixed since; the column is
  now `df["Minutes"]` (from `dt.minute`).
- `gen_data(n)` accepts a parameter it doesn't use — it just reads `work.csv`. It's a
  leftover from an earlier version that generated rows instead of reading a file.
- The date round-trip matters more than it looks: parse with the exact format string,
  then format back with the same one. If the output format doesn't match the source
  style, every downstream comparison gets confusing.

------------------------------------------------------------------------

## 9. SQL — Working Vocabulary

Source: `/f/Intern_Training/SQL_Commands/SQL_readme.md`.

### 9.1 Command categories

**DDL — Data definition language** (structure)
- create, Drop, Alter, Truncate

**DQL — Data query language** (retrieve)
- Select, From, where, Group by, Having, Distinct, order by

**DML — Data manipulation language** (manipulate)
- insert, update, delete

**DCL — Data Control language** (access control)
- GRANT, REVOKE

**TCL — Transaction control language** (execution units)
- Begin Transaction, Commit, Rollback, savepoint

### 9.2 Constraints and types used while creating tables

- Foreign key — connects a column of one table to the primary key of another table
- On delete cascade — when the parent row is deleted, child rows get deleted
  automatically
- Not null — the column must always have a value
- Default — fills a value by itself when we don't pass one
- Serial / Bigserial — auto generates id numbers for every new record
- Timestamptz — stores date-time with timezone so one instant means the same worldwide
- Index — makes filtering fast on columns we search a lot

### 9.3 Extra commands used in the api projects

- Returning — gives back the row we just inserted/updated
- On conflict do nothing — skips the row if it already exists
- On conflict do update — upsert
- Limit / Offset — pagination
- Min / Max / Avg — aggregate functions
- Execute_values — batch insert 5000 rows in one shot
- Rowcount — tells whether the update/delete actually changed any row
- Autocommit — needed for create database

### 9.4 Not used yet — next to learn

- Joins — combining two tables in one query
- Group by / Having — learned in notes, not used in real code yet
- Window functions — over, partition by, row_number
- Explain analyze — to see how postgres actually runs a query

### 9.5 Table partitioning — what was learned in the cron_jobs partitioning exercise

- Partition by range — splits one big table into smaller child tables by a value range
- Partition key rule — the primary key must include the partition column (unix_ts) or
  postgres rejects it
- Default partition — safety net child table that catches rows with no matching
  partition
- Partition pruning — postgres scans only the matching child partitions
- Drop partition — removing old data becomes drop table (instant) instead of delete in
  batches

### 9.6 Common table operations

- Create Table — create new table, define column names and datatypes
- Insert into — add elements
- Drop table — removes a table from the db
- Alter (Rename) — rename table or column, add column, modify datatype, drop column
- Truncate Table — remove all records without preserving structure
- Cloning Table — create duplicate (simple, shallow, deep)
- Temporary Table — store data temporarily during query execution
- Auto Increment — automatically generate unique values (serial in postgresql)
- Sequences — generate unique numbers automatically
- Cache management — stores sequence values in memory
- UPDATE — modify existing data
- DELETE — remove specific rows
- Duplicate rows — removed with ROW_NUMBER() or COUNT()

------------------------------------------------------------------------

## 10. Cron Jobs, Schedulers, and Table Partitioning

Source: `/f/Intern_Training/cron_jobs/cronjobs_readme.md`.

# Cron jobs
- A scheduled task where an os runs automatically at a specified time interval
- We can run programs accordingly w.r.t to the requirement

We use cron jobs to automate the tasks recursively.

Cron = the service that's always running in the background, checking "is it time to
do something?"
Cron job = one task you told it to do at a specific time.

### 10.1 The famous 5 field cron expression

```text
* * * * *
```
minutes | hours | day of month | month | day of week

This is actually an os scheduler where the os controls the schedule, but when we deal
with implementation in python we usually use a long running python scheduler.

Cron schedules the cmds. We can execute in three ways:
- With linux server using crontab -e with that 5 field expression
- In python we usually use that interpreter
- In windows we usually use task scheduler to trigger the scripts using python exe

In production use cases the cron files usually revolve around: entry point, error
handling, logging, using environment variables, database clean up, clear exit behavior.

Cron jobs can be run using bash, python, perl, php and any binary scripts.

### 10.2 Schedule

It's an event where we can run the task automatically in time intervals where it is more
like the python being implement the cron jobs (an in-process scheduler, while real cron
on linux runs the scripts through crontab).

### 10.3 APScheduler

A light weight advanced python in-process task scheduling where we can use cron like
capabilities. It supports mainly three triggers:
- Datetrigger — one-time interval execution triggers
- IntervalTrigger — fixed time interval triggers
- CronTrigger — complex scheduling based on cron expressions

Two types of schedulers:
- BackgroundScheduler — runs in the background and allows the main application to
  continue execution; ideal for long running applications
- BlockingScheduler — blocks the main thread until the scheduler is shut down; best for
  standalone scripts where the scheduler is the primary process.

### 10.4 Project setup

Create table with columns: ID, Unix_ts. Two cron jobs:
1. Insert data current unix timestamp into table every 1 minute.
2. Create a partition for values in the last 10 minutes and it should run every 10
   mins.

Project structure:
- `cron_jobs/` — root directory
- `logs/` — storing the log details
- `config.py` — configuring the credentials so that it can access the database user
  details
- `db.py` — import the config file for credential details of database, and gives
  get_connection(database=None) which connects to the default postgres db when needed
- `logging_config.py` — importing pathlib for making the actual path as parent and
  create log file to it; log rotation done by RotatingFileHandler (10 MB, 10 backups)
- `scheduler.py` — the actual cron jobs process; imports connection from db, schema/
  table name and ten minutes gap from config, imports logging_config
  - `insert_current_timestamp()` — inserts the timestamp with 1 minute difference,
    calls create_partition() just before inserting
  - `create_partition()` — creates the partition for the timestamp passed to it on the
    basis of 10 minutes gap, named timestamp_data_<window_start>, IF NOT EXISTS makes
    re-runs idempotent
  - `run_timestamp_job()` — entry point of insert_current_timestamp()
  - `run_partition_job()` — entry point of create_partition()
  - `run_scheduler()` — where the actual cron jobs done
- `setup.py` — setting up database
  - `create_database()` — create a db with autocommit while connecting to the default db
  - `create_schema()` — creating a schema and being verified
  - `create_table()` — creating a table with id and unix_ts and do partitions based on
    timestamp, plus a _default partition as the safety net
  - `initialize_database()` — entry point for those three functions

### 10.5 Keep built-in functions that are being used

- Primary Key — for look up purpose w.r.t the id/unix_ts
- load_dotenv() — loading of db credentials
- psycopg2.connect() — connecting to the db with the env variables
- RotatingFileHandler — log rotation
- int(time.time()) — converting float unix_timestamp to integer
- connection.cursor() — start the sql command
- cursor.execute() — execute db commands
- logging.getLogger() — logger name shown in terminal
- schedule.every(1).minute.do() — assign automated tasks every 1 minute
- schedule.every(10).minutes.do() — assign automated tasks every 10 minutes
- schedule.run_pending() — check pending jobs
- BlockingScheduler — for one time continuous runnable scripts
- scheduler.add_job(run_timestamp_job, "cron", minute="*/1", id="insert_timestamp")

### 10.6 APScheduler vs Schedule

| Feature | APScheduler | Schedule |
|---|---|---|
| Complexity | Feature-rich, production-grade | Lightweight, simple API |
| Triggers | Cron, interval, date, calendar | Interval-based only |
| Persistence | Yes (SQL, MongoDB, Redis, SQLite) | No — jobs lost on restart |
| Concurrency | Thread/process/async executors | Single-threaded by default |
| Best for | Production apps, web frameworks, complex schedules | Quick scripts, prototypes, simple recurring tasks |

------------------------------------------------------------------------

## 11. Rotating JSON Logging — Code Explanation

Source: `/f/Intern_Training/log_rotation/code_explanation.md`.

What the file does in one sentence: format every log record as **one-line JSON**,
write it to a **rotating file chain** (`app.log` → `app.log.1` → … → `app.log.10`)
**and** to the **console**, using unix-epoch timestamps.

### 11.1 Imports

```python
import json        # for the output format
import logging     # standard logging frameworks
import pathlib     # build root directories
import sys         # standard streams (stdin, stdout, stderr)
from logging.handlers import RotatingFileHandler  # size-based rotation triggers
```

### 11.2 Path constants

```python
BASE_DIR = pathlib.Path(__file__).resolve().parent   # current file is root directory
LOG_DIR = BASE_DIR / "logs"                          # logs folder
LOG_DIR.mkdir(exist_ok=True)                         # create if not exists
LOG_FILE = LOG_DIR / "app.log"                       # live log file
```

### 11.3 JsonFormatter

```python
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": record.created,     # unix timestamp
            "level": record.levelname,       # info/warning/error
            "logger": record.name,           # logger name
            "message": record.getMessage(),  # raw text
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)
```

### 11.4 configure_logging

```python
def configure_logging():
    logger = logging.getLogger("application")
    logger.setLevel(logging.INFO)
    if logger.handlers:
        return logger
    formatter = JsonFormatter()
    file_handler = RotatingFileHandler(
        filename=LOG_FILE,
        maxBytes=2 * 1024,
        backupCount=10,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.propagate = False
    return logger
```

### 11.5 Module-level script

```python
logger = configure_logging()  
logger.info("Application started")
logger.info("Processing request")
logger.warning("Something requires attention")
for i in range(100):
    logger.info("Testing centralized logging - message number %s", i)
```

------------------------------------------------------------------------

## 12. Regular Expressions

Source: `/f/Intern_Training/RegEx/regex_readme.md`.

Regular Expression — a sequence of characters that defines a specific search pattern.
Used for search, match, validate, extract, replace text based on defined pattern.

Common uses:
- Input validation — matching input against a pattern
- Extract information — using groups to pull specific parts of unstructured data
- Log processing — parse structured/semi-structured log lines into fields using named
  groups
- API input validation — same as input validation but on request body before processing
- Data cleaning — use re.sub() to replace unwanted patterns with a clean version

### 12.1 Pattern elements

- RegEx Pattern: the sequence of characters that defines what we want to find/match/
  validate/extract/replace
- RegEx Engine: interprets a regex pattern and applies it to input text
- Literal characters: represent themselves
- Meta characters:
  - `\` — escape character
  - `[]` — character class
  - `^` — start of string
  - `$` — end of string
  - `.` — any character except newline
  - `?` — zero/one occurrence
  - `*` — zero/more occurrence
  - `+` — one/more occurrence
  - `{}` — specifies exact range
  - `()` — groups

### 12.2 Anchors

Specify a position in the text rather than matching an actual character:
- `^` — matches beginning of string
- `$` — matches end of string
- `\A` — absolute start of string
- `\Z` / `\z` — absolute end of string

### 12.3 Special sequences

- `\d` — digit
- `\D` — non-digit
- `\w` — word character
- `\W` — non-word character
- `\s` — whitespace (tab, space, newline)
- `\S` — non-whitespace
- `\b` — word boundary
- `\B` — non-word boundary

### 12.4 Common regex functions

- `re.search()` — find first match anywhere
- `re.match()` — match only from beginning
- `re.fullmatch()` — matches entire string
- `re.findall()` — find all matches
- `re.sub()` — replace text
- `re.split()` — split based on pattern

### 12.5 Matcher functions

- `match_five_digit()` — pattern `(?<!\d)\d{5}(?!\d)` — exact 5 digits
- `match_only_lowercase()` — pattern `[a-z]`
- `match_only_uppercase()` — pattern `[A-Z]`
- `match_letters_and_numbers()` — pattern `([a-zA-Z]+)(\d+)` with grouping
- `match_a_string_starts_with_A()` — pattern `\bA\w*`
- `match_a_string_ends_with_Z()` — pattern `\w*Z\b`
- `match_a_string_contains_only_digits()` — pattern `\d+`
- `match_a_string_contains_no_digits()` — pattern `\D+`

Note: `match_letter_and_numbers()` in the implementation uses two separate findall
calls:
```python
def match_letter_and_numbers(result4):
    letters = re.findall(r"[A-Za-z]", result4)
    numbers = re.findall(r"\d+", result4)
    if not letters and not numbers:
        return None
    return {"letters": letters, "numbers": ",".join(numbers)}
```

### 12.6 Important notes

- `^abc != [^abc]` — in first case it is an anchor, in second case it is negation
- Know which use cases and scenarios to use search/match/fullmatch/findall/sub/split
- Regex is mainly used for validation purpose in day-to-day scenarios

------------------------------------------------------------------------

## 13. Machine Log Monitor (RegEx)

Source: `/f/Intern_Training/RegEx/Machine_Log_Monitor/README.md`.

# Machine Log Monitor — End-to-End Flow

This document describes exactly what happens when `scheduler.py` is executed, line by
line, from process startup to termination, including the supporting functions it calls.

### 13.1 What scheduler.py does

scheduler.py wires everything together using **APScheduler's `BlockingScheduler`**. It
schedules one recurring job that runs once per minute and stops the scheduler when the
log has been fully consumed.

#### main()

1. Calls `configure_logging()` — written at module import time in logging_config.py,
   so logging is configured **before** the scheduler starts.
2. Calls `create_scheduler()`, which returns a configured but **not yet running**
   `BlockingScheduler`.
3. Logs `"Machine log monitoring started (interval: 1 minute)"`.
4. Calls `scheduler.start()` — this blocks the process and starts the event loop.

#### create_scheduler()

1. Creates a `BlockingScheduler`.
2. Defines `run_monitoring()`, the job function:
   - Calls `monitor_machine_logs()` and captures the boolean it returns.
   - If the return value is `False` (`has_more_lines` is false), logs
     `"Machine log processing complete."` and shuts the scheduler down with
     `scheduler.shutdown(wait=False)`.
   - Otherwise returns `True` and the scheduler waits for the next interval.
3. Registers the job:
   - `trigger="interval"`, `minutes=1`
   - `id="machine_log_monitor"`, `replace_existing=True`
   - `max_instances=1`
   - `coalesce=True`
4. Returns the scheduler.

**Important:** the job does **not** run forever. It stops after the log's last line has
been read. The `is_last_line` flag returned by the reader drives this behavior.

### 13.2 One scheduled run — monitor_machine_logs()

jobs.py holds **one shared module-level reader**: `reader = MachineLogReader()`. This
reader object keeps the file position between scheduled runs. Each job invocation
processes **one line** from the log:

1. `reader.read_next_line()`:
   - Opens the log if not already open.
   - Saves the current file position (`tell()`), reads the next line, then peeks one
     character further ahead to determine whether another line follows.
   - Returns `(line_number, line, is_last_line)` on success.
   - Returns `None` when the file has reached EOF.
2. If the result is `None`, the reader is closed and `False` is returned.
3. If a line was read:
   - `parse_machine_log(line)` tries to extract the fields.
   - If parsing fails on a non-blank line → warning log, line skipped.
   - If the line is blank → info log, line skipped.
   - If parsed successfully and `level == "ERROR"`:
     - `store_errors([parsed])` writes the row into the DB.
     - `generate_report()` rebuilds the CSV from the DB.
   - If parsed successfully but `level != "ERROR"` → info log, line skipped.
4. A `try/except` wraps parsing/storing; on any exception the reader seeks back to the
   last line (`retry_last_line()`) so the line is attempted again on the next run.
5. After handling, if `is_last_line` is true, the reader is closed and `False` is
   returned. Otherwise `True` is returned.

### 13.3 Reading the log — log_reader.py

`MachineLogReader` is the low-level line reader.
- `__init__(file_path=MACHINE_LOG_FILE)` — defaults to `logs/machine.log` from config.py.
- `open()` — opens the file with UTF-8 encoding if not open yet.
- `read_next_line()` — the core:
  - `self.file.tell()` → `line_position`
  - `readline()` reads the line; if nothing returned, EOF → returns `None`
  - `line_number` incremented, `last_line_position` saved
  - A second `readline()` peeks ahead
  - `seek(next_line_position)` restores position
  - Returns `(line_number, line_without_newline, is_last_line)`
- `retry_last_line()` — seeks back to `last_line_position`, decrements line counter
- `close()` — closes the file and clears position

The `tell()`/`seek()` peek pattern is what tells the caller whether it has reached the
very last line of the file.

### 13.4 Parsing the log — log_parser.py

`parse_machine_log(line)` validates and extracts fields from one line.
- `LOG_PATTERN` is a compiled regex with named groups: timestamp, level, machine_id,
  message
- `fullmatch` is used, so the **entire** line must match
- The timestamp is parsed with `strptime` and forced to UTC via
  `.replace(tzinfo=timezone.utc)`; a bad date makes the function return `None`
- Returns a dict with timestamp, unix_timestamp, machine_id, level, error_message, or
  `None` for blank/malformed/invalid-date lines

### 13.5 Storing errors — machine_insert.py

`store_errors(errors)` inserts parsed ERROR entries into the database.
- Opens a connection via `db.get_connection()`.
- For each parsed error, executes `INSERT ... ON CONFLICT (machine_id, timestamp,
  error_message) DO NOTHING` into `{DB_SCHEMA}.machine_errors`.
- `cursor.rowcount == 1` → counted as newly inserted; otherwise counted as duplicate.
- `connection.commit()` on success; `connection.rollback()` on failure.
- `connection.close()` in finally.

The `UNIQUE` constraint `(machine_id, timestamp, error_message)` prevents duplicate
insertion.

### 13.6 Generating the report — report.py

`generate_report()` rebuilds the CSV file after each error is stored.
- Runs `SELECT machine_id, timestamp, error_message FROM {DB_SCHEMA}.machine_errors
  ORDER BY timestamp;`
- Creates `reports/` if missing.
- Writes `reports/machine_error_report.csv` with header `["Machine ID", "Timestamp",
  "Error Message"]` and one row per DB record.
- On failure, logs and re-raises; closes connection in finally.

The report is **not** regenerated on every job run — only when an ERROR entry is
actually processed.

### 13.7 Database layer — db.py

`get_connection(database=None)` opens a psycopg2 connection from settings in `.env`
(DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD). An optional database argument is
used during setup.

### 13.8 Database setup — setup_db.py

Run **once** before scheduler.py:
1. `create_database()` — connects to `postgres`, creates `{DB_NAME}` with autocommit
2. `create_schema()` — `CREATE SCHEMA IF NOT EXISTS {DB_SCHEMA}`
3. `create_table()` — `CREATE TABLE IF NOT EXISTS {DB_SCHEMA}.machine_errors` with
   columns id, machine_id, timestamp, unix_timestamp, error_message, plus the UNIQUE
   constraint

### 13.9 End-to-end run

1. `configure_logging()` runs; messages go to terminal and to `logs/app.log`
   (rotating at 10 MB, 10 backups).
2. `main()` builds and shows the "started" log line, then blocks on `scheduler.start()`.
3. **Every ~60 seconds**: `run_monitoring()` → `monitor_machine_logs()`:
   - Reads **one** line from `logs/machine.log`.
   - Parses it. Only ERROR lines are stored.
   - Stores errors into DB and rewrites CSV report.
   - If more lines, returns True; scheduler waits for next minute.
   - If last line, reader closes and returns False; job logs "Machine log processing
     complete." and shuts scheduler down.

Example console output:
```text
INFO  | 2026-10-09 12:00:00 | Machine log monitoring started (interval: 1 minute)
INFO  | 2026-10-09 12:00:00 | Saved ERROR log entries: 1; duplicates skipped: 0
INFO  | 2026-10-09 12:00:00 | Report generated | Records=1
INFO  | 2026-10-09 12:00:00 | Machine log processing complete.
```

### 13.10 Key design notes / gotchas

1. **One-shot per scheduler lifetime.** The scheduler does **not** tail the log forever.
   Once the reader reaches the last line, it closes the file and exits.
2. **Reader state persists across runs.** Because jobs.py creates one MachineLogReader at
   module level, the file position is preserved.
3. **Retry behavior.** If storing or parsing fails, retry_last_line() puts the reader
   back on that line.
4. **Duplicates are safe.** The UNIQUE constraint plus ON CONFLICT DO NOTHING guarantees
   an identical error is never inserted twice.
5. **Report regeneration is error-driven.** The CSV is rewritten only when an ERROR line
   is processed.
6. **Timestamps are UTC.** The parser marks every parsed timestamp as UTC.
7. **Setup must happen first.** setup_db.py creates the database, schema, and table
   before scheduler.py can store anything.

### 13.11 Setup & run

```bash
pip install -r requirements.txt
python setup_db.py
python scheduler.py
```

Project files involved:

| File | Role |
|---|---|
| scheduler.py | APScheduler entry; schedules & stops the job |
| jobs.py | One-line-per-run processing; owns the shared reader |
| log_reader.py | Low-level tell()/seek() line reader |
| log_parser.py | Regex + timestamp parsing |
| machine_insert.py | Error → DB insert with duplicate guard |
| report.py | DB → CSV report |
| db.py | PostgreSQL connection |
| config.py | Paths + .env settings |
| logging_config.py | Terminal + rotating file logger |
| setup_db.py | One-time DB scaffolding |

### 13.12 Future changes — if you switch to live / high-frequency logs

The current design assumes **static, bounded sample data**. If you later switch to live
or bursty logs, apply these changes exactly.

#### 1. Per-run DB connection → batch insert in one transaction

**File:** machine_insert.py. Replace the per-row cursor.execute() loop with an
executemany() call, and move connection.commit() **outside** the with block.

#### 2. One line per run → buffer lines between runs

**File:** jobs.py. Add an in-memory buffer and a drain loop so a run consumes every
buffered line before reading new file content.

#### 3. Also consider for live/bursty data

| Concern | Fix |
|---|---|
| Many small DB writes | Batch INSERT with executemany() per tick |
| High volume + low latency | Keep a shared DB connection across ticks, or use a connection pool |
| Persistent restart safety | Save reader's last_line_position to a state file |

#### 4. When to apply these

Apply these changes only when the requirement changes from static sample data to live/
bursty logs. For the current data, the design is already correct and optimal.

------------------------------------------------------------------------

## 14. Machine Log Monitor v3

Source: `/f/Intern_Training/RegEx/Machine_Log_Monitor_v3/README.md`.

This is the improved v3 version of the Machine Log Monitor end-to-end flow (see §13 for
the v1 version). The v3 README documents the same scheduler-driven log processing but
with a few improvements: the store_errors function accepts a list of parsed ERROR dicts
(a single dict is also accepted) and inserts them in one transaction, returning
(inserted, duplicates).

Key v3 improvements over v1:
- `store_errors(errors)` takes a **list** of parsed ERROR dicts and inserts them in one
  transaction (v1 called it per-element).
- The README uses PowerShell-style setup commands.
- `.env` holds credentials and is git-ignored; `config.py` refuses to start if any
  setting is missing.
- The project file table now includes `app.py` — Flask API (`/live/*`) + serves the
  `client/` dashboard.

The v3 README otherwise duplicates the v1 flow description (scheduler.py, jobs.py,
log_reader.py, log_parser.py, machine_insert.py, report.py, db.py, config.py,
logging_config.py, setup_db.py) and the same future-changes section for live/bursty
data. The v1 `alternatives.md` (approach comparison) is the canonical version; the v3
alternatives.md is an exact duplicate and was not carried into this consolidation.

------------------------------------------------------------------------

## 15. Linux and Unix Basics

Source: `/f/Intern_Training/Linux/README.md` + `/f/Intern_Training/Linux/Learning_linux.md`.

# Linux and Unix Basics

This folder contains command-line learning notes.

### 15.1 What was practiced

Commands covered:
```text
pwd   ls     cd     mkdir   touch
cp    mv     rm     cat     less
head  tail   grep   find    wc
sort  uniq   explorer.exe .
```

### 15.2 Why this matters for application-side IIoT

Linux is common for servers, gateways, containers, and edge systems. The goal is not to
master system administration yet, but to be comfortable moving around the file system,
reading logs/files, finding files, and running commands.

### 15.3 Learning flow

```text
Navigate
  ↓
Create / copy / move
  ↓
Read files
  ↓
Search text/files
  ↓
Inspect command-line output
```

### 15.4 Commands of Linux

- pwd — shows the directory we are in
- ls — list of files in directory
- cd — change directory
- mkdir — create directories
- touch — create a new file
- cp — copy the file
- mv — move files
- rm — delete the file
- cat — display the file
- less — read the file
- head — display first lines
- tail — display last lines
- grep — search text
- find — find files
- wc — count lines/words
- sort — sort data
- uniq — remove duplicates

### 15.5 explorer.exe .

Helps to open the file location in explorer.

### 15.6 Dealing with computer through a terminal

- Command prompt — built-in tool to communicate with our computer
- PowerShell — more advanced cmd-line tool for automation and scripting
- Windows — open cmd prompt, powershell within a single window

We use them for troubleshooting, performing tasks quickly, accessing advanced tools,
system recovery. Activate cmd prompt via run dialog box. For changes, open terminal in
admin mode.

- `powercfg/batteryreport` — check battery health
- `sfc/scannow` — scan windows and find errors
- `DISM/RestoreHealth` — repairs windows system image

### 15.7 Unix

A multi-user os where it allows multiple users to work on the same machine and run
different programs at once.

------------------------------------------------------------------------

## 16. High-Level IIoT Pipeline Sketch

Source: `/f/Intern_Training/.md` (root dot-file).

This is a high-level sketch of the IIoT pipeline, organized by layer:

**Communication layer**
Python consumers, validation, business rules, event detection.

**PostgreSQL, time-series storage, built RESTful APIs.**

**Live dashboard, alarms, reports and analytics using graphs.**

Layer responsibilities:
- **Communication** — configure MQTT clients, topics, QoS, authentication, reconnect
  logics
- **Data Ingestion** — consume telemetry and validate message formats
- **Data Processing** — find abnormal events
- **Database** — design schemas, store readings, handle queries
- **Backend** — build APIs, authentication, alarm services, logics
- **Frontend** — develop dashboards, charts, status view
- **Operations** — logging, monitoring, testing, deployment, security, recovery

A practical sequence:
1. **MQTT communication** — receive real/simulated machine telemetry
2. **Python ingestion service** — validate and process incoming messages
3. **PostgreSQL** — persist sensor readings and machine events
4. **Backend API** — provides machine status, historical readings and alarm data
5. **Live dashboard** — display machine health, trends, active alarms and downtime
6. **Production hardening** — add authentication, reconnect handling

------------------------------------------------------------------------

## 17. Files Removed During Consolidation

The following files were identified as unwanted, repeated, or unused and were excluded
from this consolidated document (and should be removed from the repository):

### 17.1 Dashboard / web application plans (excluded by request)

| File | Reason |
|---|---|
| `RegEx/Machine_Log_Monitor/dashboard_build_plan.md` | Live monitoring dashboard build plan — web application planning content; also duplicated by v3 version |
| `RegEx/Machine_Log_Monitor_v3/dashboard_build_plan.md` | Same dashboard build plan — excluded |
| `mqtt_dashboard_changes/dashboard/README.md` | Vue 3 + TypeScript dashboard with SSE — web application plan; excluded |

### 17.2 Duplicate / near-duplicate content

| File | Reason |
|---|---|
| `RegEx/Machine_Log_Monitor_v3/alternatives.md` | Exact duplicate of `Machine_Log_Monitor/alternatives.md` — v1 kept |
| `RegEx/Machine_Log_Monitor_v3/README.md` | Near-duplicate of `Machine_Log_Monitor/README.md`; v3 improvements folded into §14 of this consolidation, v3 file removed |

### 17.3 Non-content files (not training material)

| File | Reason |
|---|---|
| `.venv/Lib/site-packages/**/*.md` | Virtualenv package licenses — not training content |
| `Final_zip/**/*.md` | Distribution copy duplicates of live files — not source content |

### 17.4 Already consolidated

| File | Reason |
|---|---|
| `RegEx/regex_readme.md` | Merged into §12 of this consolidation |
| `RegEx/Machine_Log_Monitor/README.md` | Merged into §13 of this consolidation |
| `RegEx/Machine_Log_Monitor/alternatives.md` | Merged into §13 (future changes) and kept as canonical alternatives reference |
| `RegEx/Machine_Log_Monitor_v3/README.md` | Merged into §14 of this consolidation |
| `OOP/README.md` | Merged into §5 |
| `File_Handling/README.md` | Merged into §6 |
| `Database_Connection/README.md` | Merged into §7 |
| `Conversion/README.md` | Merged into §8 |
| `SQL_Commands/SQL_readme.md` | Merged into §9 |
| `cron_jobs/cronjobs_readme.md` | Merged into §10 |
| `log_rotation/code_explanation.md` | Merged into §11 |
| `Linux/README.md` | Merged into §15 |
| `Linux/Learning_linux.md` | Merged into §15 |
| `.md` (root) | Merged into §16 |
| `MQTT/mqtt_readme.md` | Merged into §3 |
| `MQTT/Machine_Sensor_API/readme.md` | Merged into §4 |
| `Live_IIoT_Monitoring_Platform_Plan.md` | Merged into §2 |
| `TRAINING_DOCUMENTATION.md` | Merged into §1 |
