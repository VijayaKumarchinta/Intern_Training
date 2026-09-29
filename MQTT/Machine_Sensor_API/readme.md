# Machine Sensor API

A small Flask REST API that stores and queries industrial machine sensor readings in PostgreSQL.

The idea in one picture:

```
machines  ──── have ────>  sensor readings
"Machine A"                (TEMP 72.1 at 10:00)
```

A client (Postman, a script, an MQTT pipeline) sends HTTP requests. The API validates them, talks to Postgres and returns JSON. That's the whole story.

---

## THE SIMPLE VERSION (skip this only if you're an engineer)

**What is this?** Factories have machines; machines have sensors that constantly measure things like temperature and pressure. This app is a **librarian for those measurements**: it files every reading safely, answers questions like *"how hot did Machine 5 get last Tuesday?"*, and can swallow thousands of saved readings in one gulp — without ever filing the same thing twice.

**How is it built?** Like a well-run restaurant:

| In a restaurant | In this app |
|---|---|
| The waiter takes your order and brings your food | Takes requests over the internet, returns answers |
| The doorman checks every guest at the door | Checks every incoming piece of data is sensible |
| The kitchen does the real cooking | Does the real work and talks to the database |
| The storeroom keeps the ingredients | Keeps the actual data (PostgreSQL) |
| The manager's diary records everything | Writes down every request and every mistake |

The golden rule: **the waiter never cooks, and the kitchen never takes orders.** Each file has one job, which is why the app is safe to change and easy to understand.

**What keeps it safe?**

- **A chess-clock buzzer** — if the database never answers, the app says so after ~5 seconds instead of freezing forever; any absurdly slow search is cancelled at 15 seconds.
- **A self-archiving diary** — the log file boxes its old pages at 10 MB (five boxes kept), so it can never overflow the shelf.
- **A fingerprint stamp** — every imported data file gets a unique fingerprint in a ledger; the same file is refused at the door, so duplicates are impossible.
- **Sealed envelopes** — data travels in envelopes the storeroom treats as *contents, never instructions*; nobody can sneak commands inside.
- **Honesty about mistakes** — polite, specific error messages for you; the scary technical details go only in the diary for engineers.

Nothing here requires trusting the app blindly — every one of those claims is backed by a specific file and line of code in the detailed sections below (and the plain-language "why" for each recent fix is in *What changed in this version, and why*).

```
client (Postman / curl)
   │  HTTP
   ▼
app.py                    matches the URL, validates input, shapes the response
   ▼
utils/validation.py       one shared set of input checks (used by every reading view)
   ▼
services/                 does the work — the ONLY place that writes SQL
   ▼
database/connection.py    lends a pooled Postgres connection (with timeouts)
   ▼
PostgreSQL                machine_sensor_db → machine_schema → tables
```

Routes never write SQL. Services never touch HTTP. Each layer has exactly one job — that separation is what makes the app safe to change and easy to test.

## Project layout

```
.env                       store the secrets (DB credentials)
config.py                  reads .env, validates it, fails fast if something is missing
app.py                     the Flask app: URLs, global error handlers, health check, import endpoint
wsgi.py                    one line: from app import app — the production server loads the app from here
init_db.py                 one-time setup: creates database, schema and tables (safe to re-run)
database/connection.py     the connection pool + with db.cursor() context managers + timeouts
database/schema.py         the SQL DDL: tables, indexes, the import ledger
utils/logger.py            structured UTC logging with automatic file rotation
utils/validation.py        the shared input validators (machine_id, sensor_tag, timestamps, pagination)
tests/                     the pytest suite (53 tests, no live database needed)
routes/machine_routes.py   receives the machine API calls (list / create / update / delete)
routes/reading_routes.py   receives the reading API calls (query / create / update / delete / export / statistics)
services/machine_service.py    all machine operations — the SQL lives here
services/reading_service.py    all reading operations + statistics + one shared filter builder
services/pickle_importer.py    converts the pickle file to CSV, then bulk-loads the CSV into the database
errors.py                  shared exceptions (ValidationError etc.)
data/                      the pickle files (each file holds readings for many machines)
requirements.txt           pinned dependencies
```

