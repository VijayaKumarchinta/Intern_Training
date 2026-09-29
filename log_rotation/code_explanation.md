# Code Explanation — `log_rotation/rotation.py` (function-wise)

A working demo of a **hybrid log rotation policy**: the log file rolls over when it gets too big **or** when the time interval elapses — whichever happens first.

**Functions covered:**

| # | Function / Method | Class / Scope | One-line role |
|---|---|---|---|
| 1 | `__init__` | `TimeAndSizeRotatingHandler` | Start the time window, then initialize the size-based parent |
| 2 | `shouldRollover` | `TimeAndSizeRotatingHandler` | Decide per-record: rotate by time **or** by size |
| 3 | `doRollover` | `TimeAndSizeRotatingHandler` | Run the parent's rotation, then restart the time window |
| 4 | *(module-level script)* | top level | Wire up handler + formatter + logger, emit sample logs |

---

## 0. Why this file exists (context for all functions)

Python's standard library gives you two rotation handlers, but they are **either/or**:

| Handler | Rotates on | Blind spot |
|---|---|---|
| `RotatingFileHandler` | File size | No time cap — a quiet app can keep a stale `app.log` forever |
| `TimedRotatingFileHandler` | Time interval | One runaway day can produce a multi-GB `app.log` |

`TimeAndSizeRotatingHandler` inherits the **size** logic from `RotatingFileHandler` and adds the **time** logic by hand, closing the gap in each.

---

## 1. `TimeAndSizeRotatingHandler.__init__`

```python
def __init__(
    self,
    filename,
    max_bytes,
    count,
    interval=1,
    encoding="utf-8",
):
    self.interval = interval
    self.next_rollover_time = time.time() + interval

    super().__init__(
        filename=filename,
        maxBytes=max_bytes,
        backupCount=count,
        encoding=encoding,
    )
```

**Purpose:** accept both size and time config; start the time window, hand the rest to the parent.

**Line-by-line:**

| Line | Why |
|---|---|
| `self.interval = interval` | Seconds between forced time-based rotations. Kept as an attribute so `doRollover` can restart the window without re-deriving it. |
| `self.next_rollover_time = time.time() + interval` | **Must run before `super().__init__`** — the parent opens the log file immediately (no `delay`), so the very first record can reach `shouldRollover` right after construction. `shouldRollover` reads `next_rollover_time`; if the attribute didn't exist yet, the first log line would crash with `AttributeError`. |
| `super().__init__(...)` | Delegates all size-based setup (file open, sequence-numbered backups `app_<ts>.log.1`, `app_<ts>.log.2`, …, oldest-backup deletion) to `RotatingFileHandler` instead of reimplementing it (DRY). The local `count` maps straight to the parent's `backupCount` parameter. Note there is **no `when`/`interval` passed** — those parameters belong to the *Timed* handler, which isn't used here. |

**Parameter choices:**

| Parameter | Value in demo | Why |
|---|---|---|
| `max_bytes` | `1024` (1 KB) | Tiny on purpose — a short demo loop actually triggers size rotation within seconds |
| `count` | `10` | Keeps the last 10 backups per run file, then auto-deletes the oldest — passed straight to the parent's `backupCount` |
| `interval` | `10` (seconds) | Short window so the time-based trigger is visible in the same demo run |
| `encoding` | `"utf-8"` | Required for correct byte-size math in `shouldRollover` (see §2) |

---

## 2. `TimeAndSizeRotatingHandler.shouldRollover`

```python
def shouldRollover(self, record):
    if time.time() >= self.next_rollover_time:
        return 1
    if self.maxBytes <= 0:
        return 0

    if self.stream is None:
        self.stream = self._open()

    self.stream.seek(0, os.SEEK_END)

    current_size = self.stream.tell()

    message = self.format(record)
    message_size = len(
        (message + self.terminator).encode(
            self.encoding or "utf-8"
        )
    )

    return current_size + message_size >= self.maxBytes
```

**Purpose:** the per-record decision point. The logging framework's contract: `emit()` calls this before every write; truthy return → `doRollover()` runs. Overriding only this is the minimal intervention.

**Step-by-step (each block = one decision):**

