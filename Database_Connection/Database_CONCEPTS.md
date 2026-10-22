# Database (PostgreSQL + Python + Flask) Concepts — Intern Training

**Source:** `Database_Connection/README.md`, `Database_Connection/setup.py`, `Database_Connection/main.py`

> Two stages of the same learning path: (1) `setup.py` — talk to PostgreSQL directly with psycopg2; (2) `main.py` — a Flask REST API in front of it.

---

## 1. PostgreSQL bootstrap — Postgremanager

**What:** One class that does the full bootstrap:

- `create_db()` — connects to the built-in `postgres` database first, sets `autocommit`, then creates `main`.
- `create_schema()` / `create_table()` — `main_schema.main_table` with employee columns: `first_name`, `last_name`, `email` (UNIQUE), `phone`, `hire_date`.
- `insert_employee()` / `update_employee()` / `delete_employee()` — parameterized queries, commit on success, rollback on failure.
- `fetch_all_employees()`.

**Concepts learned:**
- `CREATE DATABASE` cannot run inside a transaction → connect to the built-in `postgres` DB first and set `autocommit = True`.
- Parameterized queries (`%s` placeholders) for every value; f-strings only for identifiers like table names, never data.
- Transactions: `commit()` on success, `rollback()` on failure.
- Connection **reuse, not pooling**: `connect()` checks whether the current connection is open and pointed at the right database, and only reconnects when needed.
- Credentials now load from a `.env` file — same pattern the later Machine Sensor API uses. Originally the password was hard-coded in `setup.py`; moved to environment variables before the repo was pushed to GitHub.

**Pros:**
- Single class covers the full bootstrap + CRUD cleanly.
- Parameterized queries prevent SQL injection.
- Transaction control gives atomicity.
- `rowcount` to confirm UPDATE/DELETE actually matched a row.

**Cons/drawbacks:**
- Early versions swallowed "database already exists" into a generic `except` + print; `DuplicateDatabase` is now handled explicitly.
- Reuse without pooling does not survive traffic; the capstone moves to a connection pool.
- Connection-state checks (`conn.closed`, `conn.info.dbname`) add complexity.

**Errors encountered & causes:**
- `CREATE DATABASE` failing inside a transaction → Postgres disallows it → connect to `postgres` DB + `autocommit = True`.
- Duplicate-email insert rejected by `UNIQUE` → expected; surfaced as a clean 400 with validation first.

**Use cases:**
- Any Python+Flask app needing a relational store, especially REST APIs with simple CRUD.
- Bootstrap scripts that create the database, schema, and tables once.

**Usage:**
```python
pg = Postgremanager()
pg.create_db()
pg.create_schema()
pg.create_table()
pg.insert_employee(first_name="a", last_name="b", email="a@b.c", phone="123", hire_date="2026-01-01")
pg.update_employee(...)
pg.delete_employee(...)
```

---

## 2. Flask REST API over the employee table — main.py

**What:** A Flask `MethodView` on top of `Postgremanager`:

```
GET     /employees            list all
GET     /employees/<email>    one employee
POST    /employees            insert one or a whole batch
PUT     /employees/<email>    update
DELETE  /employees/<email>    delete
```

- POST accepts a single object **or** a list — one endpoint, batch-capable.
- Validation lives in the route; SQL lives in the manager class. That separation grew into the full routes/services/database layering.
- A browser can only speak GET — POST/PUT/DELETE need Postman, `curl`, or JS `fetch`.
- Every answer uses the same JSON shape (`status` / `message` / `data`).

**Pros:**
- Clean separation of routes vs. database.
- Consistent JSON envelope across all endpoints.
- One endpoint can insert a single record or a batch.

**Cons/drawbacks:**
- No connection pooling — fine for learning, not for traffic.
- Validation and DB logic share the route; the capstone splits this into layers.
- No auth by design (learning setup).

**Errors encountered & causes:**
- Duplicate-email insert rejected by `UNIQUE` → handled cleanly with validation first.

**Use cases:**
- Learning RESTful CRUD with Flask + PostgreSQL.
- Template for a small API.

**Usage:**
- Run `main.py`, use Postman/curl/fetch for POST/PUT/DELETE (browsers only speak GET).

---

## 3. Lessons carried forward to the capstone

1. Secrets live in `.env`, never in code.
2. Parameterized queries everywhere; identifiers out of value positions.
3. Commit/rollback per transaction; `rowcount` to confirm mutations.
4. Reuse connections with state checks; later move to a pool.
5. Route-level validation; database logic in a separate service layer.

---

**Quick reference — all database files**
| File | Role |
|---|---|
| setup.py | `Postgremanager` class: bootstrap + CRUD |
| main.py | Flask `MethodView` REST API |
| README.md | Per-folder documentation |

**Status:** 2 scripts + README, runnable standalone.