---

## What changed in this version, and why (the human version)

This project went through a design review against eight classic principles (cohesion, encapsulation, coupling, reusability, portability, defensibility, maintainability, and simplicity). The full technical review is in the *Design principles review* section below; this part is the plain-language story of what we actually changed and the reasoning behind each change.

### 1. We gave the database a "buzzer time limit" — connect and statement timeouts

**Before:** if the database disappeared or a query ran forever, the app would wait. Forever. Every request would quietly pile up behind a frozen connection until the whole API stopped answering — with no error message anywhere, because nothing had technically *failed* yet.

**Now:** the app gives the database 5 seconds to answer the door (`connect_timeout=5`), and PostgreSQL itself kills any single query that runs longer than 15 seconds (`statement_timeout=15000`).

**Why it matters:** a slow database should cause a *clear error after a few seconds*, not a *mysterious freeze forever*. Fast, visible failure with a log entry beats slow, silent failure every time. Think of it like a buzzer on a chess clock — if your opponent never moves, the game doesn't hang; it ends, and everyone can see why.

### 2. We taught the logbook to archive itself — rotating logs

**Before:** the log file grew forever. Fine for a demo week; a disk-filler after a few months of real running.

**Now:** when the log reaches 10 MB, it's archived (five archives are kept, then the oldest is dropped) and a fresh file starts. The log level also comes from the environment (`LOG_LEVEL`), so production can run quieter without touching code.

**Why it matters:** logs are the app's diary, and a diary that never runs out of pages eventually fills the whole shelf — and takes the app down with it.

### 3. We deleted one function that nobody ever called

`count_machines()` sat in the machine service, documented, tested-by-nobody, and used by nothing. Dead code isn't dangerous by itself — but every piece of code you keep is a piece someone has to read, keep compatible, and wonder about later. "You aren't gonna need it" is a principle for a reason. (If a use appears, `git`/the zip will remember it.)

### 4. We stopped copy-pasting the same SQL filter logic three times

Three service methods — list readings, stream readings for export, and calculate statistics — each rebuilt the same four filters (`machine_id`, `sensor_tag`, `from`, `to`) by hand. Adding a fifth filter meant remembering three edit sites; missing one would produce quietly inconsistent endpoints.

**Now:** one private helper, `_build_reading_filters()`, builds the `WHERE` clause and the values in a single place. All three methods call it.

**Why it matters:** the DRY rule ("don't repeat yourself") isn't about typing less — it's about the *one-edit guarantee*: a change now happens in one place, so it cannot be half-applied.

### 5. We moved input validation into its own shared module

The validators for machine IDs, sensor tags, timestamps and pagination used to be private methods *inside one view class* — and the other two reading views borrowed them across class boundaries (`ReadingView._validate_timestamp(...)`). That worked, but it meant classes were coupled through each other's internals: awkward to test, awkward to grow.

**Now:** they live in `utils/validation.py` as plain, importable functions used by every view — and the once-triplicated "from ≤ to" cross-check became a single shared `validate_from_to_order()`.

**Why it matters:** one set of rules, applied at one door, means every endpoint rejects bad input the same way. New views get correct validation for free.

### 6. The net effect, measured

| | Before | Now |
|---|---|---|
| Reading routes file | 292 lines (validation + CSV + streaming all inline) | ~199 lines (HTTP only) |
| Filter-building logic | 3 copies | 1 |
| Validators | private to one class, borrowed by others | 1 shared module |
| Hung query / dead DB | waits forever | fails in ≤15s / ≤5s, logged, pool recovers |
| Log file | grows unbounded | rotates at 10 MB, 5 archives |
| Dead code | `count_machines()` | removed |