**Step 1 — Time check (manual):**
```python
if time.time() >= self.next_rollover_time:
    return 1
```
*Why manual instead of `super().shouldRollover(record)`?* The parent here is the **size-based** handler — it has no time logic to delegate to. One wall-clock comparison against the deadline set in `__init__` (and restarted in `doRollover`) *is* the whole time policy. If time says "rotate", we're done — no size math needed.

**Step 2 — Disabled guard:**
```python
if self.maxBytes <= 0:
    return 0
```
*Why?* `<= 0` means "size limit disabled" — skip the size math entirely instead of misreading it as "always rotate". Note it reads the parent's attribute `maxBytes` (camelCase) directly — no duplicate `max_bytes` copy is kept, unlike a design that stores its own.

**Step 3 — Lazy stream open:**
```python
if self.stream is None:
    self.stream = self._open()
```
*Why?* The stream can be `None` after a delay-open or a rollover that closed the file. `seek()` on `None` would crash, so open first.

**Step 4 — Measure true file size:**
```python
self.stream.seek(0, os.SEEK_END)
current_size = self.stream.tell()
```
*Why seek before measuring?* `tell()` returns the **cursor** position, not the file size. If anything left the cursor elsewhere, we'd compare against a wrong number. `SEEK_END` pins the cursor to the true byte count. Safe because the file is opened in append mode — writes land at the end anyway.

**Step 5 — Size the incoming record in bytes:**
```python
message = self.format(record)
message_size = len((message + self.terminator).encode(self.encoding or "utf-8"))
```
*Why encode instead of `len(message)`?* The file is UTF-8 on disk, so usage is in **bytes**, but `len(str)` counts **characters**. Non-ASCII text can be 2–4× larger on disk. Encoding with the handler's own encoding gives the true cost; `or "utf-8"` covers `encoding=None`.
*Why `+ self.terminator`?* The newline is also written to disk — counting it stops the file creeping past the cap one newline at a time.
*Why the incoming record at all?* Without `current + incoming`, a file at 1,023 bytes would admit one more 200-byte record and overshoot. Checking before the write keeps files **under** budget; `>=` is the conservative choice (rotate on *reaching* the cap).

**Step 6 — Verdict:**
```python
return current_size + message_size >= self.maxBytes
```
Returns `1`/`0` — the stdlib convention for `shouldRollover`.

---

## 3. `TimeAndSizeRotatingHandler.doRollover`

```python
def doRollover(self):
    super().doRollover()
    self.next_rollover_time = time.time() + self.interval
```

**Purpose:** run the parent's rotation (close the file, shift backups `app_<ts>.log.N-1 → app_<ts>.log.N`, rename the live file to `app_<ts>.log.1`, delete the one that falls off the end, reopen) — then restart the time window.

*Why reset after `super()`?* A rotation can be triggered by **size** alone, long before the deadline. Without the reset, `next_rollover_time` would still hold the old deadline — every record after a size rotation would instantly re-trigger rotation until the original window expired, shredding backups one per message. Resetting **after** the parent call (which closes/reopens the file) re-anchors the window to the freshly opened file.

*Why is the naming safe here?* Because the parent is `RotatingFileHandler`, backups are sequence-numbered (`app_<ts>.log.1` … `app_<ts>.log.10`), so any number of rotations within a run can never collide or overwrite each other — the exact failure mode a *Timed*-parent design suffers from. And because the base name carries the run's start timestamp, separate runs never share a chain at all.

---

## 4. Module-level script (not a function — the wiring)

```python
log_file = (
    f"logs/app_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
)
```
*Why a timestamped filename?* Every run gets its **own** base file (`app_2026-09-29_15-59-21.log`): runs never append into — or continue — another run's log, so there is no cross-run mixing at all, and the filename doubles as a run identifier. `%S` granularity means two runs must start in different seconds to be distinct. It's pure string formatting — no file is touched yet — so computing it before `os.makedirs` is safe. The `datetime` name comes from the top-of-file import.

```python
os.makedirs("logs", exist_ok=True)
```
*Why?* `FileHandler` does **not** create directories — without this the first `_open()` raises `FileNotFoundError`. `exist_ok=True` makes it idempotent.

