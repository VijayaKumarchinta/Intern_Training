# Machine Sensor API (Capstone) Concepts — Intern Training

**Source:** `MQTT/Machine_Sensor_API/readme.md`

> A small Flask REST API that stores and queries industrial machine sensor readings in PostgreSQL. The capstone where MQTT thinking becomes a full production-style service.

---

## 1. Architecture (layered)

**What:** The full layered stack.

```
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

**Pros:**
- Separation of concerns: each layer has one job.
- "The waiter never cooks and the kitchen never takes orders."

**Cons/drawbacks:**
- Every layer adds indirection; boundaries must be respected.
- If a layer does the wrong thing (e.g., a route handling SQL), the whole design breaks.

**Errors encountered & causes:**
- N/A at this conceptual stage (applied in the capstone).

**Use cases:**
- Any REST API with a clear layering: routes → services → database.

**Usage:**
- HTTP → factory → validation → routes → services → pool → PostgreSQL.

---

## 2. config.py — fail-fast settings

**What:** Reads `.env` and refuses to start if something is missing.

`_get_int(name, default=None)` turns an env variable into an integer and names the exact variable in the error.

**Produces:**
- `DB_HOST/PORT/NAME/USER/PASSWORD/SCHEMA` — the database credentials.
- `DB_POOL_MIN=2` / `DB_POOL_MAX=10` — pool size, checked so min ≥ 1 and min ≤ max.
- `DATA_DIR` — defaults to the project's data/ folder.
- `IMPORT_BATCH_SIZE=5000` — rows per batch insert.
- `IMPORT_FILE_NAME` — the pickle to import, resolved relative to DATA_DIR.
- `DEFAULT_PAGE_SIZE=1000` — the page size and the limit cap.
- `GENERIC_DB_ERROR` — the one message clients see when the database fails, details stay on the server.

**The resilience knobs, all env-tunable and validated fail-fast:**
- `DB_CONNECT_TIMEOUT=5` — seconds a connection attempt may take.
- `DB_STATEMENT_TIMEOUT_MS=15000` — Postgres itself cancels any single query longer than this.
- `LOG_LEVEL=INFO` — must be one of the five standard levels.

**Pros:**
- Fail-fast boot prevents mystery 500s later.
- All knobs env-tunable.

**Cons/drawbacks:**
- `.env` must exist; no defaults for secrets.

**Errors encountered & causes:**
- N/A here (applied in capstone).

**Use cases:**
- Any service with secrets and config; fail-fast, env-based configuration.

**Usage:**
- Load `.env`, read secrets with `os.getenv`, validate at boot, fail loudly if anything is missing.

---

## 3. utils/logger.py — one shared logger

**What:** Structured UTC logging with automatic file rotation.

- Named logger `"machine_sensor_api"`, `propagate = False` so records aren't printed twice.
- UTC timestamps — `formatter.converter = time.gmtime`, log lines end in Z and match the timestamps stored in the database.
- Two handlers — console (`StreamHandler`) and file (`RotatingFileHandler` at 10 MB, five archives kept, oldest dropped).
- `if not logger.handlers` — handlers attached only once; re-imports can't duplicate log lines.

**Pros:**
- Structured, UTC logs for both humans and machines.
- Automatic file rotation prevents unbounded log growth.

**Cons/drawbacks:**
- One logger per app — multiple apps must each configure their own.

**Errors encountered & causes:**
- Duplicate log lines on re-import → guarded with `if logger.handlers: return`.

**Use cases:**
- Any service needing structured UTC logging + rotation.

**Usage:**
- Create a named logger, set `propagate=False`, add a RotatingFileHandler (10MB × 5) + StreamHandler, attach once.

---

## 4. database/connection.py — the pool and the three errors

**What:** The three errors:

- `DatabaseError` — unexpected database trouble, client sees 500 with a generic message.
- `ConflictError` — a uniqueness rule was hit, client sees 409 (inherits from `DatabaseError`).
- `RelatedResourceNotFoundError` — a referenced row is missing, client sees 400 (inherits from `DatabaseError`).

**DatabaseManager:**
- `__init__` — copies settings, sets `_pool = None`, connects to nothing yet.
- `_ensure_pool` — creates the `ThreadedConnectionPool` lazily on first use.
- `connection(commit=True)` — context manager: borrow → commit/rollback → return.
- `cursor(commit=True)` — same guarantees but yields a cursor and closes it.
- `get_connection(database=None)` — one raw connection outside the pool.
- `create_database` / `create_schema` / `create_tables` — all idempotent.

`db = DatabaseManager()` — the single shared instance every service imports.

**Pros:**
- Pooled connections survive traffic.
- Context managers always return the connection.
- Three typed errors map cleanly to HTTP codes.

**Cons/drawbacks:**
- `db = DatabaseManager()` is a module-level singleton — the later capstone rebuild replaces this with a per-worker instance.

**Errors encountered & causes:**
- Hung query could hold a pooled worker forever (no timeouts) → `connect_timeout=5` + `statement_timeout=15000` (env-tunable), verified live via `SHOW statement_timeout`.

**Use cases:**
- Multi-threaded web apps; connection pooling + timeouts.

**Usage:**
```python
with db.connection() as conn:
    with db.cursor() as cur:
        cur.execute("SELECT ...")
