# Python Internship Training — Repository Guide

**Author:** Chinta Vijayakumar
**Company:** Triniti Advanced Software Labs Pvt Ltd
**Period:** August – September 2026

This is the top-level index of my training work. Every file or folder name below is a **clickable link** — it opens the actual file in this repository (works on GitHub and in VS Code with Ctrl+Click).

---

## Repository map

| Path | What it contains |
|---|---|
| [OOP/](OOP/) | Object-oriented programming: all 5 inheritance types + encapsulation |
| [File_Handling/](File_Handling/) | Text file modes and CSV handling with a class |
| [Database_Connection/](Database_Connection/) | PostgreSQL with Python + Flask REST API (employees) |
| [Conversion/](Conversion/) | CSV → pandas → Excel data-processing pipeline |
| [MQTT/](MQTT/) | Mosquitto broker, TLS/mTLS, Paho Python client, Machine Sensor API |
| [Linux/](Linux/) | Basic Linux commands and Unix vs Linux notes |
| [TRAINING_DOCUMENTATION.md](TRAINING_DOCUMENTATION.md) | One-month engineering documentation: timeline, architecture decisions, error log, lessons |
| [PRODUCTION_COMPARISON.md](PRODUCTION_COMPARISON.md) | My code reviewed against 10 production-grade open source repos — pattern-by-pattern gaps, scorecard, upgrade plan |

---

## 1. OOP — [OOP/README.md](OOP/README.md)

Six examples, each wrapped in `try/except AttributeError` as required.

| File | Topic |
|---|---|
| [Single_inheritance.py](OOP/Single_inheritance.py) | One parent → one child |
| [Multiple_inheritance.py](OOP/Multiple_inheritance.py) | One child, multiple parents |
| [MultiLevel_inheritance.py](OOP/MultiLevel_inheritance.py) | Grandparent → parent → child chain |
| [Hierarchical_inheritance.py](OOP/Hierarchical_inheritance.py) | Multiple children, one parent |
| [Hybrid_inheritance.py](OOP/Hybrid_inheritance.py) | Combination of the above patterns |
| [Encapsulation.py](OOP/Encapsulation.py) | Public / protected (`_`) / private (`__`, name-mangled) members |

---

## 2. File Handling — [File_Handling/README.md](File_Handling/README.md)

| File | What it demonstrates |
|---|---|
| [Handle.py](File_Handling/Handle.py) | File modes `w`, `x`, `a`, `r+` with exception handling |
| [Csv_Handling.py](File_Handling/Csv_Handling.py) | `CSVManager` class — write, read, append, count rows via `csv.DictReader`/`DictWriter` |

---

## 3. PostgreSQL + Flask API — [Database_Connection/README.md](Database_Connection/README.md)

| File | What it demonstrates |
|---|---|
| [setup.py](Database_Connection/setup.py) | `Postgremanager` class — connect, create database / schema / table, employee CRUD, commit + rollback |
| [main.py](Database_Connection/main.py) | Flask `MethodView` REST API on `/employees` (GET / POST / PUT / DELETE) |
| [Screenshots/](Database_Connection/Screenshots/) | API test results |

Endpoints exposed by [main.py](Database_Connection/main.py):

```text
GET     /employees
GET     /employees/<email>
POST    /employees
PUT     /employees/<email>
DELETE  /employees/<email>
```

---

## 4. Data Conversion — [Conversion/README.md](Conversion/README.md)

| File | What it demonstrates |
|---|---|
| [Excel.py](Conversion/Excel.py) | pandas pipeline: date parsing, day/month/year/time extraction, Unix timestamp, string split, `fillna`, Excel export |
| [work.csv](Conversion/work.csv) | Source data (Date, Symbol, OHLCV — string, date-time, float columns) |
| [Work_sample_processed.xlsx](Conversion/Work_sample_processed.xlsx) | Processed output workbook |

---

## 5. MQTT — [MQTT/README.md](MQTT/README.md)

### Learning notes

| File | What it covers |
|---|---|
| [Learning.md](MQTT/Learning.md) | Mosquitto broker: start/stop/restart, config file, connection limits, TLS/mTLS certificate chain, SAN |
| [Python/python_Learning.md](MQTT/Python/python_Learning.md) | Paho client: Callback API v2, TLS setup, callbacks, loops, return codes, error types |

