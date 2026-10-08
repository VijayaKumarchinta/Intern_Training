# Machine Log Monitor

A Python application that reads machine log entries, extracts event details,
stores `ERROR` and `CRITICAL` events in PostgreSQL, creates a CSV report, and
runs the monitoring job on a schedule.

## How the Application Works

1. `scheduler.py` starts a job that runs every minute.
2. `MachineLogReader` reads one line from `logs/machine.log`.
3. `parse_machine_log()` checks the line and extracts its event information.
4. `jobs.py` sends `ERROR` and `CRITICAL` events to PostgreSQL.
5. `report.py` writes the stored events to a CSV file.
6. Processing stops when the reader reaches the last line.

If saving an event or creating its report fails, the reader rewinds that line.
The next scheduled run can retry it. PostgreSQL's unique constraint prevents a
retry from storing the same machine event twice.

## Machine Log Format

Each non-empty line should follow this format:

```text
YYYY-MM-DD HH:MM:SS | LEVEL | Machine MACHINE_ID | MESSAGE
```

Example:

```text
2026-10-08 10:16:55 | ERROR | Machine M102 | Motor overheating
2026-10-08 10:18:40 | INFO | Machine M101 | Sensor failure
2026-10-08 10:20:00 | CRITICAL | Machine M103 | Hydraulic system failure
```

Supported levels are `DEBUG`, `INFO`, `WARNING`, `ERROR`, and `CRITICAL`.
Timestamps are interpreted as UTC. Blank lines are ignored; malformed lines
and invalid dates are skipped.

## Classes, Functions, and Key Methods:

### `config.py`

This module provides shared configuration values used throughout the application.

| Name | Purpose |
| --- | --- |
| `BASE_DIR` | The folder containing the application files. |
| `load_dotenv(...)` | Loads settings from the `.env` file. |
| `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | PostgreSQL connection settings. |
| `DB_SCHEMA` | PostgreSQL schema containing the machine errors table. |
| `MACHINE_LOG_FILE` | Path to `logs/machine.log`. |
| `REPORT_FILE` | Path to `reports/machine_error_report.csv`. |

### `log_reader.py`

#### `MachineLogReader`

Reads the configured machine log one line at a time and tracks its current
position.

| Method | Purpose |
| --- | --- |
| `__init__(file_path=MACHINE_LOG_FILE)` | Sets the file to read and initializes the line counter. A different path can be supplied for testing. |
| `open()` | Opens the file the first time it is needed. |
| `read_next_line()` | Returns `(line_number, line_text, is_last_line)`. Returns `None` at end of file. |
| `retry_last_line()` | Moves back to the start of the last returned line so it can be processed again. |
| `close()` | Closes the file and clears its open-file state. |

`read_next_line()` removes the line ending and uses a brief look-ahead to tell
whether the returned line is the last one.

### `log_parser.py`

| Name | Purpose |
| --- | --- |
| `LOG_PATTERN` | Describes the expected timestamp, level, machine ID, and message layout. |
| `parse_machine_log(line)` | Returns a dictionary containing `timestamp`, `unix_timestamp`, `machine_id`, `level`, and `error_message`. Returns `None` for blank, malformed, or invalid-date lines. |

The timestamp is converted to a UTC datetime. The Unix timestamp is the same
event time represented as seconds since the Unix epoch.

### `db.py`

| Name | Purpose |
| --- | --- |
| `logger` | Records database connection failures. |
| `get_connection(database=None)` | Opens a PostgreSQL connection using settings from `config.py`. An optional database name lets setup connect to PostgreSQL's maintenance database while creating the application database. |

If a connection fails, the function logs the error and raises it so the caller
can handle or report the failure.

### `machine_insert.py`

| Name | Purpose |
| --- | --- |
| `store_errors(errors)` | Inserts event dictionaries into `{DB_SCHEMA}.machine_errors`. Counts inserted rows and ignored duplicates, commits on success, rolls back and re-raises on failure, and always closes the connection. |

The database constraint considers an event a duplicate when its machine ID,
timestamp, and message match an existing row.

### `report.py`

| Name | Purpose |
| --- | --- |
| `SELECT_QUERY` | Selects machine ID, timestamp, and message from the configured schema, ordered by timestamp. |
| `generate_report()` | Reads the stored events, creates the report directory if needed, writes a CSV header and rows, logs the result, and closes the database connection. |

If report generation fails, the function logs the exception and raises it to
the monitoring job.

### `jobs.py`

| Name | Purpose |
| --- | --- |
| `reader` | The `MachineLogReader` instance shared across scheduled runs so it can continue from its current file position. |
| `monitor_machine_logs()` | Reads and processes one line. Warns about non-empty invalid lines. Stores `ERROR` and `CRITICAL` events and generates the report for those events. Returns `True` when more lines remain and `False` at the end of the file. |

If storing an event or generating its report raises an error, this function asks
the reader to retry the same line, then re-raises the error.

### `scheduler.py`

| Name | Purpose |
| --- | --- |
| `create_scheduler()` | Creates the APScheduler scheduler and registers the monitoring job to run every minute. It stops the scheduler when the log is finished. |
| `main()` | Configures logging, reports that monitoring started, and starts the scheduler. It also logs when the user stops the application. |

The `if __name__ == "__main__"` block calls `main()` when this file is run
directly.

### `setup_db.py`

| Name | Purpose |
| --- | --- |
| `TABLE_NAME` | The name of the PostgreSQL table used for machine events. |
| `create_database()` | Creates the configured database, or logs that it already exists. |
| `create_schema()` | Creates the configured schema if needed. |
| `create_table()` | Creates the machine errors table and its duplicate-prevention constraint if needed. |

When run directly, the file configures logging and calls these three setup
functions in order.

### `logging_config.py`

| Name | Purpose |
| --- | --- |
| `BASE_DIR`, `LOG_DIR`, `LOG_FILE` | Identify the application folder and the `logs/app.log` file. |
| `configure_logging()` | Sets up informational logging to both the terminal and a rotating application log file. |

The module calls `configure_logging()` when imported. Application logs are
separate from machine events in `logs/machine.log`.

### Tests

`tests/test_pipeline.py` checks that the reader returns lines and detects the
end of a file, the parser extracts fields and rejects invalid dates, failed
event storage can be retried, `CRITICAL` events are stored, and reports can be
written when the configured path is a string.

`tests/test_machine_insert.py` checks that new events are inserted, duplicates
are ignored, and database errors trigger rollback and propagate to the caller.
These tests mock the database and do not need a running PostgreSQL server.

## PostgreSQL Setup

Create a `.env` file with the connection settings and schema name:

```text
DB_HOST=localhost
DB_PORT=5432
DB_NAME=machine_monitor_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_SCHEMA=machine_monitoring_schema
```

The table stores the machine ID, event timestamp, Unix timestamp, and message.
Its unique constraint uses `(machine_id, timestamp, error_message)`.

## Report

The CSV file is written to:

```text
reports/machine_error_report.csv
```

It has these columns: `Machine ID`, `Timestamp`, and `Error Message`. The report
is generated after each successfully processed `ERROR` or `CRITICAL` event.

## Run

Install dependencies, configure `.env`, create the database objects, and start
the scheduler from this folder:

```powershell
pip install -r requirements.txt
python setup_db.py
python scheduler.py
```

Application messages appear in the terminal and are written to `logs/app.log`.

## Run Tests

Run the tests from this folder:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```