```

---

## 5. database/schema.py — what the tables claim

**What:**
- `machine_schema` — the only schema namespace.
- `machines` — id SERIAL PK, machine_name UNIQUE NOT NULL, created_at TIMESTAMPTZ.
- `sensor_readings` — id BIGSERIAL PK, machine_id FK with ON DELETE CASCADE, sensor_tag, sensor_value NUMERIC, timestamp TIMESTAMPTZ, no uniqueness beyond the PK.
- `import_batches` — the import ledger: file_hash CHAR(64) UNIQUE (sha-256), file_name, records_inserted, records_skipped, imported_at.
- Three indexes — (machine_id, timestamp), (sensor_tag), (timestamp).

**Why readings have no uniqueness rule:**
- We used to enforce `(machine_id, sensor_tag, timestamp)` as unique, then asked the question that matters: does the source guarantee that? The data happens to satisfy it but nothing promises it always will. Uniqueness is a business claim; enforce only what you can verify. Duplicate protection now lives in ingestion.

**Pros:**
- FK ON DELETE CASCADE keeps referential integrity.
- CONSTRAINT UNIQUE + ledger give provable dedupe.
- Indexes speed lookups.

**Cons/drawbacks:**
- No uniqueness on readings → duplicates possible by design.

**Errors encountered & causes:**
- Uniqueness asserted on an unverified business claim → multiplied one file ~211× into 11.8M rows → moved to ingestion ledger.

**Use cases:**
- Any schema where you need both relational integrity and provable dedupe.

**Usage:**
- Machines: PRIMARY KEY + UNIQUE. Readings: composite PK only; dedupe in ingestion.

---

## 6. services/ — the only place SQL lives

Every method follows the same skeleton: try → with `db.cursor()` → execute → return; UniqueViolation becomes ConflictError (409), anything else becomes DatabaseError (500).

### 6.1 machine_service.py

| Method | What it does |
|---|---|
| `add_machine` | INSERT ... RETURNING; duplicate name → 409 |
| `get_all_machines` | list all machines |
| `get_machine` | one machine |
| `update_machine` | rename |
| `delete_machine` | delete; returns True/False from rowcount; DB cascades to readings |

### 6.2 reading_service.py

| Method | What it does |
|---|---|
| `add_reading` | missing machine (ForeignKeyViolation) → 400, no duplicate check on purpose |
| `get_readings` | builds WHERE via `_build_reading_filters()` and always ends with ORDER BY timestamp, id LIMIT %s OFFSET %s |
| `iter_all_readings` | generator over every matching row using a named (server-side) cursor with itersize inside a commit=False connection |
| `get_statistics` | same filters; query is MIN/MAX/AVG; no matches → JSON nulls |
| `_build_reading_filters` | the one place the standard reading filters become a WHERE clause plus values |
| `_format_reading` | the single place a DB row becomes the JSON shape |
| `utc_z` | normalizes any aware datetime to UTC and renders ISO 8601 with a Z suffix |

### 6.3 pickle_importer.py — the two-stage pipeline: .pkl → csv → postgres

**Why CSV first** — it leaves a human-readable artifact next to the raw pickle, separates "parse the weird source format" from "insert into PostgreSQL", and makes the import debuggable.

**Source records look like:**
```json
{"ID": ..., "ST": "TEMP", "TS": 1743157500, "VR": [72.1]}
```

**Import_file** resets the machine cache, checks the file exists, hashes it, refuses if already imported, converts to CSV, imports in one transaction.

**Methods:**
- `_convert_to_csv` — uses `pickle.load`, skips broken rows, unix time → UTC ISO string, written to a `.tmp` file first then `replace()`s into place.
- `_import_csv` — uses `csv.DictReader`, rejects missing columns, skips and counts broken rows, resolves the machine from the cache or with one race-safe statement: `INSERT ... ON CONFLICT (machine_name) DO UPDATE ... RETURNING id`.
- `_insert_batch` — uses `execute_values` multi-row insert, one round-trip per 5000 rows.
- `_record_import` — catches UniqueViolation so a concurrent import rolls back the whole transaction.
- `_get_file_hash` — sha-256 read in 64 KB chunks.

**Pros:**
- Two-stage pipeline = debuggable, human-readable artifact.
- Race-safe machine resolution.
- Hash ledger = duplicate protection.

**Cons/drawbacks:**
- Pickle → CSV stage is still a decision under review (could be direct).
- One bad VR value previously aborted the whole file → now per-row validation.

**Errors encountered & causes:**
- Duplicate readings on re-import → overlapping snapshots → `import_batches` hash ledger = final fix.
- One bad `VR` aborted a whole pickle file → row-level `float()` check → skip + count in `records_skipped`.
- `NUMERIC` aggregates → `Decimal` → Flask stringified stats → `::float8` cast.
- `IntegrityError` never translated → 500 → now `ConflictError`→409, FK error→400.

**Use cases:**
- Bulk importing historical snapshots (.pkl → CSV → PostgreSQL) with duplicate detection.

**Usage:**
- Run `_convert_to_csv`, then `_import_csv`; the importer hashes the file and refuses re-import.

---

## 7. utils/validation.py — one set of rules at one door

**What:** The validators moved from private methods inside one view class to plain importable functions used by every view. They raise instead of returning error tuples; one global handler converts any raise into a JSON 400.

| Function | What it does |
|---|---|
| `validate_machine_id` | positive integer or raise |
| `validate_sensor_tag` | non-empty, stripped |
| `validate_timestamp` | ISO 8601 in, aware datetime out, Z suffix allowed |
| `machine_id_from_query` / `timestamp_from_query` | absent query param → None |
| `pagination_from_query` | limit/offset parsing; raises on non-integers or negatives; caps limit at DEFAULT_PAGE_SIZE |
| `validate_from_to_order` | rejects from later than to |

**Pros:**
- One shared set of rules at one door → one-edit guarantee.
- Raising lets one global handler convert any error into a JSON 400.

**Cons/drawbacks:**
- Validation must be hoisted into a shared module.

**Errors encountered & causes:**
- Whitespace-only machine names slipped through validation → `validate_machine_id` etc. tightened.

**Use cases:**
- Any API input validation (machine id, sensor tag, timestamps, pagination, from/to order).

**Usage:**
- Call these functions at the top of every route; they raise on invalidity; one handler converts to 400.

---

## 8. routes/ — HTTP handling only

**What:** Routes never write SQL; services never touch HTTP; each route follows validate → call service → shape response.

| Class | What it does |
|---|---|
| `MachineView` | one MethodView class for all machine URLs |
| `ReadingView` | one reading or a filtered list; create (requires all four fields), partial update, delete |
| `ReadingExportView` | same filters as the list but no limit/offset; returns a streaming CSV Response |
| `ReadingStatisticsView` | same filters + from/to check; returns min/max/avg |

**Endpoints:**
- `GET /` — api index: name, status, list of all endpoints.
- `GET /health` — service + DB status, 200 if Postgres answers, 503 if not.
- `GET/POST /machines` — list / create machines.
- `GET/PUT/DELETE /machines/<id>` — read / rename / delete (deletes its readings too).
- `GET/POST /readings` — query with machine_id, sensor_tag, from, to, limit, offset / create.
- `GET/PUT/DELETE /readings/<id>` — read / update / delete one reading.
- `GET /readings/statistics` — min/max/avg with the same filters.
- `GET /readings/export` — download all filtered readings as a CSV file.
- `POST /readings/import` — convert the configured pickle to CSV then bulk import it.

**Pros:**
- HTTP handling is isolated from SQL; clean endpoint surface.

**Cons/drawbacks:**
- Routes must not drift into SQL; services must not touch HTTP.

**Errors encountered & causes:**
- N/A here (enforced by design).

**Use cases:**
- Any REST API with MethodView-based routing and a shared validator/filter layer.

**Usage:**
- One MethodView per resource; validate → call service → shape response.

---

## 9. app.py — the factory and the eight handlers

**What:** `create_app()` — the app is built inside a function so importing the module stays side-effect-free.

**Request logging** — before_request stores the start time; after_request logs HTTP method path status duration_ms.

**The eight error handlers, every possible failure becomes JSON:**
- `handle_404` / `handle_405` / `handle_400`
- `handle_validation_error` — ValidationError → 400
- `handle_conflict_error` — ConflictError → 409
- `handle_related_resource_not_found` — RelatedResourceNotFoundError → 400
- `handle_database_error` — DatabaseError → 500 with the generic message only
- `handle_unexpected_error` — Exception → 500 generic

The `__main__` block logs the startup banner and runs waitress (default port 8080).

**Pros:**
- One global error handler; all failures become JSON.
- Factory pattern keeps imports side-effect-free.

**Cons/drawbacks:**
- Eight handlers in one file; the capstone adds Blueprints later.

**Errors encountered & causes:**
- Unknown URL / wrong method → 404/405 instead of an HTML error page.

**Use cases:**
- Any Flask app; factory + global error handlers + health check.

**Usage:**
- `create_app()` for the app; `python app.py` runs waitress on 8080.

---

## 10. Honest status codes

| Code | Meaning |
|---|---|
| 200/201 | success |
| 400 | the client's mistake |
| 404/405 | unknown URL / wrong method; JSON not an HTML page |
| 409 | duplicate machine name is a conflict, not a server error |
| 503 | database down (health check) |
| 500 | anything unexpected, generic message only |

**Pros:**
- Honest, client-friendly error semantics.

**Cons/drawbacks:**
- 500 must stay generic (no internals, no credentials).

**Use cases:**
- API design — map driver errors to HTTP codes.

**Usage:**
- `ConflictError` → 409; `ForeignKeyViolation` → 400; `DatabaseError` → 500 with generic message only.

---

## 11. Key functions used throughout

**Config side** — `load_dotenv()`, `os.getenv()`, `_get_int`.

**Database side** — `psycopg2.connect()`, `ThreadedConnectionPool`, `contextmanager`, `connection.cursor()` / `cursor.execute()`, `cursor.rowcount`, `psycopg2.extras.execute_values`, `psycopg2.errors.UniqueViolation / ForeignKeyViolation / DuplicateDatabase`.

**Import side** — `pickle.load()`, `hashlib.sha256()`, `csv.DictReader` / `csv.writer`, `os.replace()`.

**API side** — Flask / MethodView / `add_url_rule`, `request.get_json(silent=True)`, `jsonify`, `app.errorhandler()`, `Response(generate(), ...)`.

**Logging side** — `logging.getLogger()`, `RotatingFileHandler`, `time.gmtime`.

---

## 12. Design decisions — the why in short

- A real server, never the dev server — waitress.
- The factory pattern — an app that imports with no side effects is an app that can be tested.
- Setup lives in `init_db.py`, not at server boot — a restart must never run DDL.
- Connection pool + context managers + timeouts — fast, visible failure with a log entry beats slow, silent failure every time.
- One global error handler — validation helpers raise, one handler converts.
- Uniqueness only where it is a fact — `machines.machine_name` UNIQUE; readings have no unverified rule.
- The import ledger — duplicate protection moved to ingestion where it belongs.
- Pagination everywhere — GET /readings never dumps the whole table.
- One shared validators module, one shared filter builder — the one-edit guarantee.
- The eight principles are constraints on decisions, not excuses to add layers.

---

## 13. Testing

53 pytest tests in `tests/`, run in ~1.5s with **no live database** (a fake pool replaces the real thing):

- `test_validation.py` (20) — the shared validators.
- `test_error_handlers.py` (8) — all eight error-handler branches.
- `test_services.py` (10) — service logic + the filter builder.
- `test_app_flow.py` (9) — the main route flows.
- `test_pickle_importer.py` (6) — hash skip, row skipping, the CSV stage.

**The alarms caught a real bug the first week:** whitespace-only machine names slipped through validation. The lesson that bit once: services grab `db` at import time, so the test fixture must patch it in each service module.

Run with: `python -m pytest tests/ -q`

**Pros:**
- 53 tests, ~1.5s, no live DB — fast and reliable.

**Cons/drawbacks:**
- Still untested: export streaming, `init_db.py`, cron_jobs/, log_rotation/.

**Errors encountered & causes:**
- Services grab `db` at import time → tests must patch it per service module.

**Use cases:**
- Any API; run `python -m pytest tests/ -q`.

**Usage:**
- Add tests for every service and route; the fake pool replaces the live DB.

---

## 14. Quick start

```bash
pip install -r requirements.txt
copy .env.example .env and fill in the database credentials
python init_db.py   # one-time setup, safe to re-run
python app.py       # the server on http://localhost:8080
curl -X POST http://localhost:8080/readings/import   # load the sample data once
```

---

## 15. Not used yet — next to learn

- Blueprints — app.py still carries factory + handlers + health + import + index in one file.
- Formatted streaming — `iter_all_readings` yields raw DB tuples.
- The CSV stage decision — keep `.pkl → csv → postgres` or go direct.
- Tests for the export generator and `init_db.py`.
- Authentication — all endpoints are open on purpose in this local learning setup.
- MQTT ingestion worker — planned Phase 2 of the IIoT platform.
- Alarm evaluation and lifecycle — planned Phase 3.
- Dashboard — planned Phase 4.
- Authentication and authorization — queued for hardening.
- Queue-based ingestion — revisit when throughput or resilience requirements justify.
- Telemetry retention policy — decision needed before telemetry volume grows, not after.

---

**Quick reference — all Machine Sensor API files**
| File | Role |
|---|---|
| app.py | Factory, error handlers, /health, /readings/import |
| config.py | Fail-fast settings |
| utils/logger.py | Structured UTC logging + rotation |
| utils/validation.py | Shared input validators |
| database/connection.py | Pool + three error types |
| database/schema.py | DDL: tables, indexes, ledger |
| routes/ | MethodViews for machines/readings |
| services/ | SQL, one class per domain |
| errors.py | Shared exceptions |
| init_db.py | One-time DB bootstrap |
| pickle_importer.py | .pkl → CSV → PostgreSQL |
| wsgi.py | Production WSGI entry |
| tests/ | 53 pytest tests |

**Status:** Rebuilt to production standard (waitress, pool with timeouts, import ledger, fail-fast config, shared validators, 53 tests).
