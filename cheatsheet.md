# /f/Intern_Training — Repeated Pieces Cheat Sheet

**One line:** the functions, keywords, methods, commands, SQL, config/env shapes, and patterns that repeat across the entire `/f/Intern_Training/` repo — OOP, file/CSV, PostgreSQL, Flask API, pandas/Excel, Mosquitto + MQTT + mTLS + Paho, Machine Sensor API capstone, cron_jobs/partitioning, log_rotation, and RegEx.

**Not:** a generic tutorial. Only what actually shows up repeatedly in this repo's files.

**Scope of this repo (the tracks the cheat sheet is built from):**
- `OOP/` — inheritance types + encapsulation
- `File_Handling/` — read/write/append + CSVManager
- `Database_Connection/` — early `Postgremanager` + first Flask API
- `Conversion/` — pandas → Excel pipeline
- `MQTT/` — Mosquitto broker, mTLS chain, Paho client demo
- `MQTT/Machine_Sensor_API/` — capstone Flask + PostgreSQL API (+ tests)
- `cron_jobs/` — APScheduler + PostgreSQL range partitioning
- `log_rotation/` — rotating JSON logging
- `RegEx/` — matcher functions + practice tasks
- `SQL_Commands/` — DDL/DQL/DML/DCL/TCL + partitioning notes
- `Linux/` — command-line basics
- root `.md` — the step-by-step live-monitoring architecture built from all of the above

---

## 0. Cross-track repeated patterns (appears in more than one track)

These are the things you end up writing the same way in several folders:

### 1) Fail-fast config from `.env`
Used in capstone `config.py`, `Database_Connection/setup.py`, `cron_jobs/config.py`.

```python
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")                # or load_dotenv() in cron_jobs

REQUIRED_ENV_VARS = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD", "DB_SCHEMA"]
_missing = [name for name in REQUIRED_ENV_VARS if not os.getenv(name)]
if _missing:
    raise RuntimeError(
        "Missing required environment variables: " + ", ".join(_missing)
        + ". Copy .env.example to .env and fill in the values."
    )
```

Repeated detail:
- Capstone uses a helper `_get_int(name, default=None)` that raises `RuntimeError` on bad int.
- `Database_Connection/setup.py` uses `_get_int(name)` (no default).
- `cron_jobs/config.py` reads straight `os.getenv` without the helper.

### 2) Parameterized SQL rule
Stated in `SQL_Commands/SQL_readme.md`, enforced in capstone services, `Database_Connection/setup.py`, `cron_jobs/scheduler.py`.

- `%s` placeholders for every data value.
- f-strings only for identifiers (schema/table/column names).
- `execute_values` for batch inserts (capstone importer uses 5000).

### 3) Transaction shape that repeats
Used in `Database_Connection/setup.py`, capstone services, `cron_jobs/scheduler.py`, `cron_jobs/setup.py`.

```python
connection = get_connection()                 # or db.get_connection()
try:
    with connection.cursor() as cursor:
        cursor.execute(sql, values)
    connection.commit()
except Exception:
    connection.rollback()
    raise
finally:
    connection.close()
```

Variation:
- Capstone: `with db.cursor() as cursor:` (pool context manager, no explicit close).
- Cron jobs: bare `get_connection()` + explicit `commit/rollback/close`.
- `CREATE DATABASE` is the exception: must use `autocommit = True` and connect to `postgres` first.

### 4) `CREATE DATABASE` special case
Repeated in `Database_Connection/setup.py`, `cron_jobs/setup.py`.

```python
connection = get_connection(database="postgres")
connection.autocommit = True
try:
    cursor.execute(f"CREATE DATABASE {DB_NAME}")
except psycopg2.errors.DuplicateDatabase:
    # already exists — fine
finally:
    connection.close()
```

Lesson repeated in training doc §3.3 and §3.12: `CREATE DATABASE` cannot run inside a transaction.

### 5) `try/except AttributeError` guard on demo calls
Repeated in every OOP demo file (`Single_inheritance.py`, `Multiple_inheritance.py`, `MultiLevel_inheritance.py`, `Hierarchical_inheritance.py`, `Hybrid_inheritance.py`, `Encapsulation.py`).

```python
phone = Smartphone("iPhone", "12 Pro", "1234", "SecretApp")
try:
    phone.show_details()
    phone.check_battery_health()
except AttributeError as e:
    print(f"Error: {e}")
```

This is required by the OOP exercise even when the call cannot really fail — it marks the stage the lesson was learned at.

### 6) File open + per-mode error handling
Repeated in `File_Handling/Handle.py`.

```python
try:
    with open(nf, "w") as cf:
        cf.write("This is a new file")
except FileNotFoundError:
    print("the file doesn't exist, first create a file")

try:
    with open(nf, "x") as cf:
        print("file created")
except FileExistsError:
    print("file already exist, create another one")

try:
    with open(nf, "a") as cf:
        cf.write("\nThis is a new line which is added earlier")
except Exception as e:
    print(f"the file error occured {e}")

try:
    with open(nf, "r+") as cf:
        print(cf.read())
except Exception as e:
    print(f"The file is not find {e}")
```

 repeated detail:
- `"x"` mode = fail loudly if file already exists.
- Dict-based CSV (`csv.DictReader`/`DictWriter`) is preferred over index-based because reordering columns cannot silently corrupt row handling.

### 7) `logging.exception` in every error path
Repeated in MQTT demo callbacks, capstone services, importer, cron_jobs.

```python
except Exception as e:
    logger.exception("...: %s", e)
```

Repeated lesson: one bad callback/message never kills the loop silently.

### 8) JSON-per-line logging for machines
Repeated in `log_rotation/rotation.py`, capstone `utils/logger.py` (text format but same rotating-file idea), `cron_jobs/logging_config.py`.

```python
from logging.handlers import RotatingFileHandler

file_handler = RotatingFileHandler(
    filename=LOG_FILE,
    maxBytes=10 * 1024 * 1024,     # 10 MB in production; 2 KB in the demo
    backupCount=10,                 # demo uses 10; capstone uses 5
    encoding="utf-8",
)
```

Repeated detail:
- `logger.propagate = False` stops double-printing through the root logger.
- `if logger.handlers: return` guards against duplicate handler attachment on re-import.
- Demo uses unix-epoch timestamp in JSON; capstone uses `%(asctime)sZ` text format.

### 9) `sys.path` injection in tests and standalone scripts
Repeated in `tests/conftest.py`, every test file, `Assigned_Tasks.py`-style tools.

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
```

### 10) `if __name__ == "__main__":` entry point
Repeated in almost every `.py` file in the repo.

---

## 1. OOP — repeated pieces (`OOP/`)

### Inheritance files (one per type)
- `Single_inheritance.py`
- `Multiple_inheritance.py`
- `MultiLevel_inheritance.py`
- `Hierarchical_inheritance.py`
- `Hybrid_inheritance.py`
- `Encapsulation.py`

### Repeated Python OOP keywords/attributes
- `class`
- `def __init__(self, ...)`
- `self`
- `self.name` — public
- `self._Code` — protected by convention
- `self.__battery_health` — private via name mangling; accessible as `_Smartphone__battery_health`
- `try/except AttributeError`

### MRO pattern that repeats
`Son(Mother, Father)` → Python searches parents left to right.

### Encapsulation levels (from `Encapsulation.py`)
```python
class Smartphone:
    def __init__(self, name, model, Code, HiddenApp):
        self.name = name
        self.model = model
        self._Code = Code
        self._HiddenApp = HiddenApp
        self.__battery_health = "100%"

    def show_details(self):
        print(f"Name: {self.name}, Model: {self.model}, Code: {self._Code}, Hidden App: {self._HiddenApp}")

    def check_battery_health(self):
        print(f"Battery health of {self.name} is {self.__battery_health}")

    def __privatecodes(self):
        print(f"Code of {self.name} is {self._Code}")
```

---

## 2. File / CSV — repeated pieces (`File_Handling/`)

### Mode pattern
- `"w"` — write (overwrite)
- `"x"` — create if not exists, fail if exists
- `"a"` — append
- `"r+"` — read/write

### `CSVManager` repeated methods (`Csv_Handling.py`)
- `write_csv(dt)` — header from `list(dt[0].keys())`, `csv.DictWriter.writeheader()` + `writerows(dt)`
- `read_csv()` — `csv.DictReader`, `list(rd)`
- `append_csv(dt)` — re-read existing fieldnames first, then append
- `count_rows()` — `len(list(rd))`

Repeated detail:
- `append_csv()` re-reads the existing header before writing so appends never drift out of column order.
- Hard-coded absolute path `r"F:\Intern_Training\dataaaa.csv"` is a known portability debt noted in the training doc.

---

## 3. PostgreSQL / Database_Connection — repeated pieces

### `Postgremanager` class (`Database_Connection/setup.py`)
Repeated methods:
- `connect(dbname=None)` — reuse check: `if self.conn and not self.conn.closed and self.conn.info.dbname == target_db: return`
- `create_db()` — connect to `postgres`, `autocommit = True`, `CREATE DATABASE`
- `create_schema()` — `CREATE SCHEMA IF NOT EXISTS`
- `create_table()` — `CREATE TABLE IF NOT EXISTS`
- `insert_employee(data)`, `fetch_all_employees()`, `update_employee(email, data)`, `delete_employee(email)`

### Repeated SQL DDL shapes
```sql
CREATE DATABASE {DB_NAME};

CREATE SCHEMA IF NOT EXISTS {DB_SCHEMA};

