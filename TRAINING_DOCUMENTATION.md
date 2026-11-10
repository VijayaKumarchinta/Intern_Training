# Engineering Training Documentation — August to October 2026

| | |
| --- | --- |
| **Author** | Chinta Vijayakumar |
| **Company** | Triniti Advanced Software Labs Pvt Ltd |
| **Period** | 17 August 2026 � 5 November 2026 |
| **Mentor** | V. Swaroop, Technical Consultant, High Technology Practice |
| **Last reviewed** | 10 November 2026 — full self-review against the mentor email thread (17 Aug – 5 Nov), the live tree, Order & Sales Management app, and Live_dashboard architecture build; verification record in §9 |

This document records the complete training period: what was built, what was
learned, what went wrong, and which engineering habits changed along the way.
Every file reference is a clickable link to the real code in this repository.

The document is written in two layers, like every other doc in this repo:
the summary and the plain-words tables first, the precise technical detail
underneath.

---

## 1. Executive summary

The training moved from language fundamentals to a production-shaped
IIoT-style data pipeline, and is still growing after the core six weeks:

```text
Weeks 1–4   Foundations: OOP, files/CSV, PostgreSQL, first Flask API,
            pandas/Excel, Mosquitto + TLS/mTLS, Paho client mastery
Weeks 5–6   Capstone: Machine Sensor API built, hardened, then rebuilt to
            production standard, reviewed against 8 design principles,
            cleaned up with a versioned-change method (§3.8–§3.10)
Since then  Supporting tracks, each small, finished, and documented like
            production code: pandas data analysis (§3.1), git workflow (§3.2),
            Python traceback module (§3.3), a full SQL command portfolio
            (§3.4), rotating JSON logging (§3.5), APScheduler-driven table
            range partitioning (§3.6), regex practice + machine-log monitoring
            (§3.7), and the Order & Sales Management app (§3.8)
```

The capstone is [Machine_Sensor_API](MQTT/Machine_Sensor_API/Machine_Sensor_API_CONCEPTS.md):
a layered REST API managing machines and sensor readings, which bulk-imports a
**pickle snapshot of ~55,918 readings across 12 machines** into PostgreSQL
with batch inserts and a duplicate-safe import ledger.

The single biggest shift of the period: from *writing code that runs* to
*designing code that survives requests, failures, and concurrent users* —
pooled database connections returned through context managers, transactions
with rollback, parameterized queries, secrets in `.env`, time-bounded failure
(timeouts), and return-code validation on every external call.

The capstone's own story had three acts:

1. **Built (Sep 15–17):** a working layered API with bulk import (§3.7).
2. **Hardened (Sep 18–21):** honest error semantics — 409/400 instead of
   blanket 500s, real JSON numbers from statistics, row-level import
   validation (§3.9).
3. **Rebuilt, reviewed, cleaned (Sep 22–28):** a real WSGI server, connection
   pooling with timeouts, an import ledger replacing a guessed uniqueness
   rule; then an 8-principles design review (with an independent cross-check
   that caught one wrong claim); then a five-fix cleanup applied by building
   parallel versions first and promoting them only after both chains proved
   identical (§3.10).

After the capstone, the same lessons were deliberately re-applied on smaller
ground: a standalone rotating-log demo (§3.5), a scheduler-driven cron-jobs
project with PostgreSQL range partitioning (§3.6), and regex practice
(§3.7) — each one small enough to finish, documented like production code.

On 8 October the whole period was self-reviewed against the original email
assignments and the live tree; the verification record is §9.

---

## 2. Timeline of assigned work

