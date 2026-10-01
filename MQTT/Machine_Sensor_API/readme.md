Machine Sensor API:
a small Flask REST api that stores and queries industrial machine sensor readings in postgres, the capstone where mqtt thinking becomes a full production-style service
machines --- have ---> sensor readings ("Machine A" has TEMP 72.1 at 10:00)
a client (postman, a script, an mqtt pipeline) sends http requests, the api validates them, talks to postgres and returns json

### what i did in this project in short
- built a three layer api (routes → services → database) where each layer has one job, the golden rule: the waiter never cooks and the kitchen never takes orders
- rebuilt it to production standard: waitress instead of the dev server, connection pool with timeouts, global json error handlers, honest status codes, rotating logs
- moved duplicate protection to ingestion with a sha-256 import ledger after learning that one file imported ~211 times bloated the db to ~11.8M rows for ~56k real readings
- added a shared validators module and one shared sql filter builder after a design review flagged the same logic copy-pasted in three places
- wrote 53 pytest tests that run in ~1.5s against a fake pool with no live database

# project layout
    - .env - stores the secrets (db credentials), never in code
    - config.py - reads .env, validates it, fails fast at boot if something is missing or broken
    - app.py - the flask app: urls, global error handlers, health check, import endpoint
    - wsgi.py - one line: from app import app, the production server loads the app from here
    - init_db.py - one-time setup: creates database, schema and tables, safe to re-run
    - database/connection.py - the connection pool + with db.cursor() context managers + timeouts
    - database/schema.py - the sql ddl: tables, indexes, the import ledger
    - utils/logger.py - structured utc logging with automatic file rotation
    - utils/validation.py - the shared input validators used by every view
    - routes/machine_routes.py - receives the machine api calls
    - routes/reading_routes.py - receives the reading api calls (query/create/update/delete/export/statistics)
    - services/machine_service.py - all machine operations, the sql lives here
    - services/reading_service.py - all reading operations + statistics + one shared filter builder
    - services/pickle_importer.py - converts the pickle file to csv, then bulk-loads the csv into the database
    - errors.py - shared exceptions (ValidationError etc.)
    - tests/ - the pytest suite (53 tests, no live database needed)

# config.py - fail-fast settings
- reads .env and refuses to start if something is missing, better to fail loudly at boot than mysteriously at request 50
- _get_int(name, default=None) - turns an env variable into an integer and names the exact variable in the error
- what it produces
    - DB_HOST/PORT/NAME/USER/PASSWORD/SCHEMA - the database credentials
    - DB_POOL_MIN=2 / DB_POOL_MAX=10 - pool size, checked so min ≥ 1 and min ≤ max
    - DATA_DIR - defaults to the project's data/ folder
    - IMPORT_BATCH_SIZE=5000 - rows per batch insert
    - IMPORT_FILE_NAME - the pickle to import, resolved relative to DATA_DIR
    - DEFAULT_PAGE_SIZE=1000 - the page size and the limit cap
    - GENERIC_DB_ERROR - the one message clients see when the database fails, details stay on the server
- the resilience knobs, all env-tunable and validated fail-fast
    - DB_CONNECT_TIMEOUT=5 - seconds a connection attempt may take, a dead database fails in ~5 seconds instead of hanging forever
    - DB_STATEMENT_TIMEOUT_MS=15000 - postgres itself cancels any single query longer than this, one slow query can't hold a pooled worker forever
    - LOG_LEVEL=INFO - must be one of the five standard levels, production can run quieter without touching code

# utils/logger.py - one shared logger
- named logger "machine_sensor_api", propagate = False so records aren't printed twice
- UTC timestamps - formatter.converter = time.gmtime, log lines end in Z and match the timestamps stored in the database
- two handlers - console (StreamHandler) and file (RotatingFileHandler at 10 MB, five archives kept, oldest dropped), a diary that archives itself so months of running can never fill the disk
- if not logger.handlers - handlers attached only once, re-imports can't duplicate log lines

# database/connection.py - the pool and the three errors
- the three errors
    - DatabaseError - unexpected database trouble, client sees 500 with a generic message
    - ConflictError - a uniqueness rule was hit, client sees 409 (inherits from DatabaseError)
    - RelatedResourceNotFoundError - a referenced row is missing, client sees 400 (inherits from DatabaseError)