**What didn't change:** every endpoint, every payload, every status code, every SQL statement. This was a cleanup, not a redesign — the API you call today is byte-for-byte the same API.

### The engineering rule we follow now

> The eight principles are **constraints on decisions, not excuses to add layers**. A change must be justified by a concrete problem — never by "production code should look like X". If a change improves one principle but makes the app more complicated, it's rejected.

That's why there's no ORM, no repository pattern, no dependency-injection framework here. Plain SQL, three layers, one config file — the simplest structure that actually solves the problem.

---

## Quick start

Four commands, in order: install the dependencies, create your local `.env` from the example and fill in your database credentials, run the one-time database setup, then start the server.

```
pip install -r requirements.txt
copy .env.example .env
python init_db.py
python app.py
```

`init_db.py` creates the database, schema and tables — it is one-time setup and safe to re-run. The server runs on **http://localhost:8080** (waitress default — no host/port config needed on purpose).

Run the test suite (no live database needed — the tests swap in a fake pool):

```
python -m pytest tests/ -q
```

Check it is alive:

```
curl http://localhost:8080/          ->  lists every endpoint
curl http://localhost:8080/health    ->  {"database":"connected","status":"ok"}
```

Load the sample data once:

```
curl -X POST http://localhost:8080/readings/import
```

The import flow is:

```
.pkl → CSV → PostgreSQL
```

The generated CSV is stored under `data/csv_files_28_03_2025/` and is the file actually read during the PostgreSQL import.

Running it again returns `400 "already imported"` — the API remembers what it has loaded (see *the import ledger* below). It will never quietly duplicate data.

---

## Optional settings (environment variables)

All optional, all with sensible defaults, all validated at startup (an invalid value stops the boot with an error naming the variable):

| Setting | Default | What it controls |
|---|---|---|
| `DB_CONNECT_TIMEOUT` | `5` | seconds to wait while connecting to Postgres |
| `DB_STATEMENT_TIMEOUT_MS` | `15000` | Postgres cancels any single query longer than this |
| `LOG_LEVEL` | `INFO` | how chatty the logs are — `DEBUG`, `INFO`, `WARNING`, `ERROR` or `CRITICAL` |

---

## Endpoints

No authentication — all endpoints are open (local learning setup).

| Method | Endpoint | Purpose |
|---|---|---|
| GET | / | API index: name, status and list of all endpoints |
| GET | /health | service + DB status |
| GET / POST | /machines | list / create machines |
| GET / PUT / DELETE | /machines/<id> | read / rename / delete (deletes its readings too) |
| GET / POST | /readings | query (`machine_id`, `sensor_tag`, `from`, `to`, `limit`, `offset`) / create |
| GET / PUT / DELETE | /readings/<id> | read / update / delete one reading |
| GET | /readings/statistics | min / max / avg with the same filters |
| GET | /readings/export | download all readings (same filters) as a CSV file — ignores limit/offset by design |
| POST | /readings/import | convert the configured pickle file to CSV, then bulk import the CSV |

Timestamps are ISO 8601, stored as **TIMESTAMPTZ in UTC**, and returned in UTC with a `Z` suffix (`2026-09-24T10:00:00Z`) — a reading means the same moment no matter where in the world you query from. Input accepts any ISO 8601 offset.

### What you get when something goes wrong

| situation | response |
|---|---|
| malformed JSON / missing fields | 400 + a message naming what's wrong |
| unknown URL / wrong method | 404 / 405 (JSON, not an HTML page) |
| duplicate machine name | 409 Conflict |
| reading pointing to a nonexistent machine | 400 Bad Request |
| database down (health check) | 503 Service Unavailable |
| anything unexpected | 500 with a **generic** message only — internal details never leak to clients |

---

## Design decisions — the "why" behind the code

