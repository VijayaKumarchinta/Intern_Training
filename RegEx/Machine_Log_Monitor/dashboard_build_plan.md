# Live Monitoring Dashboard — Build Plan

Project: `RegEx/Machine_Log_Monitor`  
Target: ERROR-only live monitoring dashboard  
Purpose: standalone study/implementation guide

---

## 1. Objective

Build a dashboard that consumes machine log events and displays live status for only `ERROR`-level events. The dashboard must be productive, observable, and reusable for studying how a real-time monitoring system is architected.

---

## 2. Scope

### In scope
- Continuous tail and buffering of `logs/machine.log`
- Parse log lines and keep only `ERROR`-level events
- Store/queue events for live display
- Expose a dashboard UI with live and historical ERROR events
- Provide status and trend views
- Provide CSV/report export for ERROR rows only

### Out of scope
- Storing DEBUG, INFO, WARNING, CRITICAL, or CRITICAL-only rows
- Full real-time event ingestion from multiple distributed machines
- Complex authentication/role systems
- Enterprise incident-management workflows

---

## 3. Current Code Baseline

The existing repo provides:

| File | Role |
|---|---|
| `log_parser.py` | Regex parser for log lines |
| `log_reader.py` | Line-by-line file reader |
| `jobs.py` | One-line-per-scheduler-run processing |
| `machine_insert.py` | Inserts parsed errors into PostgreSQL |
| `report.py` | Generates `reports/machine_error_report.csv` |
| `scheduler.py` | APScheduler wrapper (one-shot, 1-minute interval) |
| `setup_db.py` | Database/schema setup |
| `machine_errors` table | Existing ERROR-only storage table |

Current limitations:

- Scheduler is one-shot: it exits after the log reaches EOF.
- Reader processes one line per run.
- Reader state is kept in memory but not persistent or rotation-safe.
- No live event streaming.
- No real-time dashboard.
- Logging is present but not structured for dashboard alerting.

---

## 4. Overall Architecture

```
machine.log (continuous log file)
        |
        v
Tail Watcher / Event Feeder
        |
        v
Buffer (bounded, high throughput)
        |
        v
Parser (reuse log_parser.py rules)
        |
        v
Filter: ERROR only
        |
        v
Event Store / Queue
        |
        +--> Dashboard UI (realtime feed)
        +--> Alert renderer
        +--> Report generator (CSV)
        +--> DB storage (retained events)
```

---

## 5. Recommended Dashboard Stack

This stack is recommended for studying and building a practical, small, prod-like dashboard.

### Backend
- **Web framework**: FastAPI (simple, modern, easy to add endpoints)
- **Real-time channel**: Server-Sent Events (SSE)
  - SSE is sufficient for one-way live event pushes to the dashboard
  - Simpler than WebSocket; no need for bidirectional client-server communication at this stage
- **WSGI/alternative**: Uvicorn or Gunicorn as needed for production

### Frontend
- Static HTML + JS
- Lightweight charting: Chart.js or ECharts
- UI layout:
  - Header: machine list, live status, error count, lag
  - Machine panel: per-machine live status and last error
  - Event feed: live ERROR stream
  - Alert panel: active alerts
  - Trend widget: errors per minute
  - Action panel: manual refresh, time-range controls, CSV export

### Database
- PostgreSQL (already used in the project)
- Use the existing `machine_errors` table as the retention base
- Add a lightweight in-memory or Redis cache for realtime reads
- Store indexed fields: `machine_id`, timestamp, `level = ERROR`

### Example component breakdown

| Component | Responsibility |
|---|---|
| `tail_event_store.py` | Continuous log tail + buffering + parsing + ERROR filtering |
| `event_store.py` | Query recent events, machine status, time-range queries |
| `live_feed.py` | Build live SSE/WebSocket feed for the dashboard |
| `dashboard.py` | FastAPI app with `/`, `/api/stream`, `/api/events`, `GET /api/export` |
| `alerts.py` | Alert creation based on ERROR events |
| `report.py` | Generate error CSV from retained events |
| `monitor_service.py` | Run tail + store + dashboard as a single long-lived service |

---

## 6. Data Model

Keep it simple. You only need ERROR data.

### Existing table
```sql
machine_errors
- id SERIAL PRIMARY KEY
- machine_id VARCHAR(50) NOT NULL
- timestamp TIMESTAMPTZ NOT NULL
- unix_timestamp BIGINT NOT NULL
- error_message TEXT NOT NULL
- CONSTRAINT unique_machine_error UNIQUE (machine_id, timestamp, error_message)
```

### Query pattern
```sql
SELECT machine_id, timestamp, error_message
FROM machine_errors
WHERE timestamp >= $1
  AND timestamp <= $2
ORDER BY timestamp DESC;
```

### Indexes
- Primary key index on `id`
- Index on `machine_id`
- Index on `(timestamp DESC)`
- Partial index for recent ERROR events (optional):
```sql
CREATE INDEX idx_machine_errors_recent
ON machine_errors (timestamp DESC)
WHERE id IN (SELECT id FROM machine_errors LIMIT 10000);
```

