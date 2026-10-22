# SQL Concepts — Intern Training

**Source:** `SQL_Commands/SQL_readme.md`, `cron_jobs` partitioning exercise

---

## 1. SQL command categories

**What:** The command taxonomy broken into five groups.

| Category | Language | Examples |
|---|---|---|
| **DDL** — Data definition language | structure | `CREATE`, `DROP`, `ALTER`, `TRUNCATE` |
| **DQL** — Data query language | retrieve | `SELECT`, `FROM`, `WHERE`, `GROUP BY`, `HAVING`, `DISTINCT`, `ORDER BY` |
| **DML** — Data manipulation language | manipulate | `INSERT`, `UPDATE`, `DELETE` |
| **DCL** — Data control language | access control | `GRANT`, `REVOKE` |
| **TCL** — Transaction control language | execution units | `BEGIN TRANSACTION`, `COMMIT`, `ROLLBACK`, `SAVEPOINT` |

**Concepts learned:**
- DDL defines, DQL retrieves, DML mutates, DCL controls access, TCL controls transaction units.
- Keeping these categories separate makes a SQL vocabulary easy to search and remember.

**Pros:**
- Clear mental model for any SQL command.

**Cons/drawbacks:**
- Merely naming them doesn't cover real-world joins, window functions, and `EXPLAIN ANALYZE` (still "not used yet").

**Errors encountered & causes:**
- N/A at this conceptual stage (detailed usage comes later in the capstone).

**Use cases:**
- Any SQL-based application; a reference for choosing the right command family.

**Usage:**
- DDL to define tables; DQL to query; DML to mutate; DCL to grant/revoke; TCL to group statements into atomic units.

---

## 2. Constraints and types used while creating tables

| Constraint / type | What it does |
|---|---|
| **Foreign key** | connects a column to the primary key of another table |
| **On delete cascade** | when the parent row is deleted, child rows are deleted automatically |
| **Not null** | the column must always have a value |
| **Default** | fills a value by itself when not passed |
| **Serial / Bigserial** | auto-generates id numbers for every new record |
| **Timestamptz** | stores date-time with timezone so one instant means the same worldwide |
| **Index** | makes filtering fast on columns we search a lot |

**Pros:**
- Strong relational guarantees (constraints, FK cascade).
- `TIMESTAMPTZ` gives correct worldwide instants.

**Cons/drawbacks:**
- Over-enforcing constraints you can't prove leads to data-loss errors (see partitioning error below).
- Indexes speed reads but cost writes.

**Errors encountered & causes:**
- N/A here (applied in the capstone and partitioning exercises).

**Use cases:**
- Any table definition where data integrity and correctness matter.

**Usage:**
- Use `NOT NULL`, `DEFAULT`, `UNIQUE`, `FOREIGN KEY`, `ON DELETE CASCADE` deliberately.
- Use `TIMESTAMPTZ` for anything that means an instant worldwide.
- Add indexes only on columns you actually search/filter.

---

## 3. Extra commands used in the API projects

| Command | Purpose |
|---|---|
| `RETURNING` | gives back the row just inserted/updated |
| `ON CONFLICT DO NOTHING` | skips the row if it already exists |
| `ON CONFLICT DO UPDATE` | upsert |
| `LIMIT` / `OFFSET` | pagination |
| `MIN` / `MAX` / `AVG` | aggregate functions |
| `execute_values` | batch insert 5000 rows in one shot |
| `rowcount` | tells whether an UPDATE/DELETE actually changed any row |
| `AUTOCOMMIT` | needed for `CREATE DATABASE` |

**Pros:**
- `RETURNING` avoids a second round-trip to fetch an inserted id.
- `ON CONFLICT` handles dedup/upsert at the DB level.
- `execute_values` gives huge batch-insert performance.

**Cons/drawbacks:**
- `ON CONFLICT` requires a unique constraint to exist.
- `rowcount` can be 0 for a matched-but-unchanged row.

**Errors encountered & causes:**
- N/A here (applied in capstone and partitioning).

**Use cases:**
- Batch imports (`execute_values` for ~5000-row chunks).
- Idempotent upserts (`ON CONFLICT DO UPDATE`).
- Safe deletion with `rowcount` checks.

**Usage:**
```python
psycopg2.extras.execute_values(cur, "INSERT INTO t (a,b) VALUES %s", rows)
cur.execute("INSERT INTO t (...) VALUES (...) RETURNING id")
cur.execute("INSERT ... ON CONFLICT (id) DO UPDATE SET ...")
```

---

## 4. Table partitioning — what was learned in the cron_jobs exercise

**What:** Splitting one big table into smaller child tables by a value range.

| Concept | What it means |
|---|---|
| **Partition by range** | splits one table into smaller child tables by a value range |
| **Partition key rule** | the primary key **must** include the partition column (`unix_ts`) or Postgres rejects it |
| **Default partition** | safety-net child table that catches rows with no matching partition |
| **Partition pruning** | Postgres scans only the matching child partitions |
| **Drop partition** | removing old data becomes `DROP TABLE` on one child partition (instant) instead of batched `DELETE`s |

**Pros:**
- Deletion by range becomes a fast `DROP TABLE` on one child, not a slow bulk `DELETE`.
- Queries on a time range scan only the matching children (partition pruning).

**Cons/drawbacks:**
- Partitioning requires the partition column inside the primary key → composite PK.
- Rows arriving before their partition exists fail → needs just-in-time partition creation + a `DEFAULT` catch-all.

**Errors encountered & causes:**
- `CREATE TABLE … PARTITION BY` rejected a plain-`id` primary key → Postgres requires the partition column inside the PK → composite `PRIMARY KEY (id, unix_ts)`.
- Insert failed with "no partition found" → row arrived before its 10-minute partition existed → just-in-time partition creation + a `DEFAULT` catch-all partition.

**Use cases:**
- Time-series tables that grow large and are purged by time range.
- Metrics, logs, and telemetry stores where deletion/aggregation is by time.

**Usage:**
```sql
CREATE TABLE events (
    id BIGINT,
    unix_ts BIGINT,
    data JSONB,
    PRIMARY KEY (id, unix_ts)
) PARTITION BY RANGE (unix_ts);

CREATE TABLE events_10m PARTITION OF events
    FOR VALUES FROM (0) TO (1000000000);
```

---

## 5. Common table operations (quick reference)

| Operation | Purpose |
|---|---|
| `CREATE TABLE` | create new table, define column names and datatypes |
| `INSERT INTO` | add rows |
| `DROP TABLE` | removes a table from the DB |
| `ALTER` (rename) | rename table or column, add column, modify datatype, drop column |
| `TRUNCATE TABLE` | remove all records without preserving structure |
| `CLONING TABLE` | create duplicate (simple, shallow, deep) |
| `TEMPORARY TABLE` | store data temporarily during query execution |
| `AUTO INCREMENT` | automatically generate unique values (`SERIAL` in PostgreSQL) |
| `SEQUENCES` | generate unique numbers automatically |
| `CACHE management` | stores sequence values in memory |
| `UPDATE` | modify existing data |
| `DELETE` | remove specific rows |
| `Duplicate rows` | removed with `ROW_NUMBER()` or `COUNT()` |

---

**Quick reference — all SQL files**
| File | Role |
|---|---|
| SQL_readme.md | Command categories, constraints, extra commands, partitioning |
| cron_jobs/ | Range-partitioning demo with APScheduler |

**Status:** 1 readme + partitioning demo, runnable standalone.