```python
handler = TimeAndSizeRotatingHandler(
    filename=log_file,
    max_bytes=1024,
    count=10,
    interval=10,
    encoding="utf-8",
)
```
*Why explicit `encoding`?* It matters twice: the file is written as UTF-8 **and** `shouldRollover` uses the same encoding to count bytes.
*Why `interval=10`?* There is no `when` parameter in this design — `interval` is plain **seconds**, because the time check is a manual comparison. 10 seconds makes both rotation triggers observable in one demo run.

```python
formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
handler.setFormatter(formatter)
```
*Why this format?* Pipe-delimited plain text (`asctime | level | logger | message`) is trivially `grep`-/`awk`-able in a terminal — no JSON tooling needed.
*Why set it on the handler?* `shouldRollover` calls `self.format(record)` to measure the incoming record — the size math depends on this formatter being attached.

```python
logger = logging.getLogger("application")
logger.setLevel(logging.INFO)
logger.addHandler(handler)
logger.propagate = False
```
*Why a named logger instead of the root?* The root logger also captures every third-party library's records. A named logger scopes the config. `INFO` hides debug noise; `propagate = False` stops records bubbling to root and being logged twice.

```python
logger.info("Application started")
logger.info("Processing request")
logger.warning("Something requires attention")

for i in range(100):
    logger.info(f"Testing log rotation - message number {i}")
```
*Why the 100-iteration loop?* Each formatted line is ~90 bytes (timestamp + level + logger name + message + newline), so against `max_bytes=1024` the cap is crossed roughly every 11 records — several size rotations — while 100 records also span the 10-second window, exercising the time trigger too.

---

## 5. Runtime flow of one record

```
logger.info("Testing log rotation - message number i")
        │
        ▼
   emit(record)
        │
        ▼
shouldRollover(record)          §2
        │
        ├─ time.time() ≥ next_rollover_time? ──► rotate
        ├─ maxBytes <= 0? ─────────────────► no rotation
        ├─ stream open?  ── open if None
        ├─ seek to END, measure current size
        ├─ current + incoming ≥ 1024 bytes? ► rotate
        ▼
   format(record)               → formatted text line
        │
        ▼
   write line to logs/app_<timestamp>.log

(rotation, if any) ──► doRollover()            §3
        │
        ├─ super().doRollover()  → close, shift backups,
        │                          rename to app_<ts>.log.1, reopen
        └─ next_rollover_time = now + interval  → window restarts
```

---

## 6. Known limitations (worth fixing before production)

- **Deadline is runtime-anchored, not calendar-anchored.** `next_rollover_time = now + interval` means "rotate every N seconds of process life". If you wanted daily-at-midnight semantics, compute the deadline from the clock (as `TimedRotatingFileHandler.when="midnight"` does) instead of a fixed offset.
- **Rotation only happens on the next record.** `shouldRollover` runs when a record arrives; a process that logs nothing for an hour rotates *late*, on the next message, not at the deadline. Strictly on-schedule rotation would need a timer thread or a cron-triggered `doRollover()`.
- **No cross-process safety.** The size measurement reads the in-memory stream of *this* handler; another process appending to the same file isn't accounted for. Fine for a single-process app, not for multi-worker deployments sharing one log path.
- **Retention is per-run — finished runs accumulate forever.** `count=10` prunes only within one timestamped chain (`app_<ts>.log.1`–`.10`). Each run starts a new base name, so files from earlier runs are never revisited: no overlap, but also no garbage collection. A production version needs a cleanup pass (e.g. delete or zip `logs/app_*.log*` older than N days).

None of the first three affect the demo; the fourth appears only across repeated runs — all are the gaps between a demo and a production-grade handler.

---

## 7. Relation to the project

`MQTT/Machine_Sensor_API/utils/logger.py` uses the plain size-only `RotatingFileHandler` (10 MB × 5 backups). This demo is the prototype of the hybrid handler described in `log_rotation/.md`: the same size policy plus a wall-clock cap. Because backups are sequence-numbered and `doRollover` resets the window, it can replace the API's file handler as-is for a time + size policy.
