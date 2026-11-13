# Git review prep — Intern_Training

This file is a reviewer's map, not new project content. Read it first, then follow the
"Start here" path below. Everything else in the repo is reachable from that path.

## Start here

1. `TRAINING_DOCUMENTATION.md` — the master map of the whole period.
   - §1 Executive summary
   - §2 Timeline
   - §3 Technical sections (one per topic/project)
   - §4 Supporting skills
   - §5 Error log
   - §6 Engineering habits
   - §8 Three-project comparison
   - §9 Verification record
2. `7_Common_programming_Principles.md` — the principles lens used in review.
3. The one concept README per project/topic listed in "Review path by goal" below.

## Current snapshot

A zipped snapshot of the current repo tree is available as:

- `Intern_Training_review_package.zip` — built from the current `HEAD` with `git archive`.

Use it when you want a single file copy of the repo as it stands now, without cloning or pulling.
The zip is the same tree the rest of this document describes; it is not a separate or cleaned-down
version.

## What this repo is

A training record that grew from language fundamentals into three production-shaped systems:

- **Order & Sales Management (OrderSync)** — Vue 3 + Flask + PostgreSQL full-stack app.
- **Machine Sensor API (capstone)** — Flask + PostgreSQL layered REST API with bulk import,
  connection pooling, timeouts, and an import ledger.
- **PlantView / Line 30 Live Dashboard (Live_dashboard)** — IIoT live monitoring pipeline:
  MQTT ingest → PostgreSQL → Flask + Flask-SocketIO → Vue 3 + Vite, with replay and CSV export.

The rest of the folders are the smaller supporting tracks that led up to and alongside those
three: OOP, file handling, conversion, database connection, Flask + employee API, MQTT broker,
Paho client, SQL portfolio, log rotation, cron jobs + partitioning, regex, machine-log monitor,
pandas, git, traceback, networking/frontend concepts.

## Review path by goal

### If you want the whole period in one pass

`TRAINING_DOCUMENTATION.md` → the three project READMEs below → the one "honest review" note
about the test-suite blocker in §3.8/§5/§9.

### If you want each project as a self-contained unit

- **Order & Sales Management:** `Order_Sales_Management/docpack/final_full_project_explained.md`
  is the big picture; `Order_Sales_Management/server/Backend.md` and `Order_Sales_Management/db/DB.md`
  are the backend and database detail; `Order_Sales_Management/client/README.md` is the frontend entry.
  The `docpack/` subfolder holds the per-area explainer set.
- **Machine Sensor API:** `MQTT/Machine_Sensor_API/Machine_Sensor_API_CONCEPTS.md`.
- **Live_dashboard:** `Live_dashboard/documentation/README_software_documentation.md`, then
  `Live_dashboard/documentation/backend_architecture.md`,
  `Live_dashboard/documentation/frontend_architecture.md`,
  `Live_dashboard/documentation/websocket_architecture.md`,
  `Live_dashboard/documentation/website_architecture_full.md`,
  and `Live_dashboard/documentation/application_flow.md`.

### If you want a single topic

Use the topic's own `CONCEPTS.md` / `README.md`:
- `OOP/OOP_CONCEPTS.md`
- `File_Handling/File_Handling_CONCEPTS.md`
- `Conversion/Conversion_CONCEPTS.md`
- `Database_Connection/Database_CONCEPTS.md`
- `MQTT/mqtt_readme_CONCEPTS.md`
- `MQTT/Python/mqttdemo_CONCEPTS.md`
- `SQL_Commands/SQL_readme_CONCEPTS.md` (+ `Practicing.md` for the working cheat sheet)
- `log_rotation/Log_Rotation_CONCEPTS.md` (+ `code_explanation.md` for line-by-line)
- `cron_jobs/cronjobs_readme.md`
- `RegEx/regex_readme_CONCEPTS.md` + `RegEx/Machine_Log_Monitor/machine_log_monitor_CONCEPTS.md`
- `Pandas/Pandas.md`
- `Git_Documentation.md`
- `Traceback.md`
- `NetWorking/NAT.md`, `NetWorking/Vue.md`

## What is useful and safe to include in a review

All of the above. These are the authored, intentional record of what was built and learned, and
they are the files `TRAINING_DOCUMENTATION.md` already points to.

For code, the safe review targets are the same places the docs point to:
- OrderSync backend: `Order_Sales_Management/server/app/` and `Order_Sales_Management/server/tests/`
- OrderSync frontend: `Order_Sales_Management/client/src/`
- Machine Sensor API: `MQTT/Machine_Sensor_API/`
- Live_dashboard backend: `Live_dashboard/server/`
- Live_dashboard frontend: `Live_dashboard/frontend/src/`
- Live_dashboard docs: `Live_dashboard/documentation/`
- Live_dashboard schema: `Live_dashboard/db/schema.sql`

## What to skip or treat carefully during review

- **Data and artifacts that are not the authored record:** raw CSV/pickle/sample files and similar
  data assets are for running the projects, not for reviewing what was learned.
- **Generated output and screenshots:** figures, report CSVs, dev-email logs, and screenshot folders
  are outputs of running the projects. They can corroborate a run, but they are not the source of truth
  for the code or the documentation.
- **Old/parallel copies:** if a topic has more than one README or a `_v2`/`_v3`/`Final_zip`-style
  folder, follow the file the main documentation points to and treat older copies as history, not current
  truth. `TRAINING_DOCUMENTATION.md` already flags doc drift in §5 where it was caught.
- **Environment files:** treat `.env`-family files as config shape only. The training moved secrets out
  of code and into `.env`/`.env.example`; the reviewed code should read config from env, not embed real
  credentials.
- **Test-suite claims vs. local run:** the OrderSync backend is documented as passing 84 tests, but that
  claim is from the shipped tree and cannot be reproduced here because the local PostgreSQL server does not
  accept the `postgres`/`Vijay37` credential in `Order_Sales_Management/server/.env.test`. Record both the
  shipped claim and the local blocker; do not mark the suite as locally verified when it is not. See §3.8,
  §5, and §9 of `TRAINING_DOCUMENTATION.md`.

## The honest open items to carry into any review

1. **OrderSync test suite is documented as 84 passing, but the local DB credential in
   `Order_Sales_Management/server/.env.test` does not connect here.** The code can be reviewed; the test
   count is a shipped claim, not a locally verified result.
2. **Doc drift was found and recorded** — the cron_jobs readme still has `schedule`-module remnants and the
   regex readme still reflects an older grouping pattern. Those are flagged in §5 and should be cleaned before
   the docs are treated as fully current.
3. **`SQL_Commands/Practicing.md` has an uncommitted working-tree change** in this checkout; it is intentionally
   left out of the recent commits, so a reviewer should not assume the committed file is the only revision in play.

## Suggested review order for a future pass

1. Principles: `7_Common_programming_Principles.md`
2. Master map: `TRAINING_DOCUMENTATION.md`
3. Pick one system to go deep on:
   - OrderSync → `Order_Sales_Management/docpack/final_full_project_explained.md`
   - Capstone → `MQTT/Machine_Sensor_API/Machine_Sensor_API_CONCEPTS.md`
   - Live_dashboard → `Live_dashboard/documentation/README_software_documentation.md`
4. Then the relevant code tree the doc points to.
5. Then any one supporting topic via its own README/CONCEPTS file.

## Why this file exists

So a reviewer does not have to open the whole repository at once. The repo is large and partly archival;
this file points to the current, authored record and marks the parts that are outputs, history, or environment
rather than the thing to review.