CREATE TABLE IF NOT EXISTS {DB_SCHEMA}.{TABLE_NAME} (
    id SERIAL PRIMARY KEY,
    machine_name VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS {DB_SCHEMA}.{TABLE_NAME} (
    id SERIAL,
    unix_ts BIGINT NOT NULL,
    PRIMARY KEY (id, unix_ts)
) PARTITION BY RANGE (unix_ts);
```

Repeated constraint keywords:
- `PRIMARY KEY`
- `UNIQUE`
- `NOT NULL`
- `DEFAULT`
- `FOREIGN KEY ... REFERENCES ... ON DELETE CASCADE`
- `SERIAL` / `BIGSERIAL`
- `TIMESTAMPTZ`

### Repeated SQL command categories (`SQL_Commands/SQL_readme.md`)
- DDL: `CREATE`, `DROP`, `ALTER`, `TRUNCATE`
- DQL: `SELECT`, `FROM`, `WHERE`, `GROUP BY`, `HAVING`, `DISTINCT`, `ORDER BY`
- DML: `INSERT`, `UPDATE`, `DELETE`
- DCL: `GRANT`, `REVOKE`
- TCL: `BEGIN TRANSACTION`, `COMMIT`, `ROLLBACK`, `SAVEPOINT`

### Repeated extra commands used in this repo
- `RETURNING` — get back inserted/updated row
- `ON CONFLICT DO NOTHING` — duplicate-safe insert
- `ON CONFLICT DO UPDATE` — upsert
- `LIMIT` / `OFFSET` — pagination
- `MIN` / `MAX` / `AVG` — aggregates
- `execute_values` — batch insert
- `rowcount` — did an UPDATE/DELETE actually match?
- `autocommit` — needed for `CREATE DATABASE`

### Repeated "not used yet" SQL (from `SQL_readme.md`)
- Joins
- `GROUP BY` / `HAVING` in real code
- Window functions (`OVER`, `PARTITION BY`, `ROW_NUMBER`)
- `EXPLAIN ANALYZE`

### Partitioning repeated pieces (`SQL_readme.md` + `cron_jobs/`)
- `PARTITION BY RANGE`
- partition column must be in the primary key → composite `PRIMARY KEY (id, unix_ts)`
- `_default` partition as safety net
- partition pruning
- dropping old data = `DROP TABLE` on one child partition, not batched `DELETE`

---

## 4. First Flask API — repeated pieces (`Database_Connection/main.py`)

### Repeated Flask shape
```python
from flask import Flask, jsonify, request
from flask.views import MethodView
from setup import Postgremanager

app = Flask(__name__)
db = Postgremanager()

class EmpView(MethodView):
    def get(self, email=None): ...
    def post(self): ...
    def put(self, email): ...
    def delete(self, email): ...

app.add_url_rule("/employees", view_func=EmpView.as_view("employees"))
app.add_url_rule("/employees/<email>", view_func=EmpView.as_view("employee_detail"))

if __name__ == "__main__":
    try:
        db.create_db()
        db.create_schema()
        db.create_table()
        print("Starting Employee API server...")
        app.run(debug=False)
    except Exception as e:
        print(f"Failed to start server: {e}")
```

### Repeated response envelope (early API)
```python
{"status": "success", "data": ...}
{"status": "error", "message": "..."}
```

### Repeated learned facts
- `POST` accepts a single object or a list.
- Validation lives in the route; SQL lives in the manager class.
- Browser can only speak GET — POST/PUT/DELETE need `curl`/Postman/JS `fetch`.

---

## 5. pandas / Excel — repeated pieces (`Conversion/Excel.py`)

### Repeated pipeline shape
```python
df = pd.read_csv("work.csv")
df["Date"] = pd.to_datetime(df["Date"], format="%Y-%m-%d %I-%p")
df["Split_out_the_string"] = df["Symbol"].apply(list)
df["Unix_timestamp"] = df["Date"].astype("int64") // 10**6
df["Day"] = df["Date"].dt.day
df["Month"] = df["Date"].dt.month
df["Year"] = df["Date"].dt.year
df["Hours"] = df["Date"].dt.hour
df["Minutes"] = df["Date"].dt.minute
df["seconds"] = df["Date"].dt.second
df = df.fillna(0)
df["Date"] = df["Date"].dt.strftime("%Y-%m-%d %I-%p")
```

### Repeated Excel writer shape
```python
with pd.ExcelWriter(fn, engine="openpyxl") as wt:
    df.to_excel(wt, index=False, sheet_name="Sheet1")
    ws = wt.sheets["Sheet1"]
    for col in ws.columns:
        max_len = max(len(str(c.value)) for c in col if c.value is not None)
        col_let = col[0].column_letter
        ws.column_dimensions[col_let].width = max(max_len + 3, 10)
```

Repeated detail:
- `df.to_dict(orient="records")` to print every row as a dict.
- Date round-trip must use the exact format string both ways.
- Known typo incident: `Minues` → fixed to `Minutes`.

---

## 6. Mosquitto + MQTT + mTLS + Paho — repeated pieces (`MQTT/`)

### Broker service commands (Windows)
```text
net start mosquitto
mosquitto -c mosquitto.conf
net stop mosquitto
net stop mosquitto && net start mosquitto
```

### Repeated broker config concepts
- `listener 8883`
- `cafile`, `certfile`, `keyfile`
- `require_certificate true`
- `use_identity_as_username true`
- `allow_anonymous false`
- `max_connections`, `global_max_connections`, `global_max_clients`

### Repeated OpenSSL chain commands (order matters)
```text
openssl genrsa -des3 -out ca.key 2048
openssl req -new -x509 -out ca.crt -key ca.key -days 365
openssl genrsa -out server.key 2048
openssl req -new -out server.csr -key server.key -subj "/CN=domain"
openssl x509 -req -out server.crt -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -days 365 -extfile san.cnf -extensions v3_req
openssl genrsa -out client.key 2048
openssl req -new -out client.csr -key client.key -subj "/CN=client1"
openssl x509 -req -out client.crt -in client.csr -CA ca.crt -CAkey ca.key -CAcreateserial -days 360
```

### Repeated SAN config idea
- OpenSSL 3.x requires SAN.
- `san.cnf`: `[v3_req]` → `subjectAltName = @alt_names` → `IP.1`, `IP.2`, `DNS.1 = localhost`.
- IP change → edit `san.cnf` + regenerate `server.crt` only.

### Repeated terminal test commands
```text
mosquitto_sub --cafile ca.crt --cert client.crt --key client.key -h 10.58.166.132 -p 8883 -t test
mosquitto_pub --cafile ca.crt --cert client.crt --key client.key -h 10.58.166.132 -p 8883 -t test -m "hello there"
```

### Repeated Paho client shape (`MQTT/Python/mqttdemo.py`)
```python
import logging
import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)

