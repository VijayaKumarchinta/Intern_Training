# PostgreSQL with Python + Flask

This folder holds two stages of the same learning path:

1. [setup.py](setup.py) — talk to PostgreSQL directly with psycopg2
2. [main.py](main.py) — put a Flask REST API in front of it

## [setup.py](setup.py) — `Postgremanager`

One class that does the full bootstrap:

- `create_db()` — connects to the built-in `postgres` database first (you
  can't run `CREATE DATABASE` while connected to a database that doesn't exist
  yet), sets `autocommit`, then creates `main`
- `create_schema()` / `create_table()` — `main_schema.main_table` with employee
  columns: first_name, last_name, email (UNIQUE), phone, hire_date
- `insert_employee()`, `update_employee()`, `delete_employee()` — parameterized
  queries, commit on success, rollback on failure
- `fetch_all_employees()`

The connection handling is **reuse, not pooling**: `connect()` checks whether
the current connection is open and pointed at the right database, and only
reconnects when needed.

## [main.py](main.py) — the API

Flask `MethodView` on top of `Postgremanager`:

```text
GET     /employees            list all
GET     /employees/<email>    one employee
POST    /employees            insert one or a whole batch
PUT     /employees/<email>    update
DELETE  /employees/<email>    delete
```

POST validates required fields before touching the database, and every answer
uses the same JSON shape (`status` / `message` / `data`).

## [Screenshots/](Screenshots/)

Postman results for the whole flow — before/after insert, batch insert,
duplicate email rejection, update, delete:

- [POST — single insert](Screenshots/POST_inserting_single_data.png)
- [POST — batch insert](Screenshots/POST_inserting_batch_data.png)
- [GET — final view](Screenshots/GET_Retriving_data_final_view.png)

(the rest of the screenshots cover single fetch by email, duplicate rejection,
update and delete — the filenames say what each one shows)

## Honest notes

- Credentials now load from a `.env` file (see [.env.example](.env.example)) — the same
  pattern the later [Machine Sensor API](../MQTT/Machine_Sensor_API/readme.md) uses.
  Originally the password was hard-coded in `setup.py`; it was moved to environment
  variables before the repo was pushed to GitHub.
- `create_db()` here folds "database already exists" into a generic except and
  just prints it. The newer API handles `DuplicateDatabase` explicitly.

---
Back to the [repository guide](../README.md).
