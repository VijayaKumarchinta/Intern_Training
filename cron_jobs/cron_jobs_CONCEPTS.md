# Cron Jobs, Schedulers & Table Partitioning — Intern Training

**Source:** `cron_jobs/cronjobs_readme.md`, `cron_jobs/setup.py`, `cron_jobs/db.py`, `cron_jobs/scheduler.py`, `cron_jobs/logging_config.py`

> A scheduler-based project that inserts the current Unix timestamp every minute into a **range-partitioned** PostgreSQL table and creates partitions just-in-time. Rebuilt Oct 1 from OS cron/`schedule` to APScheduler's `BlockingScheduler` with two `cron`-trigger jobs.

---

## 1. Cron jobs — what they are

**What:** A scheduled task where an OS runs automatically at a specified time interval.

- **Cron** = the service that's always running in the background, checking "is it time to do something?".
- **Cron job** = one task you told it to do at a specific time.

**Concepts learned:**
- We use cron jobs to automate tasks recursively.
- The famous 5-field cron expression: `* * * * *` → minutes | hours | day of month | month | day of week.
- Cron schedules the commands; you can execute in three ways:
  - With a Linux server using `crontab -e` with the 5-field expression.
  - In Python, using an interpreter (in-process).
  - In Windows, using Task Scheduler to trigger scripts with the python exe.
- Cron jobs can be run with bash, python, perl, php, and any binary scripts.
- In production, cron files usually revolve around: entry point, error handling, logging, environment variables, database cleanup, and clear exit behavior.

**Pros:**
- Automates recurring tasks without manual intervention.
- Works across OSes (cron on Linux, Task Scheduler on Windows).

**Cons/drawbacks:**
- OS cron is separate from your app; errors and logs are decoupled from your code.
- `schedule` (Python) has no persistence — jobs are lost on restart.

**Errors encountered & causes:**
- N/A at the cron-concept stage (partitioning errors come next).

**Use cases:**
- Daily backups, log rotation, report generation, database cleanup.
- Any periodic housekeeping.

**Usage:**
- Linux: `crontab -e` → `*/5 * * * * /path/to/script.sh`
- Windows: Task Scheduler + python.exe
- Python in-process: `schedule` module or APScheduler.

---

## 2. APScheduler — the in-process scheduler

**What:** A lightweight advanced Python in-process task scheduling tool with cron-like capabilities.

**Three triggers:**
- **DateTrigger** — one-time interval execution.
- **IntervalTrigger** — fixed time interval triggers.
- **CronTrigger** — complex scheduling based on cron expressions.

**Two scheduler types:**
- **BackgroundScheduler** — runs in the background and allows the main application to continue; ideal for long-running applications.
- **BlockingScheduler** — blocks the main thread until the scheduler is shut down; best for standalone scripts where the scheduler is the primary process.

**Project structure:**
- `cron_jobs/` — root directory
- `logs/` — storing log details
- `config.py` — configuring credentials to access the database user details
- `db.py` — imports the config file for credential details of the database; gives `get_connection(database=None)` which connects to the default postgres db when needed
- `logging_config.py` — imports pathlib for making the log path, creates a log file; log rotation done by `RotatingFileHandler` (10 MB, 10 backups)
- `scheduler.py` — the actual cron jobs process; imports connection from db, schema/table name, and ten-minute gap from config; imports logging_config
  - `insert_current_timestamp()` — inserts the timestamp with a 1-minute difference, calls `create_partition()` just before inserting
  - `create_partition()` — creates the partition for the timestamp passed to it on the basis of a 10-minute gap, named `timestamp_data_<window_start>`, `IF NOT EXISTS` makes re-runs idempotent
  - `run_timestamp_job()` — entry point of `insert_current_timestamp()`
  - `run_partition_job()` — entry point of `create_partition()`
  - `run_scheduler()` — where the actual cron jobs are done