### Code

| File | What it demonstrates |
|---|---|
| [Python/mqttdemo.py](MQTT/Python/mqttdemo.py) | `MQTTClient` class — TLS on port 8883, username/password, all 5 callbacks, Paho logging, return-code checks for `subscribe()`/`publish()`, safe disconnect with `finally` |

### Machine Sensor API (Flask + PostgreSQL) — [readme.md](MQTT/Machine_Sensor_API/readme.md)

The main project: manages machines and sensor readings, with bulk import of pickle snapshots.

| File | Purpose |
|---|---|
| [app.py](MQTT/Machine_Sensor_API/app.py) | Entry point — registers all routes, `/health`, `/readings/import` (bulk pickle import) |
| [config.py](MQTT/Machine_Sensor_API/config.py) | `.env` loading, `DATA_DIR`, schema/table/index SQL |
| [requirements.txt](MQTT/Machine_Sensor_API/requirements.txt) | Flask, psycopg2-binary, python-dotenv |
| [Machine_Sensor_API_Postman_Test_Suite_Updated.json](MQTT/Machine_Sensor_API/Machine_Sensor_API_Postman_Test_Suite_Updated.json) | Postman collection covering CRUD, filters, statistics, validation, cascade delete |
| [database/connection.py](MQTT/Machine_Sensor_API/database/connection.py) | `DatabaseManager` — `get_connection()`, `create_database()`, `create_schema()`, `create_tables()`, shared `db` instance, `DatabaseError` |
| [database/models.py](MQTT/Machine_Sensor_API/database/models.py) | `Machine` and `SensorReading` data shapes |
| [routes/machine_routes.py](MQTT/Machine_Sensor_API/routes/machine_routes.py) | `MachineView` — machines CRUD endpoints |
| [routes/reading_routes.py](MQTT/Machine_Sensor_API/routes/reading_routes.py) | `ReadingView` + `ReadingStatisticsView` — readings CRUD, filters (`machine_id`, `sensor_tag`, `from`, `to`), MIN/MAX/AVG statistics |
| [services/machine_service.py](MQTT/Machine_Sensor_API/services/machine_service.py) | Machine SQL operations |
| [services/reading_service.py](MQTT/Machine_Sensor_API/services/reading_service.py) | Reading SQL operations + statistics |
| [services/pickle_importer.py](MQTT/Machine_Sensor_API/services/pickle_importer.py) | Bulk importer — reads **all 25** `.pkl` snapshots in [data/pickle_files_28_03_2025/](MQTT/Machine_Sensor_API/data/pickle_files_28_03_2025/), auto-creates machines, batch inserts of 5000 with `ON CONFLICT DO NOTHING` |
| [Machine_Sensor_API.zip](MQTT/Machine_Sensor_API.zip) | Packaged copy of the project as shared over email |

API endpoints (details in the [project readme](MQTT/Machine_Sensor_API/readme.md)):

```text
GET    /health
GET    /machines            POST /machines
GET    /machines/<id>       PUT /machines/<id>       DELETE /machines/<id>
GET    /readings            POST /readings
GET    /readings/<id>       PUT /readings/<id>       DELETE /readings/<id>
GET    /readings/statistics
POST   /readings/import     (bulk import of all pickle files)
```

---

## 6. Linux — [Linux/README.md](Linux/README.md)

| File | What it covers |
|---|---|
| [Learning_linux.md](Linux/Learning_linux.md) | Navigation and file commands (`pwd`, `ls`, `cd`, `cp`, `mv`, `rm`, `grep`, `find`, …), Unix vs Linux |

---

## Suggested reading order

```text
OOP basics            →  OOP/*.py
File handling         →  File_Handling/Handle.py, Csv_Handling.py
PostgreSQL            →  Database_Connection/setup.py
REST API              →  Database_Connection/main.py
Data conversion       →  Conversion/Excel.py
MQTT + Mosquitto      →  MQTT/Learning.md, MQTT/Python/mqttdemo.py
Machine Sensor API    →  MQTT/Machine_Sensor_API/readme.md (then app.py)
```