**1. A real server, never the dev server.**
`python app.py` runs **waitress** (a production WSGI server). Flask's dev server with `debug=True` is convenient but exposes an interactive debugger — a remote-code-execution risk. Production servers don't get that door.

**2. The app is built by a factory.**
`create_app()` builds and returns the Flask app; `wsgi.py` just imports the finished object. An app that can be imported without side effects is an app that can be tested.

**3. Setup lives in `init_db.py`, not at server boot.**
A restart must never run DDL. Creating the database/tables is a one-time, deliberate step — and it's idempotent: run it ten times, nothing breaks, nothing duplicates. (This path keeps untimed raw connections on purpose: a slow first-boot `CREATE DATABASE` should never be killed by the 5s connect timeout.)

**4. Connection pooling + context managers + timeouts.**
Opening a fresh Postgres connection per request doesn't survive real traffic. A small pool (2–10) lends connections out; `with db.cursor() as cursor:` guarantees commit on success, rollback on error, and the connection always goes back to the pool — and now the pool's connections carry `connect_timeout` and `statement_timeout`, so neither a dead database nor a runaway query can hold a worker forever.

**5. One global error handler, not fifty try/excepts.**
Validation helpers *raise* `ValidationError`; one global handler turns it into a JSON 400. Impossible to forget a check, and database details never leak into responses.

**6. Honest status codes.**
A duplicate name is a *conflict* (409), not a server error. A reading pointing at a missing machine is a *bad request* (400). A dead database is *unavailable* (503). The status tells the truth first, before the body is even read.

**7. Uniqueness only where it is a fact.**
`machines.machine_name` is UNIQUE — a machine's name is its business identity. The readings table has **no** uniqueness beyond its primary key: nothing verified says two readings can't share a machine + tag + timestamp. Uniqueness is a business claim; we only enforce claims we can prove.

**8. The import ledger (`import_batches`).**
Removing the artificial uniqueness rule moved duplicate protection to ingestion, where it belongs: every source pickle file's **SHA-256 hash** is recorded in the same transaction as its CSV-loaded data. Same source content again → 400, no matter what the file is named. This matters — under the old behavior one file got imported ~211 times and bloated the DB to ~11.8M rows for ~56k real readings.

**9. Pagination everywhere.**
`GET /readings` never dumps the whole table. `?limit=100&offset=0` (default limit 1000, validated, capped at 1000) keeps responses small and queries fast.

**10. Shared validation, one filter builder.**
Every view validates through `utils/validation.py`; every reading query builds its WHERE clause through `_build_reading_filters()`. Same rules, same SQL shape, everywhere — see the human explanation above.

---

## Design principles review (September 2026)

A structured self-review of this codebase against eight classic design principles. The ⚠️ items marked ✅ *fixed in this version* were addressed by the changes described in *What changed in this version, and why*; the rest are recorded next steps (the deeper cross-repo comparison lives in [`PRODUCTION_COMPARISON.md`](../../PRODUCTION_COMPARISON.md) at the repo root). This review was also **cross-checked against a second, independent review** (ChatGPT, working from an archived snapshot): most findings converged, one of its claims was **corrected against the live code** (see *Cross-check* below), and two of its findings were adopted here.

| # | Principle | Score (1–5) | One-line verdict |
|---|---|:---:|---|
| 1 | Cohesion & Single Responsibility | 3.5 | Layers each have one job — `app.py` does four |
| 2 | Encapsulation & Abstraction | 4 | Strong boundaries; one leaky generator |
| 3 | Loose Coupling & Modularity | 3 | Clean one-way layer deps; import-time single everywhere |
| 4 | Reusability & Extensibility | 3 | Single formatting points exist; filter logic lived in 3 places → ✅ fixed |
| 5 | Portability | 4 | pathlib + .env + UTC + waitress; dated folder names + admin-only DB init |
| 6 | Defensibility | 4.5 | The strongest principle here — fail-fast, ledger, no leaks; timeouts added → ✅ |
| 7 | Maintainability & Testability | 3.5 | 53 pytest tests added; export streaming + init_db still untested |
| 8 | Simplicity (KISS · DRY · YAGNI) | 3.5 | KISS strong; the three DRY breaks and dead method → ✅ fixed |

