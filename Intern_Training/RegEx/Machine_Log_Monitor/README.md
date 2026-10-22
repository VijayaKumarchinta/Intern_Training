# Machine Log Monitor (RegEx) — Intern Training

**Source:** `RegEx/Machine_Log_Monitor/README.md`, `RegEx/Machine_Log_Monitor_v3/README.md`, `RegEx/Machine_Log_Monitor/alternatives.md`

> A scheduler-driven log processor: reads `logs/machine.log`, parses each line with a compiled regex, stores only `ERROR` lines into PostgreSQL, and regenerates a CSV report.

---

## 1. Machine Log Monitor v1 — the flow

**What the file does in one sentence:** A standalone log monitor that tails `logs/machine.log` one line at a time and persists ERROR entries to PostgreSQL.

### 1.1 What `scheduler.py` does

`scheduler.py` wires everything together using **APScheduler's `BlockingScheduler`**. It schedules one recurring job that runs once per minute and stops the scheduler when the log has been fully consumed.

`main()`:
1. Calls `configure_logging()` — written at module import time in `logging_config.py`, so logging is configured **before** the scheduler starts.
2. Calls `create_scheduler()`, which returns a configured but **not yet running** `BlockingScheduler`.
3. Logs `"Machine log monitoring started (interval: 1 minute)"`.
4. Calls `scheduler.start()` — blocks the process and starts the event loop.

`create_scheduler()`:
1. Creates a `BlockingScheduler`.
2. Defines `run_monitoring()`, the job function:
   - Calls `monitor_machine_logs()` and captures the boolean it returns.
   - If the return value is `False` (`has_more_lines` is false), logs `"Machine log processing complete."` and shuts the scheduler down with `scheduler.shutdown(wait=False)`.
   - Otherwise returns `True`; the scheduler waits for the next interval.
3. Registers the job:
   - `trigger="interval"`, `minutes=1`
   - `id="machine_log_monitor"`, `replace_existing=True`
   - `max_instances=1`
   - `coalesce=True`

**Important:** the job does **not** run forever. It stops after the log's last line has been read. The `is_last_line` flag returned by the reader drives this behaviour.

---

### 1.2 One scheduled run — `monitor_machine_logs()`

`jobs.py` holds **one shared module-level reader**: `reader = MachineLogReader()`. This reader object keeps the file position between scheduled runs. Each job invocation processes **one line** from the log:

1. `reader.read_next_line()`:
   - Opens the log if not already open.
   - Saves the current file position (`tell()`), reads the next line, then peeks one character further ahead to determine whether another line follows.
   - Returns `(line_number, line, is_last_line)` on success.
   - Returns `None` when the file has reached EOF.
2. If the result is `None`, the reader is closed and `False` is returned.
3. If a line was read:
   - `parse_machine_log(line)` tries to extract the fields.
   - If parsing fails on a non-blank line → warning log, line skipped.
   - If the line is blank → info log, line skipped.
   - If parsed successfully and `level == "ERROR"`:
     - `store_errors([parsed])` writes the row into the DB.
     - `generate_report()` rebuilds the CSV from the DB.
   - If parsed successfully but `level != "ERROR"` → info log, line skipped.
4. A `try/except` wraps parsing/storing; on any exception the reader seeks back to the last line (`retry_last_line()`) so the line is attempted again on the next run.
5. After handling, if `is_last_line` is true, the reader is closed and `False` is returned. Otherwise `True` is returned.

---

### 1.3 Reading the log — `log_reader.py`

`MachineLogReader` is the low-level line reader.

| Method | What it does |
|---|---|
| `__init__(file_path=MACHINE_LOG_FILE)` | defaults to `logs/machine.log` from config.py |
| `open()` | opens the file with UTF-8 encoding if not open yet |
| `read_next_line()` | the core: `tell()` → read line → peek ahead with a second `readline()` → `seek()` to restore position → returns `(line_number, line_without_newline, is_last_line)` |
| `retry_last_line()` | seeks back to `last_line_position`, decrements line counter |
| `close()` | closes the file and clears position |

The `tell()`/`seek()` peek pattern is what tells the caller whether it has reached the very last line of the file.

---

### 1.4 Parsing the log — `log_parser.py`

`parse_machine_log(line)` validates and extracts fields from one line:

- `LOG_PATTERN` is a compiled regex with named groups: `timestamp`, `level`, `machine_id`, `message`.
- `fullmatch` is used, so the **entire** line must match.
- The timestamp is parsed with `strptime` and forced to UTC via `.replace(tzinfo=timezone.utc)`; a bad date makes the function return `None`.
- Returns a dict with timestamp, unix_timestamp, machine_id, level, error_message, or `None` for blank/malformed/invalid-date lines.

---

### 1.5 Storing errors — `machine_insert.py`

`store_errors(errors)` inserts parsed ERROR entries into the database:

- Opens a connection via `db.get_connection()`.
- For each parsed error, executes `INSERT ... ON CONFLICT (machine_id, timestamp, error_message) DO NOTHING` into `{DB_SCHEMA}.machine_errors`.
- `cursor.rowcount == 1` → counted as newly inserted; otherwise counted as duplicate.
- `connection.commit()` on success; `connection.rollback()` on failure.
- `connection.close()` in finally.

The `UNIQUE` constraint `(machine_id, timestamp, error_message)` prevents duplicate insertion.

---

### 1.6 Generating the report — `report.py`

`generate_report()` rebuilds the CSV file after each error is stored:

- Runs `SELECT machine_id, timestamp, error_message FROM {DB_SCHEMA}.machine_errors ORDER BY timestamp;`.
- Creates `reports/` if missing.
- Writes `reports/machine_error_report.csv` with header `["Machine ID", "Timestamp", "Error Message"]` and one row per DB record.
- On failure, logs and re-raises; closes connection in finally.

The report is **not** regenerated on every job run — only when an ERROR entry is actually processed.

---

### 1.7 Database layer — `db.py`

`get_connection(database=None)` opens a psycopg2 connection from settings in `.env` (`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`). An optional database argument is used during setup.

---

### 1.8 Database setup — `setup_db.py`

Run **once** before `scheduler.py`:

1. `create_database()` — connects to `postgres`, creates `{DB_NAME}` with autocommit.
2. `create_schema()` — `CREATE SCHEMA IF NOT EXISTS {DB_SCHEMA}`.
3. `create_table()` — `CREATE TABLE IF NOT EXISTS {DB_SCHEMA}.machine_errors` with columns id, machine_id, timestamp, unix_timestamp, error_message, plus the UNIQUE constraint.

---

### 1.9 End-to-end run

1. `configure_logging()` runs; messages go to terminal and to `logs/app.log` (rotating at 10 MB, 10 backups).
2. `main()` builds and shows `"started"` log line, then blocks on `scheduler.start()`.
3. **Every ~60 seconds**: `run_monitoring()` → `monitor_machine_logs()`:
   - Reads **one** line from `logs/machine.log`.
   - Parses it. Only ERROR lines are stored.
   - Stores errors into DB and rewrites CSV report.
   - If more lines, returns True; scheduler waits for next minute.
   - If last line, reader closes and returns False; job logs `"Machine log processing complete."` and shuts scheduler down.

Example console output:
```
INFO  | 2026-10-09 12:00:00 | Machine log monitoring started (interval: 1 minute)
INFO  | 2026-10-09 12:00:00 | Saved ERROR log entries: 1; duplicates skipped: 0
INFO  | 2026-10-09 12:00:00 | Report generated | Records=1
INFO  | 2026-10-09 12:00:00 | Machine log processing complete.
```

---

### 1.10 Key design notes / gotchas

1. **One-shot per scheduler lifetime.** The scheduler does **not** tail the log forever. Once the reader reaches the last line, it closes the file and exits.
2. **Reader state persists across runs.** Because `jobs.py` creates one `MachineLogReader` at module level, the file position is preserved.
3. **Retry behaviour.** If storing or parsing fails, `retry_last_line()` puts the reader back on that line.
4. **Duplicates are safe.** The UNIQUE constraint plus `ON CONFLICT DO NOTHING` guarantees an identical error is never inserted twice.
5. **Report regeneration is error-driven.** The CSV is rewritten only when an ERROR line is processed.
6. **Timestamps are UTC.** The parser marks every parsed timestamp as UTC.
7. **Setup must happen first.** `setup_db.py` creates the database, schema, and table before `scheduler.py` can store anything.

---

## 2. Setup & run

```bash
pip install -r requirements.txt
python setup_db.py
python scheduler.py
```

**Project file table:**

| File | Role |
|---|---|
| scheduler.py | APScheduler entry; schedules & stops the job |
| jobs.py | One-line-per-run processing; owns the shared reader |
| log_reader.py | Low-level `tell()`/`seek()` line reader |
| log_parser.py | Regex + timestamp parsing |
| machine_insert.py | Error → DB insert with duplicate guard |
| report.py | DB → CSV report |
| db.py | PostgreSQL connection |
| config.py | Paths + `.env` settings |
| logging_config.py | Terminal + rotating file logger |
| setup_db.py | One-time DB scaffolding |