class MQTTClient:
    def __init__(self):
        try:
            self.br = "localhost"
            self.port = 8883
            self.topic = "test/topic"
            self.msg = "Hello, MQTT!"
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="P1")
            self.client.enable_logger()
            self.client.tls_set(
                ca_certs="C:/Program Files/Mosquitto/ca.crt",
                certfile="C:/Program Files/Mosquitto/client.crt",
                keyfile="C:/Program Files/Mosquitto/client.key",
            )
            self.client.username_pw_set("user", "userpass")
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            self.client.on_publish = self.on_publish
            self.client.on_subscribe = self.on_subscribe
            self.client.on_disconnect = self.on_disconnect
        except Exception as e:
            logger.exception("Error occurred during initialization: %s", e)
```

### Repeated Paho methods
- `connect(host, port)`
- `subscribe(topic)` → returns `(res, mid)`
- `publish(topic, msg)` → returns object with `.rc`
- `loop_forever()` / `loop_start()`
- `is_connected()` before `disconnect()`
- `disconnect()`

### Repeated callback signatures (Paho v2)
```python
def on_connect(client, userdata, flags, reason_code, properties): ...
def on_subscribe(client, userdata, mid, reason_codes, properties): ...
def on_publish(client, userdata, mid, reason_code, properties): ...
def on_message(client, userdata, message): ...
def on_disconnect(client, userdata, disconnect_flags, reason_code, properties): ...
```

### Repeated Paho checks
- `reason_code.is_failure` in `on_connect`
- `res != mqtt.MQTT_ERR_SUCCESS` for subscribe
- `res.rc != mqtt.MQTT_ERR_SUCCESS` for publish
- `message.payload.decode("utf-8")` with `UnicodeDecodeError` → `repr(message.payload)`

### Repeated MQTT error taxonomy
- `ConnectionRefusedError`
- `ssl.SSLCertVerificationError`
- reason codes 0/1/2/3/4/5/7/8/9/14
- `MQTT_ERR_NO_CONN`, `MQTT_ERR_PROTOCOL`, `MQTT_ERR_SUCCESS`

### Repeated "not used yet" MQTT
- QoS 0/1/2
- retained messages
- last will and testament
- persistent sessions
- MQTT 5 properties

---

## 7. Machine Sensor API capstone — repeated pieces (`MQTT/Machine_Sensor_API/`)

This is the biggest repeated-pattern block in the repo because the test suite, services, routes, config, schema, utils, and `app.py` all reinforce the same shapes.

### Repeated project layout
```text
app.py
config.py
wsgi.py
errors.py
database/
  connection.py
  schema.py
routes/
  machine_routes.py
  reading_routes.py
services/
  machine_service.py
  reading_service.py
  pickle_importer.py
utils/
  validation.py
  logger.py
init_db.py
tests/
  conftest.py
  test_app_flow.py
  test_error_handlers.py
  test_pickle_importer.py
  test_services.py
  test_validation.py
