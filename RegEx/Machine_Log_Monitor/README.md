# Machine Log Monitor — End-to-End Flow

This document describes exactly what happens when `scheduler.py` is executed,
line by line, from process startup to termination, including the supporting
functions it calls.

---

## 1. What `scheduler.py` does

`scheduler.py` wires everything together using **APScheduler's `BlockingScheduler`**.
It schedules one recurring job that runs once per minute and stops the scheduler
when the log has been fully consumed.

### `main()`

1. Calls `configure_logging()` — written at module import time in
   `logging_config.py` (`configure_logging()` is invoked at the bottom of the
   file), so logging is configured **before** the scheduler starts.
2. Calls `create_scheduler()`, which returns a configured but **not yet running**
   `BlockingScheduler`.
3. Logs `"Machine log monitoring started (interval: 1 minute)"`.
4. Calls `scheduler.start()` — this blocks the process and starts the event loop.

### `create_scheduler()`

1. Creates a `BlockingScheduler`.
2. Defines `run_monitoring()`, the job function:
   - Calls `monitor_machine_logs()` and captures the boolean it returns.
   - If the return value is `False` (`has_more_lines` is false), logs
     `"Machine log processing complete."` and shuts the scheduler down with
     `scheduler.shutdown(wait=False)` — this is how the scheduler **exits**.
   - Otherwise (more lines remain), returns `True` and the scheduler waits for
     the next interval.
3. Registers the job:
   - `trigger="interval"`, `minutes=1` — runs the job every minute.
   - `id="machine_log_monitor"`, `replace_existing=True` — idempotent
     (re-scheduling the same job replaces it).
   - `max_instances=1` — only one instance at a time.
   - `coalesce=True` — if the scheduler is down when the next interval fires,
     it merges the missed runs into a single execution instead of running the
     job many times in a row.
4. Returns the scheduler.

**Important:** the job does **not** run forever. It stops after the log's last
line has been read. The `is_last_line` flag returned by the reader drives this
behavior.

---

## 2. One scheduled run — `monitor_machine_logs()`

`jobs.py` holds **one shared module-level reader**:

```python
reader = MachineLogReader()
```

This reader object keeps the file position between scheduled runs. Each job
invocation processes **one line** from the log:

1. `reader.read_next_line()`:
   - Opens the log if not already open.
   - Saves the current file position (`tell()`), reads the next line, then
     peeks one character further ahead to determine whether another line
     follows.
   - Returns `(line_number, line, is_last_line)` on success.
   - Returns `None` when the file has reached EOF (the file has no more
     lines at all).
2. If the result is `None`, the reader is closed and `False` is returned —
   meaning "no more lines remain".
3. If a line was read:
   - `parse_machine_log(line)` tries to extract the fields.
   - If parsing fails on a non-blank line → warning log, line skipped.
   - If the line is blank → info log, line skipped.
   - If parsed successfully and `level == "ERROR"`:
     - `store_errors([parsed])` writes the row into the DB.
     - `generate_report()` rebuilds the CSV from the DB.
   - If parsed successfully but `level != "ERROR"` → info log, line skipped.
4. A `try/except` wraps parsing/storing; on any exception the reader seeks
   back to the last line (`retry_last_line()`) so the line is attempted again
   on the next run.
5. After handling, if `is_last_line` is true, the reader is closed and
   `False` is returned ("no more lines remain"). Otherwise `True` is returned
   ("there are more lines").

---

## 3. Reading the log — `log_reader.py`

`MachineLogReader` is the low-level line reader.

- `__init__(file_path=MACHINE_LOG_FILE)` — defaults to
  `logs/machine.log` from `config.py`.
- `open()` — opens the file with UTF-8 encoding if not open yet.
- `read_next_line()` — the core:
  - `self.file.tell()` → `line_position` (where the current line starts).
  - `readline()` reads the line; if nothing returned, EOF → returns `None`.
  - `line_number` is incremented, `last_line_position` is saved.
  - A second `readline()` peeks ahead to know if another line exists.
  - `seek(next_line_position)` restores the position so the line just read is
    still where the caller can process it.
  - Returns `(line_number, line_without_newline, is_last_line)`.
- `retry_last_line()` — seeks back to `last_line_position`, decrements the
  line counter, and clears the saved position (so the next `read_next_line`
  can re-read it fresh). Used after a processing failure.
- `close()` — closes the file and clears the position.

The `tell()`/`seek()` peek pattern is what tells the caller whether it has
reached the very last line of the file, which is what makes the scheduler
decide to shut down.

---

## 4. Parsing the log — `log_parser.py`

`parse_machine_log(line)` validates and extracts fields from one line.

- `LOG_PATTERN` is a compiled regex with named groups:
  - `timestamp` — `YYYY-MM-DD HH:MM:SS`
  - `level` — one of `DEBUG | INFO | WARNING | ERROR | CRITICAL`
  - `machine_id` — `Machine M\d+` (e.g. `Machine M102`)
  - `message` — everything after the machine ID
- `fullmatch` is used, so the **entire** line must match — partial matches are
  rejected.