| Date | Task | Output |
| Aug 17 | OOP: 5 inheritance types + encapsulation, exception in every example | [OOP/OOP_CONCEPTS.md](OOP/OOP_CONCEPTS.md) — 6 runnable files |
| Aug 17 | PostgreSQL: create database, schema, table | [setup.py](Database_Connection/setup.py) |
| Aug 18 | File handling: read/write/append + errors | [Handle.py](File_Handling/Handle.py), [Csv_Handling.py](File_Handling/Csv_Handling.py) |
| Aug 20 | `Postgremanager` class with CRUD + transactions | [setup.py](Database_Connection/setup.py) |
| Aug 20–21 | Excel generation → pandas DataFrame → split strings | [Excel.py](Conversion/Excel.py) |
| Aug 21 | Regex practice introduction | [Assigned_Tasks.py](RegEx/Assigned_Tasks.py) | (started) |
| Aug 24–26 | Flask API over the employee table + Mosquitto broker introduced | [main.py](Database_Connection/main.py), [mqtt_readme_CONCEPTS.md](MQTT/mqtt_readme_CONCEPTS.md) |
| Aug 24–26 | Flask API over the employee table | [main.py](Database_Connection/main.py) |
| Aug 25 | Mentor check-in: learned `__init__()` init best practice, f-strings for inline substitution, `%s` placeholder | (note) |
| Aug 25 | Mentor check-in + learned `__init__()` init best practice, format strings (f) for inline substitution, `%s` as universal placeholder | (note) |
| Aug 26 | Mentor sent two Flask APIs over the employee table + mosquitto broker learning task | (email) |
| Aug 26–31 | Mosquitto broker: service control, limits, bridge concepts | [mqtt_readme_CONCEPTS.md](MQTT/mqtt_readme_CONCEPTS.md) |
| Sep 3–7 | TLS/SSL certificate chain, SAN, 8883 listener | [mqtt_readme_CONCEPTS.md](MQTT/mqtt_readme_CONCEPTS.md) |
| Sep 8–10 | Paho client: 5 callbacks, paho logging, return-code checks | [mqttdemo.py](MQTT/Python/mqttdemo.py) |
| Sep 15–17 | Machine Sensor API + bulk pickle import | [Machine_Sensor_API_CONCEPTS.md](MQTT/Machine_Sensor_API/Machine_Sensor_API_CONCEPTS.md) |
| Sep 18–21 | Capstone hardening: 409/400 exception mapping, JSON-number statistics, row-level import validation, conditions-list refactor | §3.9 |
| Sep 22–24 | Production rebuild: waitress, connection pooling, import ledger, `init_db.py`, TIMESTAMPTZ | §3.10 Pass 1 |
| Sep 25–26 | 8-principles design review + independent cross-check | §3.10 Pass 2 |
| Sep 27–28 | Five-fix cleanup built as parallel versions, verified, promoted; docs rewritten simple+engineer | §3.10 Pass 3 |
| Sep 29 | SQL command notes; log-rotation learning progression; `Database_Connection` moved to `.env` | [SQL_readme_CONCEPTS.md](SQL_Commands/SQL_readme_CONCEPTS.md), [rotation.py](log_rotation/rotation.py) |
| Sep 30 | Log-rotation demos consolidated into one hybrid JSON + rotating-file handler after lost-log debugging; first range-partitioning demo (`partition_ts`) | [rotation.py](log_rotation/rotation.py), [code_explanation.md](log_rotation/code_explanation.md) |
| Oct 1 | Documentation consolidation (one readme per topic); cron-jobs on a real scheduler; table partitioning with just-in-time partitions + composite PK | [cronjobs_readme.md](cron_jobs/cronjobs_readme.md), §3.6 |
| Oct 4–6 | Regular expressions: 8 matcher functions + notes; APScheduler cron triggers; `Final_zip/` copy assembled | [regex_readme_CONCEPTS.md](RegEx/regex_readme_CONCEPTS.md), §3.7 |
| Oct 7–8 | Regex practice on 10 tasks; machine-log monitoring assigned, built, documented, hardened | [regex_readme_CONCEPTS.md](RegEx/regex_readme_CONCEPTS.md), §3.7 |
| Oct 8 | Full self-review: cross-checked every email-assigned task against the live tree; test suite re-run; distribution sync; doc-drift findings | §9 |
| Oct 8–27 | Final self-review vs. the shipped Order & Sales Management code; verification record updated | §9 Order & Sales Management App assignment, delivered as Vue 3 + Flask + PostgreSQL full-stack app | [Order_Sales_Management/](Order_Sales_Management/) |
| Oct 27 | Traceback module documentation prepared and shared | [Traceback.md](Traceback.md) |
| Nov 2 | Pandas documentation prepared + sample-dataset practice completed | [Pandas/Pandas.md](Pandas/Pandas.md) |
| Nov 3 | Reviewed Excel sheet data from mentor; confirmed data structure and column assignments |
| Nov 4 | Verified data frame conversion and string splitting operations completed |
| Nov 5 | Reviewed final Excel sheet; confirmed alignment with pandas analysis and documentation updates; reviewed Excel data for Live_dashboard IIoT live monitoring dashboard setup |
| Nov 10 | Architecture built: IIoT live monitoring dashboard design - Excel dataset, MQTT broker, PostgreSQL database, Flask API, WebSocket hub, Vue.js dashboard framework |
---

---

## 3. Technical sections

Each section follows the same shape: **Built → Learned → Takeaway.**

### 3.1 Pandas — [Pandas/Pandas.md](Pandas/Pandas.md)

**Built:** [analysis.py](Pandas/analysis.py) + the sample dataset
[customers.csv](Pandas/customers.csv),
[orders.csv](Pandas/orders.csv),
[city_report.csv](Pandas/city_report.csv), and
[monthly_revenue.png](Pandas/monthly_revenue.png) — every
analysis/figure in the README was run and saved, so the notebook-like doc
matches what the script actually produced.

**Learned:**