- DatabaseManager
    - __init__ - copies settings, sets _pool = None, connects to nothing yet, importing the module has no side effects which is what makes testing possible
    - _ensure_pool - creates the ThreadedConnectionPool lazily on first use, every pooled connection carries connect_timeout and the statement_timeout option
    - connection(commit=True) - context manager: borrow connection → commit if the block finished, roll back if it raised → always return it to the pool, if even the rollback fails the connection is marked closed so the pool discards it instead of handing a broken one to the next caller
    - cursor(commit=True) - same guarantees but yields a cursor and closes it too, every service method is built on this one: with db.cursor() as cursor: cursor.execute(sql, values)
    - get_connection(database=None) - one raw connection outside the pool, two callers only: health() (a fresh connection proves postgres is reachable right now) and create_database() (must connect to the postgres maintenance database first), it gets connect_timeout but deliberately no statement timeout because a slow first-boot CREATE DATABASE must never be killed mid-setup
    - create_database / create_schema / create_tables - all idempotent, DuplicateDatabase is caught and treated as fine, this is why init_db.py can be re-run all day
- db = DatabaseManager() - the single shared instance every service imports

# database/schema.py - what the tables claim
    - machine_schema - the only schema namespace
    - machines - id SERIAL PK, machine_name UNIQUE NOT NULL (a machine's name is its identity, the one uniqueness claim we can prove), created_at TIMESTAMPTZ
    - sensor_readings - id BIGSERIAL PK, machine_id FK with ON DELETE CASCADE, sensor_tag, sensor_value NUMERIC (exact decimals), timestamp TIMESTAMPTZ, no uniqueness beyond the PK
    - import_batches - the import ledger: file_hash CHAR(64) UNIQUE (sha-256), file_name, records_inserted, records_skipped, imported_at
    - three indexes - (machine_id, timestamp) for the main query, (sensor_tag) for tag filters, (timestamp) for statistics, indexes speed things up, they never reject rows
- why readings have no uniqueness rule - we used to enforce (machine_id, sensor_tag, timestamp) as unique, then asked the question that matters: does the source guarantee that? the data happens to satisfy it but nothing promises it always will, uniqueness is a business claim, enforce only what you can verify, duplicate protection now lives in ingestion instead

# services/ - the only place sql lives
- every method follows the same skeleton: try → with db.cursor() → execute → return, UniqueViolation becomes ConflictError (409), anything else becomes DatabaseError (500)
machine_service.py
    - add_machine - INSERT ... RETURNING, duplicate name → 409 with a clear message instead of a fake 500
    - get_all_machines / get_machine / update_machine / delete_machine - turning None into 404 is the route's job, delete returns True/False from rowcount and the database cascades to the readings
reading_service.py
    - add_reading - missing machine (ForeignKeyViolation) → 400, no duplicate check on purpose
    - get_readings - builds the WHERE via _build_reading_filters() and always ends with ORDER BY timestamp, id LIMIT %s OFFSET %s, all values travel as %s parameters which is the sql-injection defense
    - iter_all_readings - a generator over every matching row using a named (server-side) cursor with itersize inside a commit=False connection, postgres streams rows in chunks so memory stays flat at 55 rows or 55 million, feeds the csv export
    - get_statistics - same filters, query is MIN/MAX/AVG, no matches → JSON nulls because "no data" is an answer not an error
    - _build_reading_filters - the one place the standard reading filters become a WHERE clause plus values, get_readings + iter_all_readings + get_statistics all call it (they used to build the same conditions by hand, three copies where adding a fifth filter meant three edits)
    - _format_reading - the single place a db row becomes the json shape
    - utc_z - normalizes any aware datetime to UTC and renders iso 8601 with a Z suffix, clients in every timezone see the same instant written the same way, the db still accepts any offset on input
pickle_importer.py - the two-stage pipeline: .pkl → csv → postgres
    - why csv first - it leaves a human-readable artifact next to the raw pickle, separates "parse the weird source format" from "insert into postgres" and makes the import debuggable
    - source records look like {"ID": ..., "ST": "TEMP", "TS": 1743157500, "VR": [72.1]}, tag + unix time + value list (first value used)
    - import_file - resets the machine cache, checks the file exists, hashes it, refuses if already imported, converts to csv, imports in one transaction for the whole file so data and ledger row commit together or not at all
    - _convert_to_csv - pickle.load (must be a dict of machine name → readings), broken rows skipped, unix time → utc iso string, written to a .tmp file first then replace()d into place which is atomic so a crash can never leave a half-written csv that looks finished
    - _import_csv - csv.DictReader, rejects missing columns, skips and counts broken rows, resolves the machine from the cache or with one race-safe statement: INSERT ... ON CONFLICT (machine_name) DO UPDATE ... RETURNING id so two concurrent imports can't collide
    - _insert_batch - execute_values multi-row insert, one round-trip per 5000 rows instead of per row
    - _record_import - one ledger row per import, catches UniqueViolation so a concurrent import of the same content rolls back the whole transaction and the client gets the same 400 as the early duplicate check, never a raw 500
    - _get_file_hash - sha-256 read in 64 KB chunks so file size never affects memory, the hash is the fingerprint: same content again → 400 no matter what the file is named

# utils/validation.py - one set of rules at one door
- the validators used to be private methods inside one view class with the other views borrowing them across class boundaries, now they are plain importable functions used by every view
- they raise instead of returning error tuples, one global handler converts any raise into a json 400 so a missing check is impossible
    - validate_machine_id - positive integer or raise
    - validate_sensor_tag - non-empty, stripped
    - validate_timestamp - iso 8601 in, aware datetime out, Z suffix allowed
    - machine_id_from_query / timestamp_from_query - absent query param → None (no filter)
    - pagination_from_query - limit/offset parsing, raises on non-integers or negatives, caps limit at DEFAULT_PAGE_SIZE
    - validate_from_to_order - rejects from later than to, a client mistake not a server error, used to be copy-pasted in all three views

# routes/ - http handling only
- routes never write sql, services never touch http, each route follows validate → call service → shape response
    - MachineView - one MethodView class for all machine urls, flask dispatches to get/post/put/delete by http method, get_json(silent=True) so broken json gets a json 400 not an html page
    - ReadingView - one reading or a filtered list, create (requires all four fields and reports all missing ones at once), partial update, delete
    - ReadingExportView - same filters as the list but no limit/offset because an export is the complete filtered dataset, returns a streaming csv Response with Content-Disposition: attachment, the nested generate() reuses a single StringIO per row so bytes start flowing immediately and nothing big is ever held in memory
    - ReadingStatisticsView - same filters and the same from/to check, returns minimum/maximum/average
- the endpoints
    - GET / - api index: name, status and list of all endpoints
    - GET /health - service + db status, 200 if postgres answers, 503 if not, monitoring watches this
    - GET/POST /machines - list / create machines
    - GET/PUT/DELETE /machines/<id> - read / rename / delete (deletes its readings too)
    - GET/POST /readings - query with machine_id, sensor_tag, from, to, limit, offset / create
    - GET/PUT/DELETE /readings/<id> - read / update / delete one reading
    - GET /readings/statistics - min/max/avg with the same filters
    - GET /readings/export - download all filtered readings as a csv file
    - POST /readings/import - convert the configured pickle to csv then bulk import it, running it again returns 400 "already imported", the api remembers what it has loaded

# app.py - the factory and the eight handlers
- create_app() - the app is built inside a function so importing the module stays side-effect-free, that is what lets waitress, wsgi.py and tests all import it cleanly
- request logging - before_request stores the start time, after_request logs HTTP method path status duration_ms for every request
- the eight error handlers, every possible failure becomes json
    - handle_404 / handle_405 / handle_400 - unknown url / wrong method / malformed request
    - handle_validation_error - ValidationError → 400 with a specific message
    - handle_conflict_error - ConflictError → 409
    - handle_related_resource_not_found - RelatedResourceNotFoundError → 400
    - handle_database_error - DatabaseError → 500 with the generic message only, logger.exception keeps the real cause server-side
    - handle_unexpected_error - Exception → 500 generic, internal details never leak to clients
- the __main__ block - logs the startup banner and runs waitress (default port 8080), so python app.py IS the production server

# honest status codes
    - 200/201 - success
    - 400 - the client's mistake (bad json, missing fields, reading pointing to a nonexistent machine, from > to)
    - 404/405 - unknown url / wrong method, json not an html page
    - 409 - duplicate machine name is a conflict, not a server error
    - 503 - database down (health check)
    - 500 - anything unexpected, generic message only

# key functions used throughout (w.r.t these files)
the config side
    - load_dotenv() - loads the .env secrets
    - os.getenv() - reads each variable, _get_int validates the numeric ones
the database side
    - psycopg2.connect() - the raw connections, with connect_timeout and the statement_timeout option
    - ThreadedConnectionPool - getconn/putconn, the reusable shopping cart instead of buying a new one per customer
    - contextmanager - turns connection()/cursor() into with-blocks where commit/rollback/close happen automatically
    - connection.cursor() / cursor.execute() - where python tells postgres to run sql
    - cursor.rowcount - tells whether the update/delete actually changed any row
    - psycopg2.extras.execute_values - batch insert 5000 rows in one shot for the big imports
    - psycopg2.errors.UniqueViolation / ForeignKeyViolation / DuplicateDatabase - the specific errors the services translate into honest status codes
the import side
    - pickle.load() - reads the snapshot dict (trusted internal source only, code-execution-by-design)
    - hashlib.sha256() - the content fingerprint recorded in the ledger
    - csv.DictReader / csv.writer - parse the generated csv back and write the export
    - os.replace() - the atomic staging step so a crash can't leave a half-written csv
the api side
    - Flask / MethodView / add_url_rule - the app factory and class-based views
    - request.get_json(silent=True) - broken json becomes a tidy 400, not a crash
    - jsonify - every response leaves as json
    - app.errorhandler() - the eight global handlers instead of fifty try/excepts
    - Response(generate(), ...) - the streaming csv export
the logging side
    - logging.getLogger() / RotatingFileHandler / time.gmtime - the named logger, the self-archiving diary, utc timestamps

# design decisions - the why in short
    - a real server, never the dev server - waitress, because the flask dev server with debug=True is an interactive debugger and a remote-code-execution risk
    - the factory pattern - an app that imports with no side effects is an app that can be tested
    - setup lives in init_db.py, not at server boot - a restart must never run ddl, and it is idempotent: ten runs, zero damage
    - connection pool + context managers + timeouts - fast, visible failure with a log entry beats slow, silent failure every time
    - one global error handler - validation helpers raise, one handler converts, impossible to forget a check and database details never leak
    - uniqueness only where it is a fact - machines.machine_name UNIQUE, readings have no unverified rule
    - the import ledger - duplicate protection moved to ingestion where it belongs, the hash is checked before any work and recorded in the same transaction as the data
    - pagination everywhere - GET /readings never dumps the whole table, limit is validated and capped
    - one shared validators module, one shared filter builder - the one-edit guarantee: a change happens in one place so it cannot be half-applied
    - the eight principles are constraints on decisions, not excuses to add layers - no orm, no repository pattern, no dependency-injection framework, plain sql and three layers is the simplest structure that actually solves the problem

# testing
- 53 pytest tests in tests/, run in ~1.5s with no live database (a fake pool in place of the real thing)
    - test_validation.py (20) - the shared validators
    - test_error_handlers.py (8) - all eight error-handler branches
    - test_services.py (10) - service logic + the filter builder
    - test_app_flow.py (9) - the main route flows
    - test_pickle_importer.py (6) - hash skip, row skipping, the csv stage
- the alarms caught a real bug the first week: whitespace-only machine names slipped through validation
- the lesson that bit once: services grab db at import time, so the test fixture must patch it in each service module
- run with: python -m pytest tests/ -q

# quick start
the cmds in order are
    - pip install -r requirements.txt
    - copy .env.example .env and fill in the database credentials
    - python init_db.py - one-time setup, safe to re-run
    - python app.py - the server on http://localhost:8080
    - curl -X POST http://localhost:8080/readings/import - load the sample data once

# not used yet - next to learn
    - blueprints - app.py still carries factory + handlers + health + import + index in one file, splitting it is the next cohesion step
    - formatted streaming - iter_all_readings yields raw db tuples which the export indexes positionally, yielding dicts would close the leak
    - the csv stage decision - keep .pkl → csv → postgres (audit artifact) or go direct, decide before writing more importer code
    - tests for the export generator and init_db.py - the two untested paths left
    - authentication - all endpoints are open on purpose in this local learning setup