- The timestamp is parsed with `strptime` and forced to UTC via
  `.replace(tzinfo=timezone.utc)`; a bad date makes the function return `None`.
- Returns a dict:
  ```python
  {
      "timestamp": datetime(UTC),
      "unix_timestamp": int(epoch),
      "machine_id": "M102",
      "level": "ERROR",
      "error_message": "Motor overheating"
  }
  ```
  or `None` for blank, malformed, or invalid-date lines.

---

## 5. Storing errors — `machine_insert.py`

`store_errors(errors)` inserts parsed ERROR entries into the database.

- Opens a connection via `db.get_connection()`.
- For each parsed error, executes an `INSERT ... ON CONFLICT (machine_id,
  timestamp, error_message) DO NOTHING` into
  `{DB_SCHEMA}.machine_errors`.
- `cursor.rowcount == 1` → counted as newly inserted; otherwise counted as a
  duplicate (already stored).
- `connection.commit()` on success; `connection.rollback()` on failure, which
  also logs and re-raises.
- `connection.close()` in `finally`.

The `UNIQUE` constraint `(machine_id, timestamp, error_message)` is what
prevents duplicate insertion of the exact same error.

---

## 6. Generating the report — `report.py`

`generate_report()` rebuilds the CSV file after each error is stored.

- Runs
  `SELECT machine_id, timestamp, error_message FROM {DB_SCHEMA}.machine_errors
  ORDER BY timestamp;`
- Creates `reports/` if missing (`Path(REPORT_FILE).parent.mkdir(...)`).
- Writes `reports/machine_error_report.csv` with header
  `["Machine ID", "Timestamp", "Error Message"]` and one row per DB record.
- On failure, logs and re-raises; closes the connection in `finally`.

The report is **not** regenerated on every job run — only when an ERROR entry
is actually processed. This keeps it lightweight.

---

## 7. Database layer — `db.py`

`get_connection(database=None)` opens a `psycopg2` connection from the settings
in `.env` (`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`). An
optional `database` argument is used during setup — when `setup_db.py` runs it
connects to the default `postgres` database first, then creates the real one.

---

## 8. Database setup — `setup_db.py`

Run **once** before `scheduler.py`. It creates the schema in this order:

1. `create_database()` — connects to the `postgres` database, creates
   `{DB_NAME}` with `autocommit` on, logs if it already exists.
2. `create_schema()` — `CREATE SCHEMA IF NOT EXISTS {DB_SCHEMA}`.
3. `create_table()` — `CREATE TABLE IF NOT EXISTS {DB_SCHEMA}.machine_errors`
   with columns `id`, `machine_id`, `timestamp`, `unix_timestamp`,
   `error_message`, plus the `UNIQUE (machine_id, timestamp, error_message)`
   constraint.

---

## 9. End-to-end run (what you see on the console)

1. `configure_logging()` runs; messages go to the terminal and to
   `logs/app.log` (rotating at 10 MB, 10 backups).
2. `main()` builds and shows the "started" log line, then blocks on
   `scheduler.start()`.
3. **Every ~60 seconds**: `run_monitoring()` → `monitor_machine_logs()`:
   - Reads **one** line from `logs/machine.log`.
   - Parses it. Only `ERROR` lines are stored.
   - Stores errors into the DB and rewrites the CSV report.
   - If there are more lines, returns `True`; the scheduler waits for the next
     minute and runs again.
   - If the line was the **last** line, the reader closes and returns `False`.
     The job logs `"Machine log processing complete."` and shuts the scheduler
     down (`wait=False`), so the process exits.

Example console output:

```text
INFO  | 2026-10-09 12:00:00 | Machine log monitoring started (interval: 1 minute)
INFO  | 2026-10-09 12:00:00 | Saved ERROR log entries: 1; duplicates skipped: 0
INFO  | 2026-10-09 12:00:00 | Report generated | Records=1
INFO  | 2026-10-09 12:00:00 | Machine log processing complete.
```

## 10. Key design notes / gotchas

1. **One-shot per scheduler lifetime.** The scheduler does **not** tail the
   log forever. Once the reader reaches the last line, it closes the file and
   exits. If `machine.log` gains new lines later, they are not picked up
   until the scheduler is restarted.
2. **Reader state persists across runs.** Because `jobs.py` creates one
   `MachineLogReader` at module level, the file position is preserved from
   one scheduled invocation to the next. The scheduler relies on this to
   continue from where the previous run left off.
3. **Retry behavior.** If storing or parsing fails, `retry_last_line()` puts
   the reader back on that line so the next run retries it. Only after a
   successful processing is `is_last_line` honored.
4. **Duplicates are safe.** The `UNIQUE (machine_id, timestamp,
   error_message)` constraint plus `ON CONFLICT DO NOTHING` guarantees an
   identical error is never inserted twice.
5. **Report regeneration is error-driven.** The CSV is rewritten only when an
   ERROR line is processed, never on a purely-INFO/WARNING run.
6. **Timestamps are UTC.** The parser marks every parsed timestamp as UTC
   before converting to Unix time for storage.
7. **Setup must happen first.** `setup_db.py` creates the database, schema,
   and table with the required constraints before `scheduler.py` can store
   anything.

---