- **Data structures:** one-dimensional `Series` (single labelled column) and
  two-dimensional `DataFrame` (table; "panel data" is the name's origin).
- **Quick checks before trusting a dataset:** `df.head()`, `df.shape`,
  `df.info()`, `df.describe()`, `df.isna().sum()`, `df.dtypes()` — the first
  five lines of any good analysis.
- **Cleaning:** `.fillna()` (with `pad`/`bfill` for forward/backward fill),
  `.dropna()`, `.drop_duplicates(subset=…)` with `keep`, `.replace()`; string
  work via the `.str` accessor (`.str.lower()`, `.str.split()`, `.str.strip()`).
- **Selection:** `df["col"]` (single column → Series), `df[["c1","c2"]]`
  (multi-column), `.loc[]` (label-based), `.iloc[]` (position-based),
  `.at[]`/`.iat[]` (single cell), `.query()` (readable SQL-like filters),
  `.between()` (inclusive ranges), `.isin()` (SQL `IN`).
- **Sorting & slicing:** `df.sort_values()`, `df.sort_index()`; the `kind`
  argument picks the algorithm.
- **Merging/joining/concatenating:** `.concat()` (stack or side-by-side),
  `pd.merge()` with `how=left/right/outer/inner` (SQL join equivalents),
  `pd.join()`.
- **Grouping:** `groupby()` + `agg()`, pivot tables (`index`, `values`,
  `aggfunc`), `value_counts()` for quick frequency and duplicate checks.
- **Time:** `pd.to_datetime()` with an exact format string, `.dt.day`,
  `.dt.month`, `.dt.hour`, `.dt.minute`, `.dt.timestamp` for Unix columns.
- **I/O:** `pd.read_csv()` (`sep`, `header`, `index_col`, `usecols`,
  `nrows`, `na_values`), `df.to_csv()`, `df.to_json()`,
  `pd.json_normalize()` for nested JSON, `df.to_excel()` for Excel.
- **Visualization:** `df.plot(x, y)` / `df.plot.line()` / `.plot.bar()` for
  quick charts; `savefig()` for `monthly_revenue.png`.
- **Statistics:** `df.describe()` for the five-number summary; `.mean()`,
  `.median()`, `.std()` on columns.

**Takeaway:** pandas turns a spreadsheet into a computable object — the
same skills (filter, group, merge, clean) translate directly into the
`group by` clauses and joins the SQL practice docs (§3.4) describe, which is
why both files sit next to each other in this folder.

### 3.2 Git — [Git_Documentation.md](Git_Documentation.md)

**Built:** a single repo-wide reference that covers the whole workflow a
developer needs, from `git init` to `git revert`, including branching,
remotes, merging vs rebasing, and undoing work (`restore`, `stash`,
`reflog`, `revert`).

**Learned:**

- **The four areas of git:** working directory → staging area (`git add`)
  → local repo (`git commit`) → remote (`git push`/`pull`). Everything flows
  through these four.
- **Setup:** `git init`, `git clone` (with `--depth 1`, `--branch`,
  `--recurse-submodules`), `git config --global user.name/email`,
  `git config --list --show-origin` (`--system/-system`, `--global`,
  `--local`).
- **Inspection:** `git status`, `git diff` (`--staged`, `--stat`,
  `main...HEAD`), `git log` (`--oneline`, `--graph --all`, `-n N`,
  `-- <file>`), `git show <commit>`, `git blame <file>`, `git grep`,
  `git shortlog -sn`.
- **Staging & committing:** `git add` (`.`, `-A`, `-p`, `-u`), `git commit`
  (`-m`, `-am`), `git commit --amend` (before pushing only).
- **File ops at the repo level:** `git rm`, `git rm --cached`, `git mv`,
  `.gitignore` (patterns, add before first commit; `git rm --cached` to
  untrack already-tracked files).
- **Branching:** `git branch` (`-a`, `-m`, `-d`, `-D`, `--merged`), `git
  switch` (`-c`, `-` back to previous), `git switch -c <new>`.
- **Remotes & collaboration:** `git remote` (`-v`, `add`), `git fetch`
  (safe, no file change), `git pull` (`--rebase`, `--ff-only`), `git push`
  (`-u origin <branch>`, `--force-with-lease` — never force-push main).
- **Integrating:** `git merge` (`--no-ff`, `--squash`, `--abort`),
  `git rebase` (`-i HEAD~n`, `--continue`, `--abort`), and the merge vs
  rebase decision rule (merge keeps history; rebase rewrites it, use on
  your own branch only).
- **Undoing:** `git revert <hash>` (safe, history preserved), `git restore`
  (`<file>`, `--staged`, `.`), plus `git stash` / `git reflog` for the
  drop-a-commits moments.

**Takeaway:** git is a *history tool*, not a backup tool — `revert` undoes
a commit without rewriting history, `reflog` is the safety net when a
session goes sideways, and `git fetch` before `pull`/`merge` is what
prevents replaying someone else's work.

### 3.3 Python traceback module — [Traceback.md](Traceback.md)

**Built:** a reference covering the `traceback` module's API (printing,
formatting, extracting, walking) plus the standard exception/traceback
lifecycle.

**Learned:**

- **What a traceback is:** a record of the call chain active when an
  exception was raised — where the error happened, in which line, and what
  the error was.
- **Where they live:** caught exceptions via `sys.exc_info()`; uncaught
  ones via `sys.last_traceback` (returns a 3-tuple: type, value,
  traceback object).
- **Printing:** `.print_tb()` (frames only), `.print_exception(e)`,
  `.print_exc()` (means "print the exception currently being handled"),
  `.print_last()` (last uncaught error), `.print_stack()` (current call
  stack — debugging, not error reporting).
- **Formatting:** `.format_exc()` (whole traceback as a single string —
  alerts/emails), `.format_exception()` (list of strings), `.format_exception_only()` (type + message — one-line log),
  `.format_tb()` (frames only), `.format_stack()`, `.format_list()` (a
  list of `FrameSummary`s).
- **Extracting:** `.extract_tb()` (frame data for JSON logs),
  `.extract_stack()`.
- **Walking:** `.walk_tb()` (exception call path), `.walk_stack()`.
- **Classes:** `TracebackException` (captures an exception, formats it
  later), `StackSummary` (`.extract()`, `.from_list()`, `.format()`),
  `FrameSummary` (one frame).
- **Rules of thumb:** `logging.exception("msg")` inside `except` logs the
  full traceback and re-raises (`bare raise`) so the original chain survives;
  `format_exc()` is for alerts; `format_exception_only()` for one-line
  logs; `extract_tb(e.__traceback__)` for JSON/structured logs; **never
  surface tracebacks to end users** — filter local variables before logging.

**Takeaway:** a traceback is a forensic tool, not an error message. The
lesson from the capstone: `logging.exception()` + a bare `raise` keeps the
original chain while still letting the service die cleanly; the same pattern
shows up in `mqttdemo.py`'s callbacks (`logging.exception()` per callback).

### 3.4 SQL — full command portfolio — [SQL_Commands/SQL_readme_CONCEPTS.md](SQL_Commands/SQL_readme_CONCEPTS.md) + [SQL_Commands/Practicing.md](SQL_Commands/Practicing.md)

**Built:** the command-category readme (`SQL_readme_CONCEPTS.md`) plus a
practice cheat-sheet (`Practicing.md`) covering every clause a developer
uses daily — from DDL/DML/DQL/DCL/TCL to window functions and set
operations.

**Learned (command categories):**

- **DDL** — `CREATE`, `DROP`, `ALTER`, `TRUNCATE` (shape the database).
- **DQL** — `SELECT`, `FROM`, `WHERE`, `GROUP BY`, `HAVING`,
  `DISTINCT`, `ORDER BY` (the read side).
- **DML** — `INSERT`, `UPDATE`, `DELETE` (the write side).
- **DCL** — `GRANT`, `REVOKE` (access control).
- **TCL** — `BEGIN TRANSACTION`, `COMMIT`, `ROLLBACK`, `SAVEPOINT`
  (atomic units; the capstone wraps every route in a transaction with
  explicit rollback).

**Learned (types & constraints):** `INTEGER`/`BIGINT`/`SMALLINT`, `NUMERIC`
(exact decimals), `TEXT`/`VARCHAR`, `BOOLEAN`, `DATE`/`TIMESTAMP`/`TIMESTAMPTZ`
(`TIMESTAMPTZ` = the same instant worldwide), `UUID`, `JSONB`, arrays
(`integer[]`, `text[]`); `PRIMARY KEY`, `FOREIGN KEY`, `UNIQUE`, `NOT NULL`,
`CHECK`, `DEFAULT`, `SERIAL`/`BIGSERIAL` (auto-increment), `INDEX`.

**Learned (capstone SQL features):** `RETURNING` (no second round-trip to
fetch an inserted id), `ON CONFLICT DO NOTHING` / `ON CONFLICT DO UPDATE`
(upsert — needs a unique constraint), `LIMIT`/`OFFSET` (pagination),
`MIN`/`MAX`/`AVG` (aggregates), `execute_values` (batch insert of ~5000
rows in one shot), `rowcount` (did an UPDATE/DELETE actually change anything),
`AUTOCOMMIT` (mandatory for `CREATE DATABASE` — Postgres forbids it in a
transaction block).

**Learned (table partitioning — the cron_jobs lesson, §3.6):** split one big
table into smaller children by a value range (`PARTITION BY RANGE`). The
partition column **must** be in the primary key (live Postgres rejected a
plain-`id` PK → composite `PRIMARY KEY (id, unix_ts)`); the `DEFAULT`
partition is the safety net; deleting old data becomes one `DROP TABLE` on
a child instead of a slow bulk `DELETE`; queries prune to the matching
children.

**Learned (practicing cheat-sheet):** `SELECT DISTINCT ON`, `WHERE` with
`=`, `<>`, `<=`, `>=`, `AND`/`OR`/`NOT`, `IN` / `BETWEEN` / `LIKE` /
`ILIKE` / `IS NULL`, `ORDER BY` + `LIMIT` + `OFFSET` (leaderboards, paging),
`INSERT … RETURNING`, `UPDATE` (always `WHERE`), `DELETE` vs `TRUNCATE`,
`COUNT(*)`, `COUNT(DISTINCT col)`, `SUM/AVG`, `MIN/MAX`, `GROUP BY` +
`HAVING`, `INNER`/`LEFT`/`RIGHT`/`FULL`/`CROSS`/self joins, join
conditions vs `WHERE` (a `WHERE` on a right table of a `LEFT JOIN` turns
it back into an `INNER JOIN`), one-to-one / one-to-many / many-to-many,
finding duplicates (`COUNT(*) … GROUP BY … HAVING count(*) > 1`),
finding unmatched rows (`LEFT JOIN … WHERE o.id IS NULL`), `WHERE` vs
`HAVING`, set operations (`UNION`, `UNION ALL`, `INTERSECT`, `EXCEPT`),
and window functions (`PARTITION BY` + `ORDER BY` for ranking,
running totals, and aggregates over a sliding group).

**Takeaway:** SQL is a vocabulary, not a single statement — the same mental
model (filter → group → sort → page) maps from pandas' `.loc[]`/`groupby()`
to `WHERE`/`GROUP BY`/`ORDER BY`, and the partition pattern from §3.6 is
what makes the time-series store purgable by decade instead of row.

### 3.5 Rotating-JSON logging — [log_rotation/code_explanation.md](log_rotation/code_explanation.md)

**Built:** [rotation.py](log_rotation/rotation.py) — one hybrid handler demo:
every log record formatted as **one-line JSON** (unix-epoch timestamp, level,
logger name, message, exception block when present) written to a **rotating
file chain** (`app.log` → `app.log.1` → … → `app.log.10`) plus the console.

**Learned:**

- `RotatingFileHandler.maxBytes` + `backupCount` = a diary that archives
  itself; the disk can never fill. Production code (the capstone logger,
  cron_jobs) uses 10 MB × 5–10.
- `logger.propagate = False` stops records reaching the root logger —
  without it, console handlers print every line twice.
- `if logger.handlers: return` guards against duplicate handler attachment
  on re-imports.
- JSON-per-line is what log collectors want; free-text logs are for humans
  only.

**Incident record (Sep 30):** earlier log-rotation attempts were split across
multiple demos and log lines went missing between them; the fix was
consolidating into this one hybrid handler and documenting the *actual*
function-based code. Lesson: one logging setup per application, wired in
one place, and document the code that really runs.

### 3.6 Cron jobs, schedulers, and table partitioning — [cron_jobs/cronjobs_readme.md](cron_jobs/cronjobs_readme.md)

**Built (restructured Oct 1):** a scheduler-based project that inserts the
current Unix timestamp every minute into a **range-partitioned** PostgreSQL
table and creates partitions just-in-time.

- [setup.py](cron_jobs/setup.py) — bootstrap: `CREATE DATABASE`
  (`autocommit`, `DuplicateDatabase` handled) → `CREATE SCHEMA` → the
  partitioned table `timestamp_data` with **composite primary key
  `(id, unix_ts)`** and a `_default` partition as the safety net.
- [scheduler.py](cron_jobs/scheduler.py) — the two jobs:
  `insert_current_timestamp()` (every 1 minute) and `create_partition()`
  (every 10 minutes, creating the current **and** next 10-minute window so
  a partition always exists before its first insert; `IF NOT EXISTS` makes
  re-runs idempotent).
- [db.py](cron_jobs/db.py) + [config.py](cron_jobs/config.py) —
  `get_connection(database=None)` on `.env` credentials, with an escape hatch
  to the `postgres` maintenance database for `CREATE DATABASE`.
- [logging_config.py](cron_jobs/logging_config.py) — root logger, 10 MB × 10
  rotating file + console, apscheduler quieted to WARNING (the lesson from
  §3.5 applied directly).

**Learned:**

- OS cron vs in-process schedulers: `crontab -e` runs scripts on Linux;
  on Windows, Task Scheduler; in Python, the `schedule` module or
  **APScheduler**. This project uses **APScheduler's `BlockingScheduler`**
  with two `cron`-trigger jobs (`minute="*/1"`, `minute="*/10"`) — see the
  APScheduler-vs-schedule comparison table in the
  [readme](cron_jobs/cronjobs_readme.md).
- **Partition key rule:** PostgreSQL requires the partition column to be
  part of the primary key — hence the composite `PRIMARY KEY (id, unix_ts)`
  after the first plain-`id` design was rejected by the database.
- **Just-in-time partitioning** (Oct 1 fix): inserts originally failed when
  the matching partition didn't exist yet; the insert job now creates the
  partition *before* inserting, and the `DEFAULT` partition catches anything
  that still slips through.
- Partitioning pays off at deletion time: dropping old data becomes
  `DROP TABLE` on one child partition instead of batched `DELETE`s
  ([SQL_readme_CONCEPTS.md](SQL_Commands/SQL_readme_CONCEPTS.md), *Table partitioning*).

**Takeaway:** the pipeline shape — bootstrap script → long-running scheduler →
structured logs → idempotent SQL — is the same skeleton as the capstone's
importer, just time-driven instead of request-driven. Patterns transfer; only
the trigger changes.

### 3.7 Regular expressions and the machine-log monitoring system — [RegEx/regex_readme_CONCEPTS.md](RegEx/regex_readme_CONCEPTS.md) + [RegEx/Machine_Log_Monitor/](RegEx/Machine_Log_Monitor/)

**Built (regex):** [`.py`](RegEx/.py) — eight matcher functions driven by an
interactive `main()`: exact five-digit match with lookarounds
(`(?<!\\d)\\d{5}(?!\\d)`), lowercase-only and uppercase-only scans, grouped
letters + numbers extraction, "starts with A" / "ends with Z" via word
boundaries, digits-only and no-digits scans. Notes in
[regex_readme_CONCEPTS.md](RegEx/regex_readme_CONCEPTS.md) cover the
meta-characters, anchors, special sequences, and the `re.search/match/
fullmatch/findall/sub/split` family. A separate practice file,
[Assigned_Tasks.py](RegEx/Assigned_Tasks.py), covers the ten
extraction/validation tasks (employee and machine IDs, phone numbers, log
parsing with named groups and `groupdict()`, `re.sub` cleaning, `re.split`,
dates, error lines).

**Learned (regex):**

- Aug 4–6: regex assignment — exact 5 digits, lowercase-only, uppercase-only,
  letters-and-numbers, starts-with-A, ends-with-Z, digits-only, no-digits.
  `findall()` extracts, `fullmatch()` validates; `search()` finds, `sub()` /
  `split()` transform.
- Aug 7–8: ten tasks used `re.fullmatch()`, `re.finditer()`, `re.findall()`,
  `re.search()`, `re.sub()`, `re.split()`, `groupdict()`, and named groups.
- Aug 8: `^abc` (anchor) is not `[^abc]` (negation) — one character, opposite
  meaning.
- Aug 8: lookarounds (`(?<!\\d)…(?!\\d)`) match a position, not a character —
  the clean way to say "exactly five digits, not part of a longer number".
- Named real uses: input validation, log parsing with groups, `re.sub()` data
  cleaning — the same skills the capstone uses for validating query params.

**Built (machine-log monitoring):** [setup_db.py](RegEx/Machine_Log_Monitor/setup_db.py)
→ [db.py](RegEx/Machine_Log_Monitor/db.py) (connection) →
[logging_config.py](RegEx/Machine_Log_Monitor/logging_config.py) →
[log_reader.py](RegEx/Machine_Log_Monitor/log_reader.py) (parses `machine.log`)
→ [log_parser.py](RegEx/Machine_Log_Monitor/log_parser.py) (regex extraction)
→ [jobs.py](RegEx/Machine_Log_Monitor/jobs.py) (insert + report on schedule)
→ [scheduler.py](RegEx/Machine_Log_Monitor/scheduler.py) (APScheduler cron)
→ [report.py](RegEx/Machine_Log_Monitor/report.py) (CSV output)
→ [machine_log_monitor_CONCEPTS.md](RegEx/Machine_Log_Monitor/machine_log_monitor_CONCEPTS.md).
The system stores `ERROR` entries in PostgreSQL with duplicate handling,
generates `machine_error_report.csv`, and runs on a schedule — the same
pattern as §3.6, now wired to real log data.

**Takeaway:** regex is a validation tool, not a puzzle toy — the
extract-and-validate patterns here are exactly what an API's input layer does
daily, and the log monitor is the same import pipeline as the capstone's,
just triggered by a scheduler instead of a REST call.

### 3.8 Order & Sales Management App — [Order_Sales_Management/](Order_Sales_Management/)

**The assignment (Oct 13):** a full-stack application simulating a retail/
e-commerce business: customer orders, validated order details, calculated
order totals, tracked order statuses, duplicate-order detection, and
product-wise / date-wise sales reports.

**Delivered (Oct 23) — Vue 3 + Flask + PostgreSQL (OrderSync):**

- **Frontend:** Vue 3 (Vite + Pinia + Vue Router + Axios) — public auth
  screens (`Landing`, `Login`, `Register` with 2-step OTP, `ForgotPassword`,
  `ResetPassword`); customer views (`MyOrders`); admin panels (`Orders`,
  `CreateOrder`, `OrderDetail`, `Products`, `Customers`, `Users`, `Reports`,
  `Duplicates`, `Totals`).
- **Backend:** Flask REST API (poorly typed) with a three-layer layout —
  `routes/` (thin controllers) → `services/` (business rules, no HTTP/DB) →
  `models/` (SQLAlchemy) → `utils/` (decorators, permissions, validators,
  dev email).
- **Database:** PostgreSQL `order_sales` schema — `users`, `customers`
  (1:0..1 via `user_id`), `products`, `orders`, `order_items`, plus
  hash-based import-ledger patterns from the capstone.
- **Auth & security:** registration → OTP hash + 2-min TTL → verify →
  link customer; JWT access tokens carry only `identity` + `tv`; roles are
  reloaded from the DB per request; `token_version` bumps on password reset
  and revoke formerly issued tokens; role cannot be forged via JWT.
- **Order rules (server-side):**
  - `order_id` must match `ORD####`; `customer_id` must match `C####` and
    exist; quantity integer 1–1000; product exists with a price; no duplicate
    `order_id`.
  - Server uses `products.current_price` for every line item — client
    `unit_price` is ignored.
  - Strict state machine: `Pending → Received/Shipped/Cancelled`;
    `Received → Shipped/Cancelled`; `Shipped → Delivered/Returned`;
    `Delivered → Returned`; `Cancelled`/`Returned` terminal.
  - Ownership: customers see only their own orders; cross-tenant reads return
    `404` (not `403`) to avoid leaking order IDs.
- **Reports:** `GET /api/reports/summary` (KPIs + breakdowns), plus
  `product-wise` and `date-wise` endpoints with JSON/CSV. Revenue counts only
  `Shipped` + `Delivered`, using historic `order_items.unit_price`.

**Risk note:** the shipped code says the backend suite passes (**84 tests**),
but the local test database is configured with `postgres` and password
`Vijay37` at `localhost:5432/intern_training_db`, and a live connection
fails with `FATAL: password authentication failed for user "postgres"`.
The 84-test count is the shipped code's own (6 files: `test_auth`=29,
`test_orders`=24, `test_permissions`=23, `test_pricing`=3, `test_reports`=3,
`test_smoke`=2), and it was re-run — **84 errors, all `sqlalchemy` —
because the DB host never saw the server's credentials.** Full details in
§9.