---

## 3. Future changes — if you switch to live / high-frequency logs

The current design assumes **static, bounded sample data**. If you later switch to live or bursty logs, apply these changes:

### 1. Per-run DB connection → batch insert in one transaction

**File:** `machine_insert.py`. Replace the per-row `cursor.execute()` loop with an `executemany()` call, and move `connection.commit()` **outside** the `with` block.

### 2. One line per run → buffer lines between runs

**File:** `jobs.py`. Add an in-memory buffer and a drain loop so a run consumes every buffered line before reading new file content.

### 3. Also consider for live/bursty data

| Concern | Fix |
|---|---|
| Many small DB writes | Batch INSERT with `executemany()` per tick |
| High volume + low latency | Keep a shared DB connection across ticks, or use a connection pool |
| Persistent restart safety | Save reader's `last_line_position` to a state file |

### 4. When to apply these

Apply these changes only when the requirement changes from static sample data to live/bursty logs. For the current data, the design is already correct and optimal.

---

## 4. Machine Log Monitor v3 — improvements

**What:** The improved v3 version of the Machine Log Monitor end-to-end flow. The v3 README documents the same scheduler-driven log processing but with improvements:

- `store_errors` accepts a **list** of parsed ERROR dicts (a single dict is also accepted) and inserts them in **one transaction**, returning `(inserted, duplicates)`.
- The README uses **PowerShell-style setup commands**.
- `.env` holds credentials and is git-ignored; `config.py` refuses to start if any setting is missing.
- The project file table now includes `app.py` — Flask API (`/live/*`) + serves the `client/` dashboard.

**Key v3 improvements over v1:**
- Batch insert in one transaction (v1 called it per-element).
- `.env` + fail-fast `config.py` for credentials.
- PowerShell-style setup commands.
- `app.py` added for Flask API + dashboard serving.

**Pros:**
- One transaction for many errors → far fewer round-trips.
- Fail-fast config → obvious to debug missing settings.
- Git-ignores secrets → no credentials in source.

**Cons/drawbacks:**
- Still optimised for static, bounded data.
- No persistent reader-state file.
- Duplicate `alternatives.md` exists (v1 canonical, v3 exact duplicate — the v3 file was not carried into the consolidation).

**Use cases:**
- When batch inserts are needed and credentials should not be in source.
- When a PowerShell-based setup is preferred on Windows.

**Usage:** Same as v1, plus `.env` configuration + fail-fast config; run `setup_db.py` first; `python scheduler.py` starts monitoring.

---

## 5. Summary — v1 vs v3

| Aspect | v1 | v3 |
|---|---|---|
| store_errors | One dict per run | List of dicts, one transaction |
| Setup | Shell commands | PowerShell-style |
| Secrets | Not git-ignored | `.env` git-ignored + fail-fast config |
| Extra files | — | `app.py` (Flask API + dashboard) |

---

## 6. Alternatives

**What:** The v1 `alternatives.md` (approach comparison) is the canonical version. Its purpose is to compare the log monitor approach against alternatives and is kept as the reference; the v3 `alternatives.md` was an exact duplicate and was not carried into the consolidation.

**Pros:**
- Comparison of approaches = informed trade-off decisions.

**Cons/drawbacks:**
- Redundant duplicate files existed (v3 alternatives.md).

**Errors encountered & causes:**
- v3 `alternatives.md` was an exact duplicate of v1 → removed/kept canonical in consolidation.

**Use cases:**
- Choosing between logging approaches for a monitoring project.

**Usage:**
- Reference the v1 `alternatives.md` for approach comparison; keep only one canonical copy.

---

**Quick reference — all machine-log-monitor files**
| File | Role |
|---|---|
| scheduler.py | APScheduler entry; schedules & stops the job |
| jobs.py | One-line-per-run processing; owns the shared reader |
| log_reader.py | Low-level `tell()`/`seek()` line reader |
| log_parser.py | Regex + timestamp parsing |
| machine_insert.py | Error → DB insert with duplicate guard |
| report.py | DB → CSV report |
| db.py | PostgreSQL connection |
| config.py | Paths + `.env` settings |
| logging_config.py | Terminal + rotating file logger |
| setup_db.py | One-time DB scaffolding |

**Status:** 1 APScheduler project + READMEs for v1 and v3, runnable standalone.