**Overall ≈ 3.4 / 5** — architecture and defensibility lead; testability and duplication are the gap.

### 1. Cohesion & Single Responsibility Principle — 3.5

✅ **What holds:**

- Each layer has exactly one job and it is enforced in practice, not just in this readme: routes parse HTTP (`routes/*.py` — zero SQL), services own SQL (`services/*.py` — zero `request`/`jsonify`), `database/connection.py` owns pool mechanics only.
- `errors.py` exists for exactly one reason; `utils/logger.py` for exactly one; `init_db.py` is DDL and nothing else; `wsgi.py` is one import line.
- `utc_z()` in `reading_service.py` is one tiny function doing one conversion — and it is the *only* place timestamps get their wire format.

⚠️ **What bends:**

- `app.py` carries four responsibilities in one file: app factory + 8 global error handlers + health check + import orchestration + index endpoint. Each is fine alone; together they mean every feature edits the same file. *(Next step, unchanged: split into Blueprints.)*
- The **health check writes SQL in the app layer** (`cursor.execute("SELECT 1")` in `app.py`) — the only place outside `services/` that touches SQL. It has a defensible excuse (probing the DB *is* the health check's whole job, and it deliberately uses a raw connection so a sick pool can't mask a sick database) — but it is a second code path for DB access.
- Exception definitions live in two homes: `ValidationError` in `errors.py`, the `DatabaseError` family in `database/connection.py`. Co-locating exceptions with their producer is a legitimate choice — it just costs discoverability.

### 2. Encapsulation & Abstraction — 4

✅ **What holds:**

- The pool is fully encapsulated: `DatabaseManager` never exposes `_pool`; callers only ever see `db.cursor()` / `db.connection()` context managers. Commit/rollback/broken-connection policy is invisible to every caller — that is encapsulation working.
- `_format_reading()` is the single private function where a DB row becomes the public JSON shape; callers can't see column order.
- Route classes never reach into service internals — `reading_service.update_reading(...)` is the whole contract.
- Validators were extracted to `utils/validation.py` — sibling views no longer borrow each other's private methods. ✅ *fixed in this version*

⚠️ **What bends:**

- `iter_all_readings()` **yields raw DB tuples**, and `ReadingExportView` indexes them positionally (`row[0]` … `row[4]`). The tuple layout — an internal detail — has leaked across the service boundary into a route. If a column is ever reordered, the export breaks silently. *(Next step: yield formatted dicts.)*
- The "shape" a service returns (a dict with keys `reading_id`, `machine_id`, …) is an implicit contract with no schema anywhere. Fine at this size; a `ReadingOut` model would make it explicit.

### 3. Loose Coupling & Modularity — 3

✅ **What holds:**

- Dependencies point **one way only**: `routes → services → database`. No cycles, no back-references, no service imports a route — ever.
- Modules are genuinely swappable units: the importer never imports Flask; the schema lives alone in `database/schema.py`.

⚠️ **What bends:**

- **Import-time singletons everywhere**: `db = DatabaseManager()`, `machine_service = MachineService()`, `reading_service = ReadingService()`, `pickle_importer = PickleImporter()`. Routes bind to concrete singletons at import time, so a test cannot inject a fake service or a scratch `db` without monkeypatching. This is the single biggest testability tax in the codebase. *(Next step — but only when tests actually require it; YAGNI applies.)*
- Config is module constants imported at load time (`from config import DEFAULT_PAGE_SIZE`) — settings are frozen per process, so two app instances can't have two settings. *(Next step: settings via `app.config`.)*

### 4. Reusability & Extensibility — 3

