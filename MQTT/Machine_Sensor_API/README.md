# Machine Sensor API

A layered Flask REST API for managing industrial machines and their sensor readings, backed by PostgreSQL. It ships with a bulk pickle-to-CSV importer that loads ~55,918 readings across 12 machines in batched inserts with a duplicate-safe import ledger.

Built as the capstone of an engineering training period and hardened across three passes: **built**, **hardened**, and **rebuilt to production standard** (connection pooling with timeouts, WSGI server, import ledger, 8-principles review).

## What it does

- **Machines** — create, list, get, update, delete machines (identified by name, unique).
- **Sensor readings** — create, list, get, update, delete readings; filter by machine, sensor tag, and time range; paginate; export to CSV; compute min/max/average statistics.
- **Bulk import** — convert a pickle snapshot to CSV and import it in batches of 5,000 with per-row validation, skipped-record counting, and a hash-based import ledger so the same file can never be imported twice.

## Tech stack

- **Python 3** + **Flask 3**
- **PostgreSQL** + **psycopg2-binary** (connection pool, parameterized queries, batch inserts via `execute_values`)
- **waitress** (production WSGI server)
- **python-dotenv** for environment-backed configuration
- **pytest** for the test suite (fake-db seam, no live PostgreSQL required to run)

## Repository layout

```
Machine_Sensor_API/
├── app.py              # Flask app factory + routes + error handlers + import endpoint
├── config.py           # Env-backed configuration, validated at startup
├── wsgi.py             # WSGI entry point
├── init_db.py          # One-shot bootstrap: create database → schema → tables
├── requirements.txt
├── .env                # Local secrets (gitignored); copy .env.example
├── database/
│   ├── connection.py   # DatabaseManager: pooled connections, context managers, transactions
│   └── schema.py       # DDL for schema, machines, sensor_readings, import_batches, indexes
├── routes/
│   ├── machine_routes.py   # /machines
│   └── reading_routes.py   # /readings, /readings/<id>, /readings/statistics, /readings/export
├── services/
│   ├── machine_service.py  # Machine CRUD + conflict handling
│   ├── reading_service.py  # Reading CRUD, filters, streaming export, statistics
│   └── pickle_importer.py  # Pickle → CSV → batched import with import ledger
├── utils/
│   ├── validation.py   # Input validation for query params and request bodies
│   └── logger.py       # Rotating file + console logger
├── errors.py           # ValidationError (mapped to 400)
└── tests/
    ├── conftest.py         # FakeDB seam + Flask test client fixture
    ├── test_app_flow.py    # Route-level happy paths + health failure mode
    ├── test_services.py    # SQL assembly, filter builder, error translation
    ├── test_validation.py
    └── test_pickle_importer.py
```

## API endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/` | API name, status, and endpoint list |
| GET | `/health` | Liveness + database connectivity (503 when DB is down) |
| GET | `/machines` | List all machines |
| POST | `/machines` | Create a machine |
| GET | `/machines/<machine_id>` | Get a machine by ID |
| PUT | `/machines/<machine_id>` | Update a machine name |
| DELETE | `/machines/<machine_id>` | Delete a machine |
| GET | `/readings` | List readings (filter by machine_id, sensor_tag, from, to; paginate with limit/offset) |
| POST | `/readings` | Create a reading |
| GET | `/readings/<reading_id>` | Get a reading by ID |
| PUT | `/readings/<reading_id>` | Update a reading |
| DELETE | `/readings/<reading_id>` | Delete a reading |
| GET | `/readings/statistics` | Min/max/average for a filtered set |
| GET | `/readings/export` | Stream readings as a CSV download |
| POST | `/readings/import` | Import the configured pickle snapshot (triggers pickle → CSV → batched import) |

## Configuration

Copy `.env.example` to `.env` and fill in the values. Required variables:

```
DB_HOST
DB_PORT
DB_NAME
DB_USER
DB_PASSWORD
DB_SCHEMA
```

