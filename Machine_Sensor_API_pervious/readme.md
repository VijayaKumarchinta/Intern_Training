# Machine Sensor API

A small Flask REST API that stores and queries industrial machine sensor readings in PostgreSQL.

The idea in one picture:

```
machines  ──── have ────>  sensor readings
"Machine A"                (TEMP 72.1 at 10:00)
```

A client (Postman, a script, an MQTT pipeline) sends HTTP requests. The API validates them, talks to Postgres and returns JSON. That's the whole story.

---

## How a request travels

```
client (Postman / curl)
   │  HTTP
   ▼
app.py                    matches the URL, validates input, shapes the response
   ▼
services/                 does the work — the ONLY place that writes SQL
   ▼
database/connection.py    lends a pooled Postgres connection
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
database/connection.py     the connection pool + the with db.cursor() context managers
database/schema.py         the SQL DDL: tables, indexes, the import ledger
routes/machine_routes.py   receives the machine API calls (list / create / update / delete)
routes/reading_routes.py   receives the reading API calls (query / create / update / delete)
services/machine_service.py    all machine operations — the SQL lives here
services/reading_service.py    all reading operations + statistics
services/pickle_importer.py    converts the pickle file to CSV, then bulk-loads the CSV into the database
errors.py                  shared exceptions (ValidationError etc.)
data/                      the pickle files (each file holds readings for many machines)
requirements.txt           pinned dependencies
```

Learning notes that saved me time:

- `pathlib` — clean way to deal with file system paths
- `dotenv` — lets Python read `.env` files
- when reading data files, build the path from the project base first, then point into the data folder

---

## Quick start

```
pip install -r requirements.txt
copy .env.example .env        # then fill in your DB credentials
python init_db.py             # one-time: database + schema + tables
python app.py                 # starts the server
```

The server runs on **http://localhost:8080** (waitress default — no host/port config needed on purpose).

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
A restart must never run DDL. Creating the database/tables is a one-time, deliberate step — and it's idempotent: run it ten times, nothing breaks, nothing duplicates.

**4. Connection pooling + context managers.**
Opening a fresh Postgres connection (TCP handshake + auth) per request doesn't survive real traffic. A small pool (2–10) lends connections out; `with db.cursor() as cursor:` guarantees commit on success, rollback on error, and the connection always goes back to the pool. Same idea as `with open(file) as f:` — cleanup that cannot be forgotten.

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

| old (v2) | now |
|---|---|
| app.py | app.py + wsgi.py + init_db.py |
| config_v2.py | config.py |
| database/connection_v2.py | database/connection.py |
| database/schema.py | database/schema.py |
| database/models.py | removed (dead code — never imported) |
| services/*_v2.py | services/*.py |
| routes/*_v2.py | routes/*.py |
| — | errors.py, .env.example (new) |

---

*Function-by-function walkthrough: see `code_explanation.md`. Test suite: import `Machine_Sensor_API_Postman_Test_Suite.json` into Postman (server on 8080, run the whole collection top-to-bottom).*