✅ **What holds:**

- Reusable single points exist where they matter most: `_format_reading()` (row → dict), `utc_z()` (timestamp → wire), `_get_file_hash()` (chunked SHA-256), `_insert_batch()` (bulk insert), the `READING_SELECT` column constant.
- **The filter builder is now one shared `_build_reading_filters()`** — previously copy-pasted in `get_readings` / `iter_all_readings` / `get_statistics`. Adding a fifth filter is now a one-edit change. ✅ *fixed in this version*
- Adding a whole new resource is a known, additive motion: one route file + one service file + DDL — nothing existing needs editing (beyond registration).

⚠️ **What bends:**

- The machine service still builds the machine dict inline in three methods while `reading_service.py` centralizes it in `_format_reading` — the same idea, inconsistently applied between sibling files. *(Small; next cleanup.)*

### 5. Portability — 4

✅ **What holds:**

- No hardcoded credentials, hosts, or ports — everything flows from `.env` through `config.py`, which *refuses to boot* if a variable is missing.
- `pathlib` for every path, `LOG_DIR.mkdir(parents=True, exist_ok=True)` instead of assuming the folder exists.
- All timestamps stored and emitted in UTC (`TIMESTAMPTZ`, `formatter.converter = time.gmtime`, `utc_z`) — the app means the same thing in every timezone.
- **waitress** instead of gunicorn: a pure-Python WSGI server, so the app deploys on Windows and Linux alike.
- Log level now comes from the environment (`LOG_LEVEL`) instead of a hardcoded `INFO`. ✅ *fixed in this version*

⚠️ **What bends:**