- `setup.py` — setting up the database
  - `create_database()` — create a db with autocommit while connecting to the default db
  - `create_schema()` — creating a schema and being verified
  - `create_table()` — creating a table with id and unix_ts, doing partitions based on timestamp, plus a `_default` partition as the safety net
  - `initialize_database()` — entry point for those three functions

**Pros:**
- In-process scheduling avoids OS scheduling complexity.
- `BlockingScheduler` gives a clean, standalone continuous run.

**Cons/drawbacks:**
- `schedule` module has no persistence (jobs lost on restart) and only interval triggers.
- APScheduler offers cron/interval/date triggers + persistence + thread/process/async executors — more complexity.

**Errors encountered & causes:**
- Inserts failed with "no partition found" → row arrived before its 10-min partition → just-in-time creation + DEFAULT partition.
- `CREATE TABLE … PARTITION BY` rejected plain-`id` PK → partition column must be in the PK → composite `PRIMARY KEY (id, unix_ts)`.

**Use cases:**
- Periodic data housekeeping (timestamp logs, metrics, cache cleanup).
- Time-series tables that grow large and are purged by time range.

**Usage:**
```python
from apscheduler.schedulers.blocking import BlockingScheduler

sched = BlockingScheduler()
sched.add_job(run_timestamp_job, "cron", minute="*/1", id="insert_timestamp")
sched.add_job(run_partition_job, "cron", minute="*/10", id="create_partition")
sched.start()
```

---

## 3. APScheduler vs `schedule` module

| Feature | APScheduler | `schedule` |
|---|---|---|
| Complexity | Feature-rich, production-grade | Lightweight, simple API |
| Triggers | Cron, interval, date, calendar | Interval-based only |
| Persistence | Yes (SQL, MongoDB, Redis, SQLite) | No — jobs lost on restart |
| Concurrency | Thread/process/async executors | Single-threaded by default |
| Best for | Production apps, web frameworks, complex schedules | Quick scripts, prototypes, simple recurring tasks |

**Pros:**
- APScheduler: full trigger model + persistence + concurrency.
- `schedule`: minimal API for simple loops.

**Cons/drawbacks:**
- `schedule` has no persistence and only interval triggers.
- APScheduler is heavier and more complex.

**Errors encountered & causes:**
- Readme kept `schedule`-module remnants after the Oct 1 rewrite to APScheduler → found in the Oct 8 review; readme cleaned up.

**Use cases:**
- Use APScheduler for production/web apps and complex schedules.
- Use `schedule` for quick scripts and prototypes.

**Usage:**
- Choose APScheduler for anything beyond simple recurring tasks; prefer `cron` + `BlockingScheduler` for standalone scripts.

---

## 4. Keep-built-in functions used in the project

- **Primary Key** — for lookup purpose w.r.t. the id/unix_ts.
- `load_dotenv()` — loading of db credentials.
- `psycopg2.connect()` — connecting to the db with the env variables.
- `RotatingFileHandler` — log rotation.
- `int(time.time())` — converting float unix_timestamp to integer.
- `connection.cursor()` — start the SQL command.
- `cursor.execute()` — execute db commands.
- `logging.getLogger()` — logger name shown in terminal.
- `schedule.every(1).minute.do()` — assign automated tasks every 1 minute.
- `schedule.every(10).minutes.do()` — assign automated tasks every 10 minutes.
- `schedule.run_pending()` — check pending jobs.
- `BlockingScheduler` — for one-time continuous runnable scripts.
- `scheduler.add_job(run_timestamp_job, "cron", minute="*/1", id="insert_timestamp")`.

---

**Quick reference — all cron_jobs files**
| File | Role |
|---|---|
| setup.py | Database bootstrap |
| db.py | Postgres connection |
| config.py | Credentials |
| logging_config.py | Rotating file logger |
| scheduler.py | APScheduler entry + jobs |
| cronjobs_readme.md | Per-folder documentation |

**Status:** 1 scheduler project (APScheduler) + README, runnable standalone.