---

## 4. Supporting skills

| Skill | Files | What you get |
| **Pandas** | [Pandas/Pandas.md](Pandas/Pandas.md), [analysis.py](Pandas/analysis.py), `customers.csv`, `orders.csv`, `city_report.csv`, `monthly_revenue.png` | Data I/O, cleaning, selection, grouping, merging, pivot tables, plotting |
| **Git** | [Git_Documentation.md](Git_Documentation.md) | init → clone → commit → branch → remote → merge/rebase → undo; the full workflow |
| **Traceback** | [Traceback.md](Traceback.md) | print/format/extract/walk API + the logging rule (`exception` + bare `raise`) |
| **SQL** | [SQL_Commands/SQL_readme_CONCEPTS.md](SQL_Commands/SQL_readme_CONCEPTS.md), [SQL_Commands/Practicing.md](SQL_Commands/Practicing.md) | Command categories, types, constraints, capstone SQL, partitioning, window functions |
| **Logging** | [log_rotation/](log_rotation/) | Rotating JSON handler, one-line-JSON, `propagate=False`, `if logger.handlers: return` |
| **Scheduling** | [cron_jobs/](cron_jobs/) | APScheduler `BlockingScheduler` + `cron` triggers + range-partitioned table |
| **Regex** | [RegEx/regex_readme_CONCEPTS.md](RegEx/regex_readme_CONCEPTS.md), [RegEx/.py](RegEx/.py), [Assigned_Tasks.py](RegEx/Assigned_Tasks.py), [Machine_Log_Monitor/](RegEx/Machine_Log_Monitor/) | 8 matchers, 10-task practice, log ingestion → DB → CSV on a schedule |
| **OOP** | [OOP/OOP_CONCEPTS.md](OOP/OOP_CONCEPTS.md) + [OOP/*.py](OOP/) | 5 inheritance types + encapsulation, exception-guarded demos |
| **Linux** | [Linux/](Linux/) | Navigation, file ops, `grep`/`find`/`wc`, `sort`/`uniq`, `grep -r` vs `find -exec` |
| **Networking / frontend** | [NetWorking/NAT.md](NetWorking/NAT.md), [NetWorking/Vue.md](NetWorking/Vue.md) | NAT/redirection concepts, Vue Router + Pinia explainer |
| **Capstone** | [MQTT/Machine_Sensor_API/](MQTT/Machine_Sensor_API/) | Flask + PostgreSQL machine sensor API, pool, timeouts, import ledger |
| **Order & Sales** | [Order_Sales_Management/](Order_Sales_Management/) | Vue 3 + Flask + PostgreSQL full-stack app, roles, status machine, reports |
| **Live_dashboard** | [Live_dashboard/](Live_dashboard/) | IIoT live monitoring dashboard: Excel → MQTT → PostgreSQL → Flask API → WebSocket → Vue.js dashboard, real-time telemetry, alarm evaluation, replay controls |
---

## 5. Error log (encountered → resolved)

| Error | Root cause | Fix / lesson |
| `FileExistsError` while practicing | `"x"` mode on existing file | Intended behavior — guard with try/except |
| `CREATE DATABASE` failing inside transaction block | Postgres disallows it | Connect to `postgres` db + `autocommit = True` |
| Duplicate-email insert rejected | `UNIQUE` constraint | Expected; surfaced as a clean 400 with validation first |
| Broken multiline `mosquitto.conf` written via `echo` | Newline loss in shell redirect | Edit the real config file manually |
| `ssl.SSLCertVerificationError` | Cert without SAN / wrong CN / expired | Add IP/DNS to `san.cnf`, regenerate server cert |
| Callbacks "not firing" | Expecting callbacks to replace return-code checks | Check `subscribe()`/`publish()` results **and** register callbacks |
| `Minues` column typo in Excel output | Manual typo in generated columns | Fixed to `Minutes`; proofread output schema |
| Blank snapshot record sets | First snapshot(s) carried empty dicts | Importer treats empty data as 0 records, continues |
| `FATAL: password authentication failed for user "postgres"` | `Order_Sales_Management/server/.env.test` points at `localhost:5432/intern_training_db` with `user=postgres password=Vijay37`; the local server does not accept that password → all 84 backend tests error (`sqlalchemy`) | Record the shipped claim + blocker in §7/§9; the code is correct — the local DB host is not configured for it |
| Duplicate readings on re-import | Overlapping snapshots | Fixed with `ON CONFLICT DO NOTHING`; **final fix (Sep 28):** the `import_batches` hash ledger — content, not constraints |
| Statistics returned as JSON strings | `NUMERIC` → psycopg2 `Decimal` → Flask stringifies | Cast aggregates `::float8` — real numbers at the JSON boundary |
| Duplicate machine / missing FK machine returned 500 | `IntegrityError` never translated | `ConflictError` → 409, FK error (now `RelatedResourceNotFoundError`) → 400 |
| One bad `VR` value aborted a whole pickle file | Value not validated per row | Row-level `float()` check → skip + count in `records_skipped` |
| Fragile `WHERE 1 = 1` concatenation | Appended conditions depended on trailing whitespace | Conditions list + `" AND ".join(...)` — later grew into one shared `_build_reading_filters()` |
| Hung query could hold a pooled worker forever | No connect/statement timeouts | `connect_timeout=5` + `statement_timeout=15000` (env-tunable); verified live via `SHOW statement_timeout` |
| Log file grew without bound | Plain `FileHandler` on a long-running service | `RotatingFileHandler` 10 MB × 5 + `LOG_LEVEL` from env |
| A reviewer's "live code" finding didn't match the tree | Finding came from an archived zip snapshot | Full-text search proved the live code clean; lesson: **review the live tree, not the archive** |
| Log lines went missing between rotation demos | Two parallel logging demos, each with its own handlers | Consolidated into one hybrid JSON + rotating handler (Sep 30); one logging setup per app |
| Inserts failed with "no partition … found" | Row arrived before its 10-minute partition existed | Just-in-time partition creation before each insert + a `DEFAULT` catch-all partition (Oct 1) |
| `CREATE TABLE … PARTITION BY` rejected the plain-`id` primary key | Postgres requires the partition column inside the PK | Composite `PRIMARY KEY (id, unix_ts)` (Oct 1) |
| Two concurrent imports could collide resolving the same machine name | Machine lookup + insert were not atomic — risk caught in review, not a crash observed | Race-safe `INSERT … ON CONFLICT (machine_name) DO UPDATE … RETURNING id` in the importer |
| Cron readme still documented `schedule.every(...).do()` calls | The readme kept `schedule`-module remnants after the Oct 1 rewrite to APScheduler | Found in the Oct 8 review; readme to be cleaned so it documents only what actually runs |
| Regex readme showed a grouping pattern the code doesn't use | Notes were written before the implementation changed to two `findall` calls | Found in the Oct 8 review; the lesson applies to notes too — docs drift, code is the source of truth |

---

## 6. How the period changed my engineering habits

1. **Secrets** — from hard-coded passwords to `.env` + fail-fast `config.py`
   (capstone, cron_jobs, and since Sep 29 back-ported to the early
   `Database_Connection` project too).
2. **Connections** — from one long-lived reused connection, through
   per-request connections with `finally` cleanup, to a pooled manager with
   context managers that always return the connection (and discard broken
   ones).
3. **SQL** — from string concatenation to parameterized queries everywhere;
   identifiers kept out of value positions; filters built in one shared place.
4. **Failure handling** — from printing exceptions to typed exceptions
   (`DatabaseError` and family), rollback, `rowcount` checks, and
   `logging.exception()`.
5. **Time-bounded failure** — a stuck database or runaway query now hits
   `connect_timeout`/`statement_timeout`: fast, visible, logged failure beats
   slow, silent failure.
6. **External calls** — always validate the immediate return code *and*
   handle the async confirmation (Paho lesson; generalizes to any messaging
   system).
7. **Data integrity** — enforce only claims that can be proven; protect the
   rest at ingestion (the hash ledger), so a wrong assumption can't multiply
   into 11.8M rows again.
8. **Structure** — routes/services/database layering, earned after flat
   scripts became hard to navigate.
9. **Readability** — replaced `WHERE 1 = 1` string surgery with a conditions
   list, then a single shared builder; code is read far more often than it is
   written.
10. **Versioned change discipline** — build the fix as a parallel copy, verify
    both chains behave identically, promote only then. Rollback becomes
    trivial by construction.
11. **Review the live tree** — an archived zip is not the codebase; every
    finding gets verified against the live files before acting on it.
12. **Principles over fashion** — the 8-principles checklist runs on every
    change, with the standing override: a change that adds complexity without
    solving a concrete problem is rejected (KISS wins).
13. **Documentation** — if a README would embarrass me in review, the code
    isn't ready.
14. **Explain it simply** — if a non-technical reader can't understand the
    first section of a doc, the doc isn't finished yet.
15. **Consolidate, don't accumulate** — scattered note files drift apart;
    each topic now lives in exactly one readme (Oct 1 consolidation), and this
    document gets re-verified against the live tree before every revision.
16. **One frontend, one backend, one source of truth for roles** — the
    Oct 13–23 work made the separation concrete: the Vue frontend owns UI,
    navigation, and client-side guards; Flask owns auth, pricing, status
    machine, and tenancy; `constants.Role` replaced string literals everywhere.
17. **Verify before claiming coverage** — the shipped 84-test suite count
    comes from the `Order_Sales_Management` tree; the re-run in this
    environment surfaces `sqlalchemy` auth errors because the local PostgreSQL
    server does not accept the `postgres`/`Vijay37` credential in
    `server/.env.test`. Records both here (§7 and §9) rather than claiming a
    pass the environment won't let me make.

---

*All file links in this document are relative and verified against the live
tree on 8 October 2026. The capstone's
[Machine_Sensor_API_CONCEPTS.md](MQTT/Machine_Sensor_API/Machine_Sensor_API_CONCEPTS.md)
carries the full simple + engineer detail; line-by-line code walkthroughs
nlive per-topic, e.g.
[log_rotation/code_explanation.md](log_rotation/code_explanation.md).*
