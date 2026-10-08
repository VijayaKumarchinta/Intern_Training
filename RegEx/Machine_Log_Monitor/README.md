# Machine Log Monitor

This project reads a machine log, stores only `ERROR` entries in PostgreSQL,
creates a CSV report, and checks the log every minute.

# How the application works

1. `scheduler.py` starts the monitoring job every minute.
2. `MachineLogReader` reads one line from `logs/machine.log`.
3. `parse_machine_log()` extracts the timestamp, level, machine ID, and message.
4. `jobs.py` stores the entry if its level is `ERROR`; other levels are skipped
   and logged.
5. `report.py` creates the CSV report after an error entry is processed.
6. The scheduler stops after the last line has been read.

If saving an error or creating its report fails, the reader returns to that line
so it can be tried again on the next run. A database constraint prevents the
same error from being inserted more than once.

# Machine log format

Each non-empty line should follow this format:

```text
YYYY-MM-DD HH:MM:SS | LEVEL | Machine MACHINE_ID | MESSAGE
```

Example:

```text
2026-10-08 10:16:55 | ERROR | Machine M102 | Motor overheating
2026-10-08 10:18:40 | INFO | Machine M101 | Sensor failure
```

The parser recognizes `DEBUG`, `INFO`, `WARNING`, `ERROR`, and `CRITICAL`.
Only `ERROR` entries are stored. Timestamps are treated as UTC. Blank lines
are skipped, and invalid lines or dates are logged and skipped.

# Project files and functions

## `config.py`

- `BASE_DIR` - finds the application folder so file paths work regardless of
  the terminal's current folder.
- `load_dotenv(...)` - loads database settings from `.env`.
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` - provide the
  PostgreSQL connection settings.
- `DB_SCHEMA` - selects the schema where machine errors are stored.
- `MACHINE_LOG_FILE` - identifies `logs/machine.log`.
- `REPORT_FILE` - identifies `reports/machine_error_report.csv`.

## `log_reader.py`

### `MachineLogReader`

Reads the machine log one line at a time and remembers its file position.

- `__init__(file_path=MACHINE_LOG_FILE)` - sets the input file and initializes
  the line counter.
- `open()` - opens the input file when it is first needed.
- `read_next_line()` - returns the line number, line text, and whether it is the
  last line; returns `None` when the file ends.
- `retry_last_line()` - moves back to the last line after a processing failure.
- `close()` - closes the input file when reading is finished.

## `log_parser.py`

- `LOG_PATTERN` - describes the expected layout of a machine log line.
- `parse_machine_log(line)` - checks a line and returns its timestamp, Unix
  timestamp, level, machine ID, and error message; returns `None` for blank,
  malformed, or invalid-date lines.

## `db.py`

- `get_connection(database=None)` - opens a PostgreSQL connection using the
  settings from `config.py`; an optional database name is used during setup.

## `machine_insert.py`

- `store_errors(errors)` - inserts parsed `ERROR` entries, counts inserted rows
  and duplicates, commits successful changes, and rolls back on failure.

## `report.py`

- `SELECT_QUERY` - selects machine ID, timestamp, and error message from the
  configured schema, ordered by timestamp.
- `generate_report()` - fetches the saved errors and writes them to the CSV
  report.

## `jobs.py`

- `reader` - keeps the reader's position between scheduled runs.
- `monitor_machine_logs()` - reads and processes one line; stores `ERROR`
  entries, logs why other lines are skipped, and reports whether more lines
  remain.

## `scheduler.py`

- `create_scheduler()` - schedules the monitoring job to run once per minute
  and stops when the log has been processed.
- `main()` - configures logging and starts the scheduler.

## `setup_db.py`

- `create_database()` - creates the configured database or logs that it already
  exists.
- `create_schema()` - creates the configured schema if it does not exist.
- `create_table()` - creates the machine-errors table and duplicate constraint.

When run directly, this file calls the setup functions in database, schema,
and table order.

## `logging_config.py`

- `configure_logging()` - sends application messages to the terminal and
  `logs/app.log`.
- `RotatingFileHandler` - limits the size of the application log by rotating
  older log files.

# Python methods and statements used

Each item gives what it does and why this project uses it.

- `Path(...).resolve()` - finds an absolute path so input and output files can
  be located reliably.
- `.parent` - gets a path's containing folder, for example to create the report
  folder.
- `os.getenv(...)` - reads configuration values without placing database
  settings directly in the source code.
- `re.compile(...)` - prepares the log-line pattern once so it can be reused.
- `.fullmatch(...)` - checks that the complete line follows the expected format.
- `.groupdict()` - collects the named fields captured by the regular expression.
- `datetime.strptime(...)` - converts the timestamp text to a datetime.
- `.replace(tzinfo=timezone.utc)` - marks the machine event timestamp as UTC.
- `.timestamp()` - converts the datetime to Unix time for database storage.
- `open(...)` and `.readline()` - open the machine log and read one line at a
  time.
- `.tell()` and `.seek(...)` - save and restore the file position for look-ahead
  and retry.
- `.rstrip(...)` and `.strip()` - remove line endings or surrounding whitespace
  where needed.
- `int(...)` - stores the Unix timestamp as an integer.
- `Path(...).mkdir(...)` - creates the report folder if it is missing.
- `csv.writer(...)` - writes report values using CSV formatting.
- `writer.writerow(...)` - writes the report's column headings.
- `writer.writerows(...)` - writes the database results to the report.
- `len(...)` - counts report records for the log message.
- `with` - ensures files and database cursors are cleaned up when their work is
  complete.
- `raise` - passes failures back to the caller so a failed log line can be
  retried.

# SQL commands and database features used

- `CREATE DATABASE` - creates the application database.
- `CREATE SCHEMA` - creates a namespace for the machine errors table.
- `CREATE TABLE` - defines the columns used to store each error.
- `INSERT INTO` - saves parsed error entries.
- `SELECT ... FROM ... ORDER BY` - retrieves saved errors in timestamp order
  for the report.
- `ON CONFLICT ... DO NOTHING` - ignores an error that already exists instead
  of inserting a duplicate.
- `UNIQUE (machine_id, timestamp, error_message)` - identifies duplicate
  machine error entries.
- `NOT NULL` - requires the important event fields to have values.
- `SERIAL` - generates a unique ID for each stored row.
- `TIMESTAMPTZ` - stores the event time with timezone information.
- `BIGINT` - stores the Unix timestamp as an integer.
- `commit()` - saves successful database changes.
- `rollback()` - cancels changes when a database operation fails.
- `autocommit` - allows the database-creation command to run outside a
  transaction.

# Database configuration

Create a `.env` file in this folder:

```text
DB_HOST=localhost
DB_PORT=5432
DB_NAME=machine_monitor_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_SCHEMA=machine_monitoring_schema
```

The table stores the machine ID, event timestamp, Unix timestamp, and error
message. The unique key is `(machine_id, timestamp, error_message)`.

# Report

The report is written to:

```text
reports/machine_error_report.csv
```

It contains `Machine ID`, `Timestamp`, and `Error Message` columns. It is
regenerated after an `ERROR` entry is processed.

# Run the application

From this folder, install the dependencies, set up the database, and start the
scheduler:

```powershell
pip install -r requirements.txt
python setup_db.py
python scheduler.py
```

Application messages are shown in the terminal and written to `logs/app.log`.