Optional, with defaults:

```
DATA_DIR            (default: <project>/data)
IMPORT_FILE_NAME    (default: pickle_files_28_03_2025/all_topics_20250328-114500.pkl)
IMPORT_BATCH_SIZE   (default: 5000)
DEFAULT_PAGE_SIZE   (default: 1000)
DB_POOL_MIN         (default: 2)
DB_POOL_MAX         (default: 10)
DB_CONNECT_TIMEOUT  (default: 5)
DB_STATEMENT_TIMEOUT_MS (default: 15000)
LOG_LEVEL           (default: INFO)
```

Configuration is validated at startup. Missing required variables raise a `RuntimeError` with the exact missing names.

## Database setup

The project uses a dedicated PostgreSQL schema and three tables:

- `machines` — `id`, `machine_name` (unique), `created_at`
- `sensor_readings` — `id`, `machine_id` (FK → machines, ON DELETE CASCADE), `sensor_tag`, `sensor_value`, `timestamp`
- `import_batches` — `id`, `file_name`, `file_hash` (unique), `records_inserted`, `records_skipped`, `imported_at`

Indexes cover `(machine_id, timestamp)`, `sensor_tag`, and `timestamp`.

Bootstrap (one time):

```bash
cd Machine_Sensor_API
python init_db.py
```

`init_db.py` connects to the `postgres` maintenance database with autocommit, creates the target database if missing, creates the schema, then creates the tables and indexes.

## Running the server

Development (Flask's dev server):

```bash
cd Machine_Sensor_API
flask run
```

Production (waitress):

```bash
cd Machine_Sensor_API
python app.py
```

The server listens on `http://localhost:8080`.

## Importing sensor data

The import reads the pickle file configured in `IMPORT_FILE_NAME`, converts it to CSV in `data/csv_files_28_03_2025/`, then inserts readings in batches. Each row is validated individually; unparseable rows are skipped and counted. The import is guarded by a hash ledger in `import_batches.file_hash`, so re-importing the same file returns a clear error instead of inserting duplicates.

Trigger it:

```bash
curl -X POST http://localhost:8080/readings/import
```

## Error handling

- `ValidationError` → 400
- `ConflictError` (duplicate machine name) → 409
- `RelatedResourceNotFoundError` (FK violation, e.g. reading for a missing machine) → 400
- `DatabaseError` → 500 with a generic message
- Unhandled exceptions → 500

Every route runs inside a transaction with rollback on failure, and the connection is always returned to the pool.

## Testing

The test suite swaps the real `DatabaseManager` for a `FakeDB` seam, so it exercises the real route, service, and handler code without a live PostgreSQL connection.

```bash
cd Machine_Sensor_API
python -m pytest tests/ -v
```

## Design notes

- **Connections**: pooled via `ThreadedConnectionPool`; acquired through context managers that always commit/rollback and always return the connection (discarding broken ones).
- **Timeouts**: `connect_timeout` and `statement_timeout` are set on every connection so a hung query fails fast and visibly instead of holding a pooled worker forever.
- **SQL**: parameterized everywhere; identifiers come from the schema config, never from user input.
- **Filters**: reading filters are built in one shared helper (`_build_reading_filters`), used by the list, streaming export, and statistics paths.
- **Import ledger**: duplicate protection is based on file content hash, not on a guessed uniqueness rule, so re-runs are safe and explicit.

## Documentation

Full technical detail, the build/harden/rebuild story, and the 8-principles review are in [`Machine_Sensor_API_CONCEPTS.md`](Machine_Sensor_API_CONCEPTS.md) at the project root.

## Project context

Part of an internship training portfolio (Triniti Advanced Software Labs Pvt. Ltd., Aug–Nov 2026), alongside the **Order & Sales Management** app and the **PlantView / Line 30 Live Dashboard**. The same backend discipline — layered routes/services/database, secrets in `.env`, validate at the boundary, pool with timeouts, transaction rollback — is applied across all three.