- `pickle_importer.py` hardcodes a **dated folder name**: `csv_directory = DATA_DIR / "csv_files_28_03_2025"`. Import a snapshot from a different date and the CSV silently lands in a March-2025 folder. `IMPORT_FILE_NAME` in `config.py` has the same date baked into its *default* — but that one is env-overridable, so only the CSV directory is a true code-level assumption. *(Next step: derive the CSV folder from the input file's parent.)*
- **Operational portability:** `init_db.py` → `db.create_database()` assumes the connecting user has PostgreSQL **administrative rights** (`CREATE DATABASE`). Normal in development; often refused in production, where a pre-created database and limited credentials are handed over. The right shape later: keep `init_db.py` as the dev-only bootstrap and treat "database already exists" as the normal production path. *(Finding adopted from the cross-review.)*

### 6. Defensibility — 4.5 (the strongest principle in the codebase)

✅ **What holds:**

- **Fail-fast everywhere it counts:** `config.py` raises at startup on missing/non-integer env vars and on invalid pool bounds (`DB_POOL_MIN >= 1`, `DB_POOL_MAX >= DB_POOL_MIN`) — the app never boots half-configured. The new timeout knobs are validated the same way. ✅
- **Every SQL value is parameterized** (`%s` placeholders) — zero string-interpolated values across all three service files. SQL injection has no door.
- **The import ledger:** SHA-256 content hash recorded in the *same transaction* as the imported rows, `ON CONFLICT DO NOTHING` on inserts, `_is_already_imported()` pre-check, and the CSV staged via temp-file-then-`replace()` (atomic write — a crash mid-import can't leave a half-written CSV).
- **No information leaks:** unexpected errors return a generic 500 body while `logger.exception` keeps the real cause server-side; database details never reach a client.
- **Input hardened at the boundary:** pagination capped (`min(limit, DEFAULT_PAGE_SIZE)`), negative/zero values rejected, `machine_id > 0` enforced, ISO-8601 parsing with explicit `ValidationError`s, `request.get_json(silent=True)` so malformed JSON is an error, not a crash.
- **Pool armor:** broken connections detected (`conn.closed`) and discarded (`putconn(conn, close=True)`); failed rollbacks mark the connection dead instead of poisoning the pool.
- **Timeouts added:** `connect_timeout=5` and `statement_timeout=15000` on pooled connections — a hung query can no longer hold a worker forever, and a dead database fails in seconds instead of freezing the app. ✅ *fixed in this version*
- The importer validates CSV headers (`required_columns.issubset(...)`) and skips malformed rows *with counters* rather than dying on row 10,000.

⚠️ **What bends:**

- `pickle.load` remains code-execution-by-design — mitigated (trusted internal source, shape validation, `ST/TS/VR` key allowlist) but never eliminated. *(Long-term: accept JSONL/Parquet at the boundary.)*

### 7. Maintainability & Testability — 2.5 → **3.5** (pytest added September 28)

✅ **What holds:**

- `create_app()` is importable with **no side effects** — the factory pattern's whole payoff — and `wsgi.py` is a one-line import of the finished object.
- Services are plain classes with plain methods: `reading_service.get_readings(machine_id=...)` is directly callable from any future test.
- Documentation is part of the maintenance story: this readme, `code_explanation.md` (function-by-function), and the Postman collection.
- Consistent internal conventions make the code scannable: every service method follows try → `with db.cursor()` → log → return; every route follows validate → call service → shape response.

⚠️ **What bends:**

- **The automated test suite now exists** (September 28): 53 tests in `tests/` covering all 8 error-handler branches, the shared validators, the filter builder, driver-error → HTTP-code translation, the importer's hash-skip and row-skipping, and the main route flows — all against a fake pool, no live database, ~1.5s total. ✅ *#1 gap closed*
- Coverage is broad but not complete: the export streaming generator and the `init_db.py` bootstrap are still untested.
- The import-time singletons (see principle 3) and frozen config constants mean the standard testing moves — inject a fake service, boot the app with a test config, point the pool at a scratch database — all require editing source first. *(The test suite works around this by patching the `db` name in each service module — the workaround itself documents why dependency injection would help.)*
- The `app.py` concentration (principle 1) is a maintenance tax: parallel work on two features means merge conflicts on one file.

### 8. Simplicity — KISS · DRY · YAGNI — 3.5

✅ **What holds:**

- **KISS, genuinely:** plain SQL over an ORM (a deliberate, stated choice), no base-class hierarchy for just two resources, no plugin/config frameworks, no speculative abstractions. The reading-export streaming is the fanciest thing in the repo — and it exists because unbounded `fetchall()` genuinely was a problem.
- **YAGNI, mostly respected:** nothing in the code exists "just in case." No auth framework, no caching layer, no message queue — each would be premature today. `count_machines()` was the one miss — now deleted. ✅ *fixed in this version*

⚠️ **What bends:**

- **The CSV intermediate stage is a decision waiting to happen.** The pipeline is `.pkl → CSV → PostgreSQL`. If the CSV is merely a byproduct, going `.pkl → PostgreSQL` directly would delete an entire failure surface: CSV writing, temp-file staging, CSV parsing, extra disk I/O, and the dated output folder. If the CSV is wanted as an audit/inspection/archival artifact, it stays — but as a *deliberate*, documented pipeline stage. Decide before writing any more importer code. *(Finding adopted from the cross-review.)*
- The validators now live in one shared module — the coupling-through-internals concern is resolved. ✅ *fixed in this version*

### Cross-check against a second review (and one correction)

A second, independent review (ChatGPT, based on an archived zip snapshot) reached the **same conclusions on almost every point**: `app.py`, `reading_routes.py`, and `PickleImporter` carry too many responsibilities; global singletons hurt testability; the reading-filter builder was duplicated ×3; `count_machines()` was dead; dated folder names reduce portability; the pickle trust boundary must stay internal; and there are no automated tests. It contributed two findings adopted above — the **CSV-stage KISS question** and the **admin-rights portability note** — and, most usefully, the *what NOT to change* discipline: no repositories, DI frameworks, ORM rewrites, or `BaseService` classes just to score principle points.

**One correction.** That review's Priority 1 was a real inconsistency: *"`schema.py` defines `DROP_LEGACY_UNIQUE_INDEX_SQL` / `DROP_LEGACY_UNIQUE_CONSTRAINT_SQL` but `create_tables()` never executes them."* **That was true of the archived snapshot, not of the live code.** The current `database/schema.py` contains only `CREATE` statements, and a full-text search for `DROP` across the project returns zero matches. The zip is an older snapshot — the lesson: review the live tree, not the archive.

One related verification is still worth a single command: since the live init path never *drops* anything, a database that was ever created by the older schema could still carry the legacy uniqueness rule. `\d machine_schema.sensor_readings` in psql settles it — the history section says the legacy constraint was already dropped, so this is verification, not a known defect.

### What changed in this cleanup (mapped to the review)

| # | Change | Principle it serves |
|:---:|---|---|
| 1 | Shared filter builder `_build_reading_filters()` in `reading_service.py` | 8 DRY, 4 Reusability |
| 2 | Shared validators in `utils/validation.py`; all views import them; one `validate_from_to_order()` | 3 Coupling, 8 DRY, 2 Encapsulation |
| 3 | Deleted `count_machines()` | 8 YAGNI |
| 4 | DB `connect_timeout` + `statement_timeout` (env-tunable) | 6 Defensibility |
| 5 | `RotatingFileHandler` + `LOG_LEVEL` from env | 7 Maintainability, 5 Portability |

**Recorded but not done (in priority order):** split `app.py` into Blueprints · make `iter_all_readings()` yield formatted dicts · decide the CSV stage's fate · derive the CSV output folder from the input file's parent · verify no legacy unique index survives on old databases (psql check) · tests for export streaming and `init_db.py`.

---

## History: from v2 to now

The project was rebuilt to production standard. The old version ran Flask's dev server with `debug=True`, opened a fresh DB connection per request, had per-route try/excepts that leaked SQL details, returned 500 for duplicates, created the database on every boot (which silently never ran under a real server), and let a re-import multiply the same file ~211 times.

Main changes, in short:

1. real WSGI server (waitress) + `wsgi.py` entrypoint; app factory pattern
2. database bootstrap extracted to `python init_db.py`; server never runs DDL
3. `ThreadedConnectionPool` + `with db.cursor()` context managers replace per-request connections
4. global JSON error handlers; internal errors return a generic message only
5. status codes corrected: duplicate → 409, bad FK → 400, DB down → 503
6. exception-based validation (`ValidationError` → JSON 400, missing fields reported all at once)
7. fail-fast config validation; secrets in `.env`
8. readings table has no unverified uniqueness rule; duplicate protection moved to ingestion (`import_batches`, content-hash guard); legacy constraint dropped
9. `TIMESTAMP` → `TIMESTAMPTZ` (UTC-aware, no DST ambiguity); real composite index on `(machine_id, timestamp)`
10. pagination on reading queries; pinned requirements; dead code removed
11. *(this cleanup)* shared validators module, shared SQL filter builder, dead code removed, DB timeouts, rotating logs — details in *What changed in this version, and why*

| old (v2) | now |
|---|---|
| app.py | app.py + wsgi.py + init_db.py |
| config_v2.py | config.py |
| database/connection_v2.py | database/connection.py |
| database/schema.py | database/schema.py |
| database/models.py | removed (dead code — never imported) |
| services/*_v2.py | services/*.py |
| routes/*_v2.py | routes/*.py |
| — | errors.py, utils/validation.py, .env.example (new) |

*The pre-cleanup state of every file is archived in `Machine_Sensor_API.zip`. Function-by-function walkthrough: see `code_explanation.md`. Test suite: import `Machine_Sensor_API_Postman_Test_Suite.json` into Postman (server on 8080, run the whole collection top-to-bottom).*