```

### Repeated config keys (`config.py`)
```python
DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, DB_SCHEMA
DB_POOL_MIN = _get_int("DB_POOL_MIN", 2)
DB_POOL_MAX = _get_int("DB_POOL_MAX", 10)
DB_CONNECT_TIMEOUT = _get_int("DB_CONNECT_TIMEOUT", 5)
DB_STATEMENT_TIMEOUT_MS = _get_int("DB_STATEMENT_TIMEOUT_MS", 15000)
DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data")))
IMPORT_BATCH_SIZE = _get_int("IMPORT_BATCH_SIZE", 5000)
IMPORT_FILE_NAME = os.getenv("IMPORT_FILE_NAME", "pickle_files_28_03_2025/all_topics_20250328-114500.pkl")
DEFAULT_PAGE_SIZE = _get_int("DEFAULT_PAGE_SIZE", 1000)
GENERIC_DB_ERROR = "A database error occurred. Please try again later."
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
```

### Repeated error types (`errors.py` + `database/connection.py`)
```python
class ValidationError(ValueError):
    pass

class DatabaseError(Exception):
    pass

class ConflictError(DatabaseError):
    pass

class RelatedResourceNotFoundError(DatabaseError):
    pass
```

Repeated mapping:
- `ValidationError` → 400
- `ConflictError` → 409
- `RelatedResourceNotFoundError` → 400
- `DatabaseError` → 500
- unexpected `Exception` → 500

### Repeated DB access patterns (`database/connection.py`)
```python
db = DatabaseManager()

with db.cursor() as cursor:
    cursor.execute(sql, values)
    row = cursor.fetchone()

with db.connection(commit=False) as connection:
    with closing(connection.cursor(name=...)) as cursor:
        cursor.itersize = chunk_size
        cursor.execute(sql, values)
        for row in cursor:
            yield row

connection = db.get_connection()
```

### Repeated `DatabaseManager` API
- `db.get_connection()`
- `db.connection(commit=True/False)`
- `db.cursor()`
- `db.create_database()`
- `db.create_schema()`
- `db.create_tables()`
- `db.close()`

### Repeated schema (`database/schema.py`)
```sql
CREATE SCHEMA IF NOT EXISTS {DB_SCHEMA};

