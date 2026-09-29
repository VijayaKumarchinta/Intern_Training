# Machine Sensor API — how the code works
## `config.py`

Reads `.env`, checks it, and refuses to start if something is missing or broken.
Better to fail loudly at boot than mysteriously at request 50.

- **`_get_int(name, default=None)`** — turns an env variable into an integer. If the value is not a number, the error names the exact variable. Direct `int(os.getenv(...))` would just throw a bare `TypeError`.

Settings it produces: `DB_HOST/PORT/NAME/USER/PASSWORD/SCHEMA`, pool size (`DB_POOL_MIN` default 2 / `DB_POOL_MAX` default 10, checked so min ≥ 1 and min ≤ max), `DATA_DIR` (defaults to the project's `data/` folder), `IMPORT_BATCH_SIZE` (5000), `IMPORT_FILE_NAME` (defaults to `pickle_files_28_03_2025/all_topics_20250328-114500.pkl`, resolved relative to `DATA_DIR`), `DEFAULT_PAGE_SIZE` (1000 — the page size and the `limit` cap), and `GENERIC_DB_ERROR` (the one message clients see when the database fails; details stay on the server).

## `utils/logger.py`

One shared logger for the whole app: every module does `from utils.logger import logger` and gets the same configured object.

- **Named logger `machine_sensor_api`** — INFO level, `propagate = False` so records aren't printed twice via the root logger.
- **UTC timestamps** — `formatter.converter = time.gmtime`, so log lines end in `Z` and match the timestamps stored in the database.
- **Two handlers** — console (`StreamHandler`) and file (`logs/machine_sensor_api.log`, directory auto-created). Same format for both: `timestamp | LEVEL | name | message`.
- **`if not logger.handlers`** — handlers are attached only once. Re-imports (Flask's reloader, tests importing the app twice) can't duplicate log lines.

## `errors.py`

- **`ValidationError(ValueError)`** — what validation helpers raise when the client sent something wrong. It exists so `app.py` can catch exactly this and answer with a tidy JSON 400.


## `database/connection.py`

### The three errors

| error | meaning | client sees |
| `DatabaseError` | unexpected database trouble | 500, generic message |
| `ConflictError` | a uniqueness rule was hit | 409 |
| `RelatedResourceNotFoundError` | a referenced row is missing | 400 |

The two specific ones inherit from `DatabaseError`, so one `except` still catches everything database-related.

### `DatabaseManager`

- **`__init__`** — copies settings from config, sets `_pool = None`. Connects to nothing yet — importing the module has no side effects, which is what makes testing possible.
- **`_ensure_pool`** — creates the `ThreadedConnectionPool` on first use, returns the existing one after that. Expensive work happens once, lazily. Pool creation (and closing) is logged.
- **`close_pool`** — closes all connections; used at shutdown, not while serving.
- **`connection(commit=True)`** — context manager: borrow connection → hand it to your code → commit if the block finished, roll back if it raised → always return the connection to the pool. If even the rollback fails, the connection is marked closed so the pool discards it instead of handing a broken connection to the next caller. The importer gets its one long transaction simply by keeping the whole file inside a single `connection()` block (default `commit=True`): the single commit fires when the block ends, covering data and ledger row together. Explicit `commit=False` has exactly one user: `iter_all_readings`, which streams rows on a borrowed connection.
- **`cursor(commit=True)`** — same guarantees, but yields a cursor and closes it too. Every service method is built on this one:

```
with db.cursor() as cursor:
    cursor.execute(sql, values)
```

Same idea as `with open(file) as f:` — cleanup that runs even on failure, and can't be forgotten.

- **`get_connection(database=None)`** — one raw connection outside the pool. Two callers only: `health()` (a fresh connection proves Postgres is reachable right now) and `create_database()` (which must connect to the `postgres` maintenance database first).
- **`create_database`** — runs `CREATE DATABASE`; if it already exists, catches `DuplicateDatabase` and moves on. This tolerance is why `init_db.py` can be re-run all day.
- **`create_schema`** — `CREATE SCHEMA IF NOT EXISTS`.
- **`create_tables`** — runs every DDL constant from `schema.py`, in order. All idempotent.
- **`db = DatabaseManager()`** — the single shared instance every service imports.

 

## `database/schema.py`

No functions — one named SQL constant per statement, all `IF NOT EXISTS`.

| constant | what it builds |
| `CREATE_SCHEMA_SQL` | the `machine_schema` namespace — the only schema |
| `CREATE_MACHINES_TABLE_SQL` | `id SERIAL PK`, `machine_name UNIQUE NOT NULL` (a machine's name is its identity — the one uniqueness claim we can prove), `created_at TIMESTAMPTZ` |
| `CREATE_SENSOR_READINGS_TABLE_SQL` | `id BIGSERIAL PK`, `machine_id` FK with `ON DELETE CASCADE`, `sensor_tag`, `sensor_value NUMERIC` (exact decimals), `timestamp TIMESTAMPTZ` — **no uniqueness beyond the PK** |
| `CREATE_IMPORT_BATCHES_TABLE_SQL` | the import ledger: `file_hash CHAR(64) UNIQUE` (SHA-256), `file_name`, `records_inserted`, `records_skipped`, `imported_at` |
| three `CREATE INDEX` constants | `(machine_id, timestamp)` for the main query, `(sensor_tag)` for tag filters, `(timestamp)` for statistics. Indexes speed things up; they never reject rows |

**Why readings have no uniqueness rule:** we used to enforce `(machine_id, sensor_tag, timestamp)` as unique. Then we asked the question that matters: does the source *guarantee* that? The data happens to satisfy it (55,918 readings, zero duplicate triples), but nothing promises it always will. Uniqueness is a business claim — enforce only what you can verify. Duplicate protection now lives in ingestion instead (see the importer).

 

## `services/machine_service.py`

Every method has the same skeleton: try → `with db.cursor()` → execute → return result; `UniqueViolation` becomes `ConflictError` (409), anything else becomes `DatabaseError` (500). Outcomes are logged through the shared logger (created / retrieved / updated / deleted, plus warnings for not-found and conflicts).

- **`add_machine(machine_name)`** — `INSERT ... RETURNING`. Duplicate name → 409 with a clear message instead of a fake 500.
- **`get_all_machines()`** — every machine, ordered by id, as dicts.
- **`get_machine(machine_id)`** — one machine or `None`. Turning `None` into 404 is the route's job, not this method's.
- **`update_machine(machine_id, machine_name)`** — rename. `None` if missing; `ConflictError` if the new name belongs to another machine.
- **`delete_machine(machine_id)`** — `DELETE`, `True`/`False` from `rowcount`. The database cascades to the machine's readings, not us.
- **`count_machines()`** — `SELECT COUNT(*)`.

 

## `services/reading_service.py`

- **`add_reading(machine_id, sensor_tag, sensor_value, timestamp)`** — `INSERT ... RETURNING`. Missing machine (`ForeignKeyViolation`) → 400. No duplicate check on purpose: two readings sharing machine/tag/timestamp are both stored.
- **`get_reading(reading_id)`** — one reading or `None`.
- **`get_readings(machine_id, sensor_tag, from_time, to_time, limit, offset)`** — the list endpoint's engine. Builds the `WHERE` from whichever filters arrived, always ends with `ORDER BY timestamp, id LIMIT %s OFFSET %s`. All values travel as `%s` parameters — that's the SQL-injection defense.
- **`iter_all_readings(..., chunk_size=1000)`** — a generator over *every* matching row, using a named (server-side) cursor with `itersize` inside a `commit=False` connection. Postgres streams rows in chunks; memory stays flat at 55 rows or 55 million. Feeds the CSV export.
- **`update_reading(reading_id, ...)`** — partial update; only supplied fields enter the `SET` clause.
- **`delete_reading(reading_id)`** — `DELETE`, `True`/`False`.
- **`get_statistics(...)`** — same filters, query is `MIN / MAX / AVG`. No matches → JSON `null`s: "no data" is an answer, not an error.
- **`_format_reading(row)`** — the single place a DB row becomes the JSON shape (`reading_id`, `machine_id`, `sensor_tag`, `sensor_value` float, timestamp via `utc_z`).
- **`utc_z(value)`** — module-level helper shared with the export route: normalizes any aware datetime to UTC and renders it ISO 8601 with a `Z` suffix (`2026-09-24T10:00:00Z`). Clients in every timezone see the same instant written the same way; the DB still accepts any offset on input.

 

## `services/pickle_importer.py`

Import is a **two-stage pipeline: pickle → CSV → database**. Source records look like `{"ID": ..., "ST": "TEMP", "TS": 1743157500, "VR": [72.1]}` — tag, unix time, value list (first value used). `ID` is unused for now; whether it's a real event identifier is still an open question.

Why convert to CSV first? It leaves a human-readable artifact next to the raw pickle, separates "parse the weird source format" from "insert into Postgres", and makes the import debuggable — you can open the CSV and see exactly what the database was fed.

- **`__init__(batch_size=IMPORT_BATCH_SIZE)`** — batch size from config, plus a `machine_ids` cache so each machine is resolved once per file, not once per reading.
- **`import_directory(directory)`** — runs `import_file` for every `.pkl` in a folder, sums the counts.
- **`import_file(file_path)`** — the full flow:
  1. resets the machine cache — a cached id from a previous run can go stale if the machine was deleted in between, and every batch insert would then fail with a dangling `machine_id`
  2. file exists? no → `ValueError` → 400
  3. `_get_file_hash()` — SHA-256 of the file's bytes (content, not name)
  4. `_is_already_imported()` — hash already in the ledger → `ValueError` → 400, before any work
  5. `_convert_to_csv()` — pickle → CSV (see below)
  6. `_import_csv()` — one transaction via `db.connection()` for the whole file — data and ledger row commit together or not at all
  7. returns counts plus `csv_file`, the name of the generated CSV

- **`_convert_to_csv(file_path)`** — `pickle.load` (must be a dict of machine name → readings), then writes `DATA_DIR/csv_files_28_03_2025/<stem>.csv` with columns `machine_name, sensor_tag, sensor_value, timestamp`. Per reading: `ST`/`TS`/`VR` pulled, broken rows skipped, unix time → UTC ISO string. Written to a `.tmp` file first, then `replace()`d into place — atomic, so a crash can never leave a half-written CSV that looks finished.
- **`_import_csv(csv_path, file_path, file_hash)`** — reads the CSV back with `csv.DictReader`, rejects it if required columns are missing. Per row: parse value/time, skip and count broken rows, resolve the machine (below), buffer into batches. Every 5,000 rows → `_insert_batch()`. At the end, `_record_import()` writes the ledger row; the context manager commits.
- **machine resolution (inside `_import_csv`)** — SELECT by name from the cache; if missing, a single race-safe statement: `INSERT ... ON CONFLICT (machine_name) DO UPDATE SET machine_name = EXCLUDED.machine_name RETURNING id`. No second SELECT needed, and two concurrent imports can't collide.
- **`_insert_batch(cursor, batch)`** — `execute_values` multi-row insert: one round-trip per 5,000 rows instead of per row. No `ON CONFLICT` — the hash check already proved the content is new.
- **`_record_import(cursor, file_path, file_hash, result)`** — one ledger row per import; also our audit trail for what entered the database. Catches `UniqueViolation`: if a concurrent import of the same file content committed its ledger row between the pre-check and this insert, this whole transaction (data + ledger) rolls back and the client gets the same 400 as the early duplicate check — never a raw 500.
- **`_get_file_hash(file_path)`** — reads in 64 KB chunks, so file size never affects memory.
- **`_is_already_imported(file_hash)`** — `SELECT 1` from `import_batches`.

 

## `routes/machine_routes.py`

- **`MachineView`** — one `MethodView` class for all machine URLs; Flask dispatches to `get`/`post`/`put`/`delete` by HTTP method.
  - **`get(machine_id=None)`** — list without id, single machine with id; `None` → 404.
  - **`post()`** — `get_json(silent=True)` so broken JSON gets a JSON 400, not an HTML page; validates `machine_name`; 201 with the stored machine.
  - **`put(machine_id)`** — rename; 404 if missing, 409 if the new name is taken.
  - **`delete(machine_id)`** — `False` → 404; success → 200 with a message.

 
## `routes/reading_routes.py`

Validation helpers **raise** instead of returning error tuples — one global handler converts any raise into a JSON 400, so a missing check is impossible. They are static/class methods on `ReadingView`; `ReadingExportView` and `ReadingStatisticsView` reuse them as `ReadingView._validate_...()` rather than duplicating the logic.

- **`_validate_machine_id(value)`** — positive integer or raise.
- **`_validate_sensor_tag(value)`** — non-empty, stripped.
- **`_validate_timestamp(value)`** — ISO 8601 in, aware datetime out; `Z` suffix allowed.
- **`_timestamp_from_query(name)`** — `?from=` / `?to=`; absent → `None` (no filter).
- **`_get_machine_id_query_param()`** — same pattern for `?machine_id=`.
- **`_pagination_from_query()`** — `limit`/`offset` parsing; raises on non-integers or negatives; caps `limit` at `DEFAULT_PAGE_SIZE`.
- **`ReadingView`**
  - **`get(reading_id=None)`** — one reading or a filtered list; also rejects `from` > `to` (a client mistake, not a server error).
  - **`post()`** — requires all four fields, reports **all** missing ones at once; 201.
  - **`put(reading_id)`** — partial update of any field.
  - **`delete(reading_id)`** — 404 if missing, 200 on success.
- **`ReadingExportView`**
  - **`get()`** — same filters as the list (no `limit`/`offset`: an export is the complete filtered dataset). Returns a streaming CSV `Response` with `Content-Disposition: attachment` → the browser downloads `readings_export.csv`.
    - **`generate()`** — the nested generator: writes the CSV header, then yields one formatted line per row from `iter_all_readings()`. It reuses a single `StringIO` (seek + truncate per row) instead of allocating a new buffer each time. Bytes start flowing immediately; nothing big is ever held in memory.
- **`ReadingStatisticsView`**
  - **`get()`** — same filters and the same `from`/`to` check; returns `{minimum, maximum, average}`.



## `app.py`

- **`create_app()`** — the factory. The app is built inside a function so importing the module stays side-effect-free — that's what lets waitress, `wsgi.py` and tests all import it cleanly.
- **Request logging** — a `before_request` hook stores `g.request_start_time`, an `after_request` hook logs `HTTP <method> <path> status=<code> duration_ms=...` for every request. Together with the handlers below, the log file tells the full story of any request without touching client-visible responses.
- **The eight error handlers** — every possible failure becomes JSON:

| handler | catches | returns |
| `handle_404` | unknown URL | 404 |
| `handle_405` | wrong method | 405 |
| `handle_400` | malformed request | 400 |
| `handle_validation_error` | `ValidationError` | 400, specific message |
| `handle_conflict_error` | `ConflictError` | 409, specific message |
| `handle_related_resource_not_found` | `RelatedResourceNotFoundError` | 400, specific message |
| `handle_database_error` | `DatabaseError` | 500, **generic message only** |
| `handle_unexpected_error` | `Exception` | 500, generic message |

Client errors log as warnings; the two 500 handlers use `logger.exception`, so the stack trace lands in the log file while the client still gets only a generic message.

- **`add_url_rule(...)`** — connects `/machines`, `/machines/<id>`, `/readings`, `/readings/<id>`, `/readings/export`, `/readings/statistics` to their view classes.
- **`index()`** — `GET /`. JSON: name, status, list of endpoints. The quickest "is it alive" check, and API discovery without docs.
- **`health()`** — `GET /health`. `SELECT 1` on a fresh connection: 200 if Postgres answers, 503 if not. Monitoring watches this.
- **`import_readings()`** — `POST /readings/import`. Path = `DATA_DIR` + `IMPORT_FILE_NAME`. Logs start and completion with the counts; 201 on success with `message`, `file`, `csv_file`, `records_inserted`, `records_skipped`. The importer's `ValueError` (missing file, already-imported hash) → 400; database trouble → the generic 500.
- **`app = create_app()`** — the object the server loads.
- **the `__main__` block** — logs the startup banner and runs waitress (default port 8080), so `python app.py` *is* the production server.

 

## `wsgi.py` and `init_db.py`

- **`wsgi.py`** — one real line: `from app import app`. An external server (`waitress-serve wsgi:app`) loads the app from here.
- **`main()` in `init_db.py`** — `create_database()` → `create_schema()` → `create_tables()`, progress logged via the shared logger. Run once per environment; kept out of the server because a restart must never run DDL. Returns `0` on success and `1` on failure (logged with stack trace) so scripts and CI can detect a failed setup — fully idempotent either way: ten runs, zero damage.