For production, use a dedicated `machine_events` table with `level` and `severity`, but for the study plan, the existing `machine_errors` table is acceptable.

---

## 7. Event Flow

### Step-by-step

1. **Tail watcher** opens `logs/machine.log` and tracks file size.
2. It seeks to the end and reads new lines as they are appended.
3. New lines are written into a **bounded buffer**.
4. A **drainer** consumes the buffer and parses each line.
5. `parse_machine_log` is reused to extract fields.
6. Only lines where `level == "ERROR"` are kept.
7. Validated errors are inserted into PostgreSQL in **batches**.
8. The dashboard streams recent ERROR events over SSE/WebSocket.
9. The report endpoint regenerates `reports/machine_error_report.csv` with the latest ERROR rows.

### Buffer behavior

| Situation | Handling |
|---|---|
| New line arrives | Add to buffer |
| Buffer full | Drop oldest or throttle writes |
| Burst of lines | Drain efficiently without blocking live UI |
| Parser fails | Log warning; do not crash; retry next tick |
| DB insert fails | Retry with backoff; do not crash in a hard way |

---

## 8. Realtime Implementation Details

### Recommended approach: Server-Sent Events

Rationale:
- Simpler than WebSockets for one-way live updates
- Works in browsers with `EventSource`
- Easy to add to FastAPI
- Less client-side complexity

Endpoint example:
```text
GET /api/stream
```

Client:
```javascript
const source = new EventSource("/api/stream");
source.onmessage = (e) => {
  const event = JSON.parse(e.data);
  // render event in live feed
};
```

Server: push new ERROR events as JSON strings.

### What to push
Keep the stream lightweight:

```json
{
  "event_id": 1234,
  "machine_id": "M102",
  "timestamp": "2026-10-08T15:46:55+05:30",
  "unix_timestamp": 1759916815,
  "message": "Motor overheating"
}
```

### Dashboard panels and update strategy

| Panel | Update source |
|---|---|
| Live event feed | SSE stream |
| Machine status table | Recent event query + last error per machine |
| Error trend | Time-window query, e.g. errors/minute |
| Alert panel | Recent ERROR events with active status |
| CSV export | Endpoint that writes/reads from `reports/machine_error_report.csv` |

---

## 9. UI Layout

### Header
- Machine list / status card
- Today's error count
- Live event count
- Lag indicator (how long dashboard is behind)

### Status Table
| Machine | Status | Last Error Time | Error Count | Notes |
|---|---|---|---|---|
| M102 | Active | current | 3 | live |
| M101 | Active | current | 2 | live |

Status values:
- `live` — recent ERROR present
- `quiet` — no recent ERROR
- `alert` — recent ERROR in feed

### Live Event Feed
- Newest first
- Color-coded by severity: ERROR only
- Click an item to highlight the machine
- Auto-scroll to newest
- Memory-safe: paginate or limit event window

### Alert Panel
- Active alerts = recent ERROR per machine
- Shows machine, timestamp, message, severity

### Trend Widget
- Chart: `errors per minute` over last 10, 60, or 1440 minutes
- Live updated with SSE or periodic refresh

### Export Panel
- Download current `reports/machine_error_report.csv`
- Filtered/queried by time range or machine

---

## 10. Implementation Steps

### Step 1: Add a persistent tail/feed component

Create `tail_watcher.py` or `monitor_service.py`.

Responsibilities:
- Open `logs/machine.log`
- Track file size
- Seek to end
- Read new lines
- Detect EOF
- Handle file rotation if needed

Pseudo-code:

```python
class TailWatcher:
    def __init__(self, file_path, buffer_size=10000):
        self.file_path = file_path
        self.buffer_size = buffer_size
        self.file = None
        self.size = 0

    def open(self):
        self.file = open(self.file_path, "r", encoding="utf-8")
        self.file.seek(self.size)

    def read_new(self):
        line = self.file.readline()
        if line:
            return line
        # wait briefly if nothing new
        time.sleep(0.5)
        current_size = self.file.tell()
        if current_size > self.size:
            self.size = current_size
            return self.file.readline()
        return None
```

### Step 2: Add an event parser and filter

Reuse `log_parser.py`.

```python
from log_parser import parse_machine_log

def is_error_event(parsed):
    return parsed is not None and parsed["level"] == "ERROR"
```

Do not duplicate the regex. Use the existing parser.

### Step 3: Add an event store

Create `event_store.py`.

Responsibilities:
- Save parsed errors to PostgreSQL
- Query recent events
- Query errors by machine
- Query errors in time range
- Provide metrics: total errors, rate, pending alerts

Interface:

```python
class EventStore:
    def save(self, errors: list[dict]) -> int:
        ...

    def recent(self, limit=100, cursor: int | None = None):
        ...

    def by_machine(self, machine_id: str, limit=50):
        ...

    def by_time_range(self, start, end):
        ...

    def metrics(self):
        ...
```

### Step 4: Add a live feed

Create `live_feed.py`.

Responsibilities:
- Keep a list of recent errors
- Broadcast new errors to connected SSE clients
- Bound broadcast memory usage
- Allow heartbeat/lag measurement

Interface:

```python
class LiveFeed:
    def subscribe(self, client):
        ...

    def publish(self, event: dict):
        ...
```

### Step 5: Build the FastAPI dashboard

Create `dashboard.py`.

Endpoints:

| Endpoint | Purpose |
|---|---|
| `GET /` | Serve dashboard UI |
| `GET /api/stream` | SSE live stream of ERROR events |
| `GET /api/events?limit=&cursor=` | Recent ERROR events |
| `GET /api/events/machine/<machine_id>` | Errors for one machine |
| `GET /api/events/time?start=&end=` | Events in time range |
| `GET /api/alerts` | Active alerts |
| `GET /api/metrics` | Counts/health |
| `GET /api/export` | CSV download for errors |

### Step 6: Add alert logic

Create `alerts.py` or add it to `event_store.py`.

- When a new ERROR arrives, mark it as active for that machine
- Group consecutive alerts per machine
- Provide a way to clear/acknowledge

### Step 7: Add CSV export

Reuse `report.py` and keep behavior focused on ERROR rows.

Behavior:
- Write `reports/machine_error_report.csv`
- Header: `Machine ID, Timestamp, Error Message`
- Rows only from recent/retained ERROR events

### Step 8: Add a long-running monitor service

Create `monitor_service.py`.

Responsibilities:
- Start tail watcher
- Start event store
- Start live feed
- Start dashboard
- Handle graceful shutdown

Pseudo-flow:

```python
def main():
    tail = TailWatcher(...)
    store = EventStore(...)
    feed = LiveFeed(...)
    dashboard = Dashboard(...)

    while True:
        line = tail.read_new()
        if line is None:
            continue
        parsed = parse_machine_log(line)
        if parsed is None:
            continue
        if not is_error_event(parsed):
            continue
        store.save([parsed])
        feed.publish(parsed)
        # optionally generate report periodically
```

---

## 11. Productive Dashboard Checklist

### Real-time
- New ERROR lines appear in the feed quickly
- Feed does not re-read old data
- Lag is visible

### Error-only
- No DEBUG/INFO/WARNING/CRITICAL rows shown
- Filters and metrics respect ERROR-only

### Usability
- Machine status table is visible
- Time range filter works
- Auto-refresh or SSE refresh works
- Click-to-highlight machine works

### Data
- Events persist in PostgreSQL
- CSV export is available
- Query window is bounded

### Reliability
- Parser failures do not block the feed
- DB insert failures are retried
- App can restart and continue without losing event position
- Dashboard does not crash on slow network or malformed event

### Output
- `reports/machine_error_report.csv` is regenerated
- Only ERROR rows are included

---

## 12. Performance Targets

| Metric | Target |
|---|---|
| New ERROR line visible in UI | < 1 second for low volume |
| Live feed memory usage | bounded, e.g. < 1MB per 1000 events |
| DB inserts per batch | 25–100 rows per transaction |
| Query performance | < 100ms for recent 1000 rows |
| Resume after restart | avoid duplicate insertion |

When volume increases:
- Increase batch insert size
- Add Redis or in-memory cache
- Partition the events table by timestamp
- Use a worker queue for heavy processing

---

## 13. Monitoring and Observability

Add to dashboard:
- Total ERROR count
- Errors per minute
- Machine count with active errors
- Feed lag
- DB health
- Parser error count
- DB insert failure count

Log format:
```text
timestamp | level | module | event | message
```

Example:
```text
2026-10-12 20:40:01 | INFO | monitor_service | feed_started | log watcher started
2026-10-12 20:40:02 | INFO | monitor_service | errors_saved | 5 errors saved
2026-10-12 20:40:03 | WARNING | monitor_service | parser_error | line skipped
```

---

## 14. Upgrade Path

If you later need more capability:

### From one-shot log to continuous log
- Replace static reader with `tail_watcher`
- Add file rotation handling
- Add persistent offset tracking

### From ERROR-only to multi-level
- Add `level` column to stored events
- Expose severity filters
- Create separate alert rules per level

### From single machine file to distributed logs
- Add log ingestion from multiple files/machines
- Use a time-series DB or streaming store
- Add message queue for fan-out

---

## 15. Acceptance Criteria

The plan is complete when:

1. A dashboard UI is available and loadable.
2. New `ERROR` lines from `logs/machine.log` appear live.
3. Non-ERROR lines are ignored in the dashboard view.
4. Recent errors can be queried by time range and machine.
5. CSV export is regenerated with ERROR rows only.
6. Alert panel shows active machines from recent errors.
7. The system does not crash on parser/DB failures.
8. The architecture clearly separates:
   - tail/feed
   - parse/filter
   - store/query
   - dashboard
   - export/alerting