CREATE TABLE IF NOT EXISTS {DB_SCHEMA}.machines (
    id SERIAL PRIMARY KEY,
    machine_name VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS {DB_SCHEMA}.sensor_readings (
    id BIGSERIAL PRIMARY KEY,
    machine_id INTEGER NOT NULL REFERENCES {DB_SCHEMA}.machines(id) ON DELETE CASCADE,
    sensor_tag VARCHAR(50) NOT NULL,
    sensor_value NUMERIC NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS {DB_SCHEMA}.import_batches (
    id SERIAL PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL,
    file_hash CHAR(64) NOT NULL UNIQUE,
    records_inserted INTEGER NOT NULL DEFAULT 0,
    records_skipped INTEGER NOT NULL DEFAULT 0,
    imported_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

### Repeated indexes (`schema.py`)
```sql
CREATE INDEX IF NOT EXISTS idx_sensor_readings_machine_timestamp
    ON {DB_SCHEMA}.sensor_readings (machine_id, timestamp);

CREATE INDEX IF NOT EXISTS idx_sensor_readings_sensor_tag
    ON {DB_SCHEMA}.sensor_readings (sensor_tag);

CREATE INDEX IF NOT EXISTS idx_sensor_readings_timestamp
    ON {DB_SCHEMA}.sensor_readings (timestamp);
```

### Repeated reading service shared pieces (`services/reading_service.py`)
```python
READING_SELECT = "id, machine_id, sensor_tag, sensor_value, timestamp"

def utc_z(value):
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
```

Repeated service methods:
- `add_reading(machine_id, sensor_tag, sensor_value, timestamp)`
- `get_reading(reading_id)`
- `get_readings(machine_id=None, sensor_tag=None, from_time=None, to_time=None, limit=None, offset=None)`
- `get_readings_export(machine_id=None, sensor_tag=None, from_time=None, to_time=None, chunk_size=1000)` — generator
- `update_reading(reading_id, machine_id=None, sensor_tag=None, sensor_value=None, timestamp=None)`
- `delete_reading(reading_id)`
- `get_statistics(machine_id=None, sensor_tag=None, from_time=None, to_time=None)`
- `_build_reading_filters(...)`
- `_format_reading(row)`

### Repeated service error-translate pattern
```python
except psycopg2.errors.UniqueViolation:
    raise ConflictError("...") from None

except psycopg2.errors.ForeignKeyViolation:
    raise RelatedResourceNotFoundError("...") from None

except DatabaseError:
    raise

except Exception as error:
    raise DatabaseError(f"Failed to ...: {error}") from error
```

### Repeated route shape (`routes/machine_routes.py`, `routes/reading_routes.py`)
```python
class MachineView(MethodView):
    def get(self, machine_id=None): ...
    def post(self): ...
    def put(self, machine_id): ...
    def delete(self, machine_id): ...

app.add_url_rule("/machines", view_func=MachineView.as_view("machines"), methods=["GET", "POST"])
app.add_url_rule("/machines/<int:machine_id>", view_func=MachineView.as_view("machine_detail"), methods=["GET", "PUT", "DELETE"])
```

### Repeated reading routes
- `GET /readings`, `POST /readings`
- `GET /readings/<int:reading_id>`, `PUT`, `DELETE`
- `GET /readings/export`
- `GET /readings/statistics`

### Repeated app routes
- `GET /` → index
- `GET /health` → 200/503
- `POST /readings/import` → pickle import

### Repeated validation helpers (`utils/validation.py`)
```python
validate_machine_id(value)
validate_sensor_tag(value)
validate_timestamp(value)
validate_from_to_order(from_time, to_time)
machine_id_from_query()
sensor_tag_from_query()
timestamp_from_query(name)
pagination_from_query()
```

Repeated validation detail:
- `validate_machine_id` accepts positive int or numeric string → int; rejects 0/negative/non-numeric.
- `validate_timestamp` parses ISO 8601 with `Z` → `+00:00` replacement.
- `pagination_from_query` uses `DEFAULT_PAGE_SIZE` default.

### Repeated pickle importer pieces (`services/pickle_importer.py`)
```python
class PickleImporter:
    def __init__(self, batch_size=IMPORT_BATCH_SIZE):
        self.batch_size = batch_size
        self.machine_ids = {}

    def import_directory(self, directory): ...
    def import_file(self, file_path): ...
    def _get_file_hash(self, file_path): ...
    def _is_already_imported(self, file_hash): ...
    def _convert_to_csv(self, file_path): ...
    def _import_csv(self, csv_path, file_path, file_hash): ...
```

Repeated pickle payload shape:
- `data[machine_name]` is a list of readings.
- Each reading: `{"ST": sensor_tag, "TS": unix_timestamp, "VR": [value]}`.
- `VR[0]` is the numeric value.

Repeated importer behaviors:
- `.pkl → CSV → PostgreSQL`.
- SHA-256 file hash ledger in `import_batches` prevents re-import.
- Batch insert with `execute_values`, `page_size=self.batch_size`.
- Row-level skip for bad tag/timestamp/non-numeric value.
- `records_inserted` / `records_skipped` returned.
- Empty/blank snapshot → 0 records, continues.

### Repeated logger setup (`utils/logger.py`)
```python
logger = logging.getLogger("machine_sensor_api")
logger.setLevel(LOG_LEVEL)
logger.propagate = False

if not logger.handlers:
    formatter = logging.Formatter("%(asctime)sZ | %(levelname)s | %(name)s | %(message)s")
    formatter.converter = time.gmtime
    console_handler = logging.StreamHandler()
    console_handler.setLevel(LOG_LEVEL)
    console_handler.setFormatter(formatter)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=10_000_000, backupCount=5, encoding="utf-8")
    file_handler.setLevel(LOG_LEVEL)
    file_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
```

### Repeated `app.py` skeleton
- `create_app()` factory
- `@app.before_request` / `@app.after_request` for request timing
- 8 error handlers: 404, 405, 400, `ValidationError`, `ConflictError`, `RelatedResourceNotFoundError`, `DatabaseError`, `Exception`
- `add_url_rule` + `MethodView.as_view`
- `waitress.serve(app)` in `__main__`

### Repeated test shapes (`tests/`)
- `FakeCursor(results, rowcount, fail_with)` — `execute`, `fetchone`, `fetchall`, `close`
- `FakeDB` seam + `patched_services` monkeypatch of `db` in each service module
- `client` fixture from `create_app()`, `app.config["TESTING"] = True`
- importer `snapshot` fixture: tiny pickle in `{"Machine A": [{"ST":..., "TS":..., "VR":[...]}], ...}` shape
- `sys.path.insert(0, str(Path(__file__).resolve().parent.parent))` in every test file

### Repeated test counts
- `test_validation.py` (20)
- `test_error_handlers.py` (8)
- `test_services.py` (10)
- `test_app_flow.py` (9)
- `test_pickle_importer.py` (6)
- Total: 53 tests

### Repeated capstone lessons (from training doc §3.8–§3.10)
- Drop unprovable unique constraint `(machine_id, sensor_tag, timestamp)` → use `import_batches` hash ledger.
- Cast aggregates `::float8` so statistics return JSON numbers, not strings.
- Shared filter builder `_build_reading_filters()` replaces triplicated `WHERE 1 = 1` surgery.
- Shared validators in `utils/validation.py`.
- `connect_timeout=5`, `statement_timeout=15000`.
- `TIMESTAMPTZ` everywhere.
- `init_db.py` for DDL, not at boot.
- Waitress + `wsgi.py` instead of Flask dev server.

---

## 8. cron_jobs / partitioning — repeated pieces (`cron_jobs/`)

### Repeated project layout
```text
cron_jobs/
  config.py
  db.py
  logging_config.py
  scheduler.py
  setup.py
  .env
```

### Repeated config (`cron_jobs/config.py`)
```python
DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, DB_SCHEMA
TABLE_NAME = "timestamp_data"
TEN_MINUTES = 600
```

### Repeated db helper (`cron_jobs/db.py`)
```python
def get_connection(database=None):
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=database or DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )
```

### Repeated scheduler shape (`cron_jobs/scheduler.py`)
```python
from apscheduler.schedulers.background import BlockingScheduler

scheduler = BlockingScheduler()
scheduler.add_job(run_timestamp_job, "cron", minute="*/1", id="insert_timestamp")
scheduler.add_job(run_partition_job, "cron", minute="*/10", id="create_partition")
scheduler.start()
```

Repeated job functions:
- `insert_current_timestamp()` — `int(time.time())`, insert, commit, `ON CONFLICT` not needed because partition + PK handles it
- `create_partition(unix_ts)` — compute current + next 10-minute window, `CREATE TABLE IF NOT EXISTS ... PARTITION OF ... FOR VALUES FROM (%s) TO (%s)`
- `run_timestamp_job()`, `run_partition_job()`, `run_scheduler()`

Repeated partitioning detail:
- partition name: `{TABLE_NAME}_{window_start}`
- creates current + next window so a partition always exists before its first insert
- `IF NOT EXISTS` makes re-runs idempotent

### Repeated cron_jobs SQL
```sql
CREATE DATABASE {DB_NAME};

CREATE SCHEMA IF NOT EXISTS {DB_SCHEMA};

CREATE TABLE IF NOT EXISTS {DB_SCHEMA}.{TABLE_NAME} (
    id SERIAL,
    unix_ts BIGINT NOT NULL,
    PRIMARY KEY (id, unix_ts)
) PARTITION BY RANGE (unix_ts);
```

### Repeated logging_config shape (`cron_jobs/logging_config.py`)
```python
def configure_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    if logger.handlers:
        return logger
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    file_handler = RotatingFileHandler(filename=LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=10, encoding="utf-8")
    console_handler = logging.StreamHandler(sys.stdout)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger
```

Repeated detail:
- Root logger, not a named logger.
- `apscheduler` quieted to `WARNING`.
- `configure_logging()` called at module import time.

### Repeated APScheduler vs schedule comparison (from `cronjobs_readme.md`)
| Feature | APScheduler | schedule |
|---|---|---|
| Complexity | Feature-rich, production-grade | Lightweight, simple API |
| Triggers | Cron, interval, date, calendar | Interval-based only |
| Persistence | Yes (SQL, MongoDB, Redis, SQLite) | No |
| Concurrency | Thread/process/async executors | Single-threaded by default |
| Best for | Production apps, web frameworks, complex schedules | Quick scripts, prototypes, simple recurring tasks |

### Repeated cron expression fields
```text
* * * * *
minutes, hours, day of month, month, day of week
```

### Repeated "not used yet" in cron_jobs
- No test coverage
- No graceful shutdown beyond `KeyboardInterrupt`
- `db.py` still uses bare `print` for connection failure, not the configured logger

---

## 9. log_rotation — repeated pieces (`log_rotation/`)

### Repeated file (`log_rotation/rotation.py`)
One hybrid handler:
- every record formatted as one-line JSON (unix-epoch timestamp, level, logger name, message, exception block when present)
- written to rotating file chain + console

### Repeated classes/functions
- `JsonFormatter(logging.Formatter)` — `format(self, record)`
- `configure_logging()` — builds and returns the wired logger

### Repeated JSON log shape
```json
{
  "timestamp": record.created,
  "level": record.levelname,
  "logger": record.name,
  "message": record.getMessage(),
  "exception": "..."   // only when record.exc_info is set
}
```

### Repeated patterns (same as cross-track #7 + #8)
- `RotatingFileHandler`
- `logger.propagate = False`
- `if logger.handlers: return`
- One logging setup per application, wired in one place

---

## 10. RegEx — repeated pieces (`RegEx/`)

### Repeated import
```python
import re
```

### Repeated functions (`regex_readme.md` + `Assigned_Tasks.py`)
- `re.search()` — first match anywhere
- `re.match()` — match from the beginning
- `re.fullmatch()` — entire string must match
- `re.findall()` — all matches
- `re.finditer()` — all matches as iterator
- `re.sub()` — replace
- `re.split()` — split by pattern

### Repeated pattern catalog (from `regex_readme.md`)
- `(?<!\d)\d{5}(?!\\d)` — exact 5 digits, not part of longer number
- `[a-z]` / `[A-Z]` — lowercase-only / uppercase-only
- `([a-zA-Z]+)(\\d+)` — letters then numbers (grouping)
- `\bA\w*` — starts with A
- `\w*Z\b` — ends with Z
- `\d+` — digits only
- `\D+` — no digits
- `^[A-Z][a-z]+$`
- `^\d{5}$`
- `^[^0-9]+$`

### Repeated practice-task patterns (`Assigned_Tasks.py`)
```python
re.fullmatch(r"EMP\d{4}", emp_id)
re.fullmatch(r"M\d{3}", machine_id)
r"(?P<phone>(?<![A-Za-z0-9])\d{10}(?![A-Za-z0-9]))"
r"Machine\s+(M\d+)\s+temperature\s+(\d+(?:\.\d+)?)"
r"Machine\s+(?P<machine_id>M\d+)\s+temperature\s+(?P<temperature>\d+(?:\.\d+)?)\s+status\s+(?P<status>\w+)"
r"Machine:\s*(?P<machine_id>M\d+)\s*\|\s*Temperature:\s*(?P<temperature>\d+(?:\.\d+)?)\s*C\s*\|\s*Status:\s*(?P<status>\w+)"
r"ERROR\s+Machine\s+(?P<machine_id>M\d+)\s+(?P<error_message>.+)"
re.sub(r"[^a-zA-Z0-9]", "_", text)
re.split(r"[,;|:]+", text)
r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
r"(?P<date>\b\d{2}[-/]\d{2}[-/]\d{4}\b)"
```

### Repeated regex takeaways (from `regex_readme.md`)
- `^abc` (anchor) ≠ `[^abc]` (negation).
- Lookarounds match a position, not a character.
- Named groups + `groupdict()` for log parsing.
- `re.sub()` for data cleaning.
- Regex is a validation/extraction tool, not a puzzle toy.

### Repeated known issues (from training doc §3.13)
- Concepts file literally named `.py` hides it from most tooling.
- `regex_readme.md` drifted from code: documents `([a-zA-Z]+)(\\d+)` grouping while code uses two separate `findall` calls.

---

## 11. Linux — repeated pieces (`Linux/`)

### Repeated commands (`Linux/README.md`, `Learning_linux.md`)
```text
pwd   ls   cd   mkdir   touch
cp    mv   rm   cat     less
head  tail grep find    wc
sort  uniq explorer.exe .
```

### Repeated command meanings (from `Learning_linux.md`)
- `pwd` — where you are
- `ls` — list files in directory
- `cd` — change directory
- `mkdir` — create directories
- `touch` — create a new file
- `cp` — copy
- `mv` — move
- `rm` — delete
- `cat` — display file
- `less` — read file
- `head` — first lines
- `tail` — last lines
- `grep` — search text
- `find` — find files
- `wc` — count lines/words
- `sort` — sort data
- `uniq` — remove duplicates
- `explorer.exe .` — open current folder location in explorer (WSL trick)

### Repeated terminal concepts
- command prompt — built-in tool to communicate with the computer
- PowerShell — more advanced command-line tool for automation/scripting
- admin mode for system changes
- `powercfg /batteryreport`
- `sfc /scannow`
- `DISM /RestoreHealth`

---

## 12. Root-level “everything that repeats across tracks” summary

### Repeated project bootstrap shape
1. `.env` + fail-fast config check
2. DB connect (or connect to `postgres` for `CREATE DATABASE`)
3. `CREATE SCHEMA IF NOT EXISTS`
4. `CREATE TABLE IF NOT EXISTS`
5. Long-running process or request handler
6. Structured logging
7. `if __name__ == "__main__":` entry point

### Repeated SQL identity rule
- identifiers via f-string
- data via `%s`
- batch via `execute_values`
- duplicates via ledger/constraint decided on provenance, not assumption

### Repeated logging identity
- one logger setup per app
- rotating file handler
- `propagate = False`
- `logging.exception` in every error path

### Repeated Python identity
- `with` for resources
- `try/except` around plausible failure points
- `raise X from None` for user-facing errors
- `if __name__ == "__main__":`
- `sys.path` injection when a file expects to be run from elsewhere

### Repeated engineering-habit identity (from training doc §6)
1. secrets → `.env` + fail-fast config
2. connections → pool + context managers that always return the connection
3. SQL → parameterized everywhere; identifiers out of value positions
4. failure handling → typed exceptions, rollback, `rowcount`, `logging.exception`
5. time-bounded failure → `connect_timeout` + `statement_timeout`
6. external calls → validate immediate return code AND async confirmation
7. data integrity → enforce only provable claims; protect the rest at ingestion
8. structure → routes/services/database layering
9. readability → shared filter builder, not `WHERE 1 = 1`
10. versioned change discipline → build parallel copy, verify both chains, promote only then
11. review the live tree, not the archive
12. principles over fashion (KISS wins)
13. documentation — if a README would embarrass you in review, the code is not ready
14. explain it simply — non-technical first section
15. consolidate, don't accumulate — one README per topic

---

*Built from the repeated pieces in: `OOP/*`, `File_Handling/*`, `Database_Connection/*`, `Conversion/*`, `MQTT/*`, `MQTT/Machine_Sensor_API/*`, `cron_jobs/*`, `log_rotation/*`, `RegEx/*`, `SQL_Commands/*`, `Linux/*`, and root `.md` + `TRAINING_DOCUMENTATION.md`.*