## 11. Setup & run

```bash
pip install -r requirements.txt
python setup_db.py        
python scheduler.py   
```

Project files involved:

| File | Role |
|---|---|
| `scheduler.py` | APScheduler entry; schedules & stops the job |
| `jobs.py` | One-line-per-run processing; owns the shared reader |
| `log_reader.py` | Low-level `tell()`/`seek()` line reader |
| `log_parser.py` | Regex + timestamp parsing |
| `machine_insert.py` | Error → DB insert with duplicate guard |
| `report.py` | DB → CSV report |
| `db.py` | PostgreSQL connection |
| `config.py` | Paths + `.env` settings |
| `logging_config.py` | Terminal + rotating file logger |
| `setup_db.py` | One-time DB scaffolding |

---

## 13. Future changes — if you switch to live / high-frequency logs

The current design assumes **static, bounded sample data**: the log is
fully written before the scheduler starts, the scheduler reads it once,
and it exits. The three "cons" of that design don't matter for static
data. If you later switch to live or bursty logs, apply these changes
exactly.

### 1. Per-run DB connection (open a new PostgreSQL connection every
   job run) → batch insert in one transaction

**File:** `machine_insert.py`
**Change:** Replace the per-row `cursor.execute()` loop (currently inside
   `with connection.cursor() as cursor:`) with an `executemany()` call,
   and move `connection.commit()` **outside** the `with` block.

**Before:**
```python
        with connection.cursor() as cursor:
            for error in errors:
                cursor.execute(...)
                if cursor.rowcount == 1:
                    inserted += 1
                else:
                    ignored_duplicates += 1

        connection.commit()
```

**After:**
```python
        with connection.cursor() as cursor:
            params = [
                (
                    error["machine_id"],
                    error["timestamp"],
                    error["unix_timestamp"],
                    error["error_message"],
                )
                for error in errors
            ]
            cursor.executemany(sql, params)
            inserted = ...   # count inserted / duplicate rows from
                             # cursor.rowcounts as needed

        connection.commit()   # single commit for the whole batch
```

**Rationale:** one round-trip to the DB for the whole batch instead of
   one statement per line. Keep a single `connection` and a single
   `commit` so a partial failure can still `rollback()` the entire
   batch.

### 2. One line per run (misses bursts faster than 1 minute)
   → buffer lines between runs

**File:** `jobs.py`
**Change:** Add an in-memory buffer and a drain loop so a run consumes
   every buffered line before reading new file content.

**Before (module-level state):**
```python
reader = MachineLogReader()


def monitor_machine_logs():
    result = reader.read_next_line()
    if result is None:
        reader.close()
        return False

    line_number, line, is_last_line = result

    try:
        parsed = parse_machine_log(line)
        if parsed is None:
            if line.strip():
                logger.warning(
                    "Skipping line %d: invalid log format or timestamp",
                    line_number,
                )
            else:
                logger.info("Skipping line %d: blank line", line_number)
        elif parsed["level"] == "ERROR":
            store_errors([parsed])
            generate_report()
        else:
            logger.info(
                "Skipping line %d: level is %s; only ERROR is stored",
                line_number,
                parsed["level"],
            )
    except Exception:
        reader.retry_last_line()
        raise

    if is_last_line:
        reader.close()
        return False

    return True
```

**After:**
```python
reader = MachineLogReader()
_buffer = []


def _drain_buffer():
    """Yield buffered lines first, then read fresh from the file."""
    while _buffer:
        line_number, line, is_last_line = _buffer.pop(0)
        yield line_number, line, is_last_line

    while True:
        result = reader.read_next_line()
        if result is None:
            reader.close()
            return
        yield result


def monitor_machine_logs():
    for line_number, line, is_last_line in _drain_buffer():
        try:
            parsed = parse_machine_log(line)
            if parsed is None:
                if line.strip():
                    logger.warning(
                        "Skipping line %d: invalid log format or timestamp",
                        line_number,
                    )
                else:
                    logger.info("Skipping line %d: blank line", line_number)
            elif parsed["level"] == "ERROR":
                store_errors([parsed])
                generate_report()
            else:
                logger.info(
                    "Skipping line %d: level is %s; only ERROR is stored",
                    line_number,
                    parsed["level"],
                )
        except Exception:
            reader.retry_last_line()
            raise

    return not is_last_line
```

**How it fixes the gap:** burst lines are queued into `_buffer` during
   the first run's `read_next_line()`; the next run's `_drain_buffer()`
   consumes all of them before reading new file content. The
   `is_last_line` flag from the **actual last file line** still drives
   shutdown, so lines written after the log is "finished" are still
   picked up on restart.

### 3. Also consider for live/bursty data

| Concern | Fix |
|---|---|
| Many small DB writes | Batch `INSERT` with `executemany()` per tick (see 13.1). |
| High volume + low latency | Keep a shared DB connection across ticks, or use a connection pool. |
| Persistent restart safety | Save the reader's `last_line_position` to a state file so a crash doesn't re-process lines. |

### 4. When to apply these

Apply these changes only when the requirement changes from static
sample data to live/bursty logs. For the current data, the design is
already correct and optimal.