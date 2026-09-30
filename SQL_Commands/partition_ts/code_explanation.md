# Code Explanation — `partition_ts/` (function by function)

## The simple version first

Think of the table as a **diary with dividers**.

- **`insert` job** — writes one line in the diary (the current unix timestamp).
- **`partition` job** — staples a **new divider** into the diary, so the writer never writes on a page without a divider.
- The writer never thinks about dividers. The binder (PostgreSQL) automatically places each line behind the right divider.
- Two files only: `db.py` holds all the SQL, `cron_jobs.py` is the entrypoint you run from cron. Each function explained below, quickly.

---

## db.py — function by function

### The settings (module level)

```python
DB_CONFIG = {...} - reads DB_HOST / DB_PORT / DB_NAME / DB_USER / DB_PASSWORD from .env (load_dotenv loads the file). all five are required
SCHEMA = os.getenv("DB_SCHEMA") - the schema folder name from .env (like partition_demo)
TABLE_NAME = "readings" - the parent table name
WINDOW_SIZE = 600 - one divider per 600 seconds = 10 minutes
```

```python
def get_connection(): - opens one fresh psycopg2 connection using DB_CONFIG. every function below uses it with `with`, so commit and close happen automatically
```

```python
def create_table(): - one-time setup, run by hand, never by cron:
    CREATE TABLE IF NOT EXISTS readings (id BIGSERIAL, unix_ts BIGINT NOT NULL, PRIMARY KEY (id, unix_ts)) PARTITION BY RANGE (unix_ts)
    GOTCHA: the primary key must include the partition column (unix_ts), a plain PRIMARY KEY (id) is rejected by postgres
    IF NOT EXISTS makes it safe to run again and again
```

Run it once on a fresh database like this:

```bash
python -c "import db; db.create_table()"
```

```python
def get_window_bounds(unix_ts): - turns any moment into its 10-minute window:
    start = (unix_ts // WINDOW_SIZE) * WINDOW_SIZE, end = start + WINDOW_SIZE (end excluded)
    the nice part: 10:41 and 10:47 both compute the same window start, so the partition names are always predictable
    this is why the partition job is idempotent - same window = same name every time
```

```python
def create_partition(unix_ts): - the divider maker:
    uses get_window_bounds() to get start/end
    partition_name = readings_p_<start> - the name comes from the window start, so re-runs and cron overlaps are no-ops thanks to IF NOT EXISTS
    CREATE TABLE IF NOT EXISTS readings_p_<start> PARTITION OF readings FOR VALUES FROM (start) TO (end)
    the f-string is allowed here because partition names are identifiers, never user data
```

```python
def insert_timestamp(): - the writer. one INSERT with int(time.time()) as unix_ts:
    VALUES (%s) - the value travels as a parameter, never glued into the text
    and here is the magic: the insert never thinks about dividers. postgres automatically drops the row into the right partition. if we change the partition strategy later, this function never changes
```

---

## cron_jobs.py — function by function

### Logging setup (module level)

```python
LOG_DIR / LOG_FILE - logs/cron_jobs.log next to the file, created if missing
logging.basicConfig(filename=..., level=logging.INFO) - everything goes to the log file, not the terminal (that is what cron wants)
logger = logging.getLogger(__name__) - our own diary of events. info for normal things, exception for errors with full detail
```

```python
def insert_job(): - the cron target for writing a line:
    db.insert_timestamp() then logs "Insert job completed successfully"
    on any error: logger.exception (full traceback into the log) and raise - cron sees a non-zero exit and knows the run failed
```

```python
def partition_job(): - the cron target for stapling the divider:
    now = int(time.time()) - take the current moment
    _, current_end = db.get_window_bounds(now) - find where the current window ends (that is where the next window starts)
    db.create_partition(current_end) - create the NEXT window's partition (the future one), so the writer always has a home before it needs it
    same error pattern: log the traceback, raise, cron sees the failure
```

```python
def main(): - the tiny CLI:
    exactly one argument is required: insert or partition
    no argument / unknown argument -> log error and exit(1) so cron reports it
    this matches a real crontab, two lines:
      * * * * * python cron_jobs.py insert
      */10 * * * * python cron_jobs.py partition
```

```python
if __name__ == "__main__": main() - running the file with a job argument IS the run
```

---

## The wiring that makes it automatic

One-time, on a fresh database (deliberate, by hand — a restart must never run DDL):

```bash
python -c "import db; db.create_table()"
```

Then real cron runs the two jobs on schedule:

```cron
* * * * * cd /path/to/partition_ts && python cron_jobs.py insert
*/10 * * * * cd /path/to/partition_ts && python cron_jobs.py partition
```

Every minute one line is written on the `:00`, and every 10 minutes the next divider is stapled before it is needed.

---

## Why these choices (the short list)

| Choice | What it buys |
|---|---|
| `unix_ts` BIGINT (epoch) | UTC by definition, no timezone drift; window math is exact integer arithmetic |
| Clock-aligned windows (`now // 600 * 600`) | Same window always = same partition name, so `IF NOT EXISTS` makes cron overlaps harmless |
| Look-ahead (create the NEXT window) | An insert landing exactly on a boundary still has a home — no "no partition of relation found for row" |
| Insert never mentions partitions | Loose coupling: change the window size or strategy, `insert_timestamp()` never changes |
| `%s` placeholder for the value | the tick value travels as data; f-strings build only table/partition names (identifiers) |
| `PRIMARY KEY (id, unix_ts)` | postgres requires the partition column inside the primary key |
| Log to file + `logger.exception` | cron has no screen; the log file is the record, and failures exit non-zero so cron mail/alerts fire |

---

## Known limitation to improve next

`partition_job` creates only the **next** window. If cron has not run the partition job for a while (machine off, cron stopped), the **current** window may not exist and the next insert fails. Two easy upgrades:

1. create BOTH the current and the next partition in `partition_job` (loop `get_window_bounds` twice), and/or
2. add a `DEFAULT` partition in `create_table()` as the safety net that catches rows with no matching divider instead of losing them.

---

## Verify it in pgAdmin

```sql
-- which divider holds which rows
SELECT tableoid::regclass AS partition, count(*), min(unix_ts), max(unix_ts)
FROM partition_demo.readings
GROUP BY 1
ORDER BY 1;

-- prove pruning: only one child partition is scanned
EXPLAIN ANALYZE SELECT * FROM partition_demo.readings WHERE unix_ts = EXTRACT(EPOCH FROM now());
```

(replace `partition_demo` with the schema name from .env)
