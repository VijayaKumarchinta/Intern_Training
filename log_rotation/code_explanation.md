# Code Explanation — `log_rotation/rotation.py` (line by line)

What the file does in one sentence: format every log record as **one-line JSON**,
write it to a **rotating file chain** (`app.log` → `app.log.1` → … → `app.log.10`)
**and** to the **console**, using unix-epoch timestamps.

The file has five parts, explained line by line below:

1. [Imports](#1-imports)
2. [Path constants](#2-path-constants)
3. [`JsonFormatter`](#3-jsonformatter)
4. [`configure_logging`](#4-configure_logging)
5. [Module-level script](#5-module-level-script)

---

## 1. Imports

```python
import json
```
Serializes the log dict to a JSON string. Chosen over manual string building
because it also **escapes** correctly: a message containing quotes, backslashes
or newlines comes out as valid JSON (`\n` inside the string, not a real
line break) — which is what keeps *one record = one line* true.

```python
import logging
```
The standard-library logging framework. Everything here (Formatter, Filter,
Logger, handlers) comes from it.

```python
import pathlib
```
Object-oriented filesystem paths (`Path` instead of string juggling with `os.path`).
Used below to build the log directory path relative to *this file*.

```python
import sys
```
Gives access to `sys.stdout`, so the console handler can be pointed at standard
output explicitly.

```python
from logging.handlers import RotatingFileHandler
```
The stdlib **size-based** rotation handler. When the log file crosses `maxBytes`
it closes it, shifts the backup chain (`app.log.1 → app.log.2 → …`), starts a
fresh `app.log`, and deletes the backup that falls off the end. This is the
entire rotation machinery — imported, not written.

---

## 2. Path constants

```python
BASE_DIR = pathlib.Path(__file__).resolve().parent
```
The directory **this script lives in**. `__file__` is the script's path;
`.resolve()` makes it absolute (and cleans up `..` segments); `.parent` drops
the filename. Pinning paths to the script's folder — instead of the *current
working directory* — means the demo writes to the right place whether run from
the repo root, another drive, or a scheduler.

```python
LOG_DIR = BASE_DIR / "logs"
```
The log directory: `<script folder>/logs`. The `/` operator is pathlib's
path join — same as `os.path.join(BASE_DIR, "logs")`.

```python
LOG_DIR.mkdir(exist_ok=True)
```
Creates the directory *now*, at import time. Two reasons this line must exist:
`FileHandler` opens files but **never creates directories** (without it, the
first log write raises `FileNotFoundError`), and `exist_ok=True` makes it
idempotent — re-running the script on an existing folder doesn't crash.

```python
LOG_FILE = LOG_DIR / "app.log"
```
The base name of the log chain. All runs **append into one chain** —
`app.log` is the live file, `app.log.1`…`app.log.10` its rotated history —
so the log survives across restarts instead of fragmenting per run.
(Passed as a `Path` — handlers accept path-like objects and convert internally.)

---

## 3. `JsonFormatter`

```python
class JsonFormatter(logging.Formatter):
```
Subclasses the base `Formatter` to replace only *how a record renders*.
The logging framework calls `formatter.format(record)` for every record a
handler is about to write; overriding `format` is the single customization
point for output shape.

```python
    def format(self, record):
```
`record` is a `LogRecord` — the framework's internal envelope carrying
everything about one logging event: message + args, level, logger name,
timestamps, exception info. (This override takes no `*args`/`**kwargs`
because it never delegates to `super().format` — it builds the output itself.)

```python
        log_data = {
            "timestamp": record.created,
```
**Unix epoch seconds (float)** — e.g. `1790744286.0384576` = seconds since
1970-01-01 UTC, the fractional part being sub-second precision. `record.created`
is stamped by the framework **at emit time** (`time.time()` was called the
moment `logger.info(...)` executed) — more accurate than formatting time, which
runs slightly later. Numeric timestamps sort instantly, need no timezone
handling (epoch is UTC by definition), and are the native unit of log
pipelines (Elasticsearch/Loki/Datadog). Need milliseconds instead?
`int(record.created * 1000)`.

```python
            "level": record.levelname,
```
The level as text — `"INFO"`, `"WARNING"`, `"ERROR"`. `record.levelno` is the
numeric twin (20/30/40); the string form is what humans and dashboards read.

```python
            "logger": record.name,
```
The name of the logger that emitted the record (`"application"` here).
In bigger apps, child loggers (`application.db`, `application.http`) make this
field a free component/module tag.

```python
            "message": record.getMessage(),
```
The **final** message string. Crucially this is not `record.msg`:
`getMessage()` applies `%`-style interpolation, so
`logger.info("x=%s", x)` logs the rendered `"x=5"`, while `record.msg` would
leak the raw template `"x=%s"`.

```python
        }
```

```python
        if record.exc_info:
```
`exc_info` is `None` for ordinary records and a `(type, value, traceback)`
tuple when the record came from `logger.exception()` or
`logger.error(..., exc_info=True)`. Truthiness = "is there a traceback?"

```python
            log_data["exception"] = self.formatException(
                record.exc_info
            )
```
The stdlib helper renders the traceback into the standard text block. It goes
into the JSON **as a string field** — `json.dumps` will escape its newlines as
`\n`, which is exactly why even a traceback stays on one physical line.

```python
        return json.dumps(log_data)
```
Serialize. `json.dumps` guarantees no bare newline ever appears in its output
(they're escaped inside strings), so the invariant holds: **one record →
exactly one JSON line** — the JSON-Lines format every log shipper tails.

---

## 4. `configure_logging`

```python
def configure_logging():
```
One function that builds and returns the fully wired logger — so any module
(entrypoint, tests, another script) gets identical logging with one call.

```python
    logger = logging.getLogger("application")
```
A **named** logger, not the root. `getLogger` returns a **singleton per name**
(same object every call — this matters two lines down). Naming scopes the
config to this app's records; third-party libraries logging through root are
not touched by anything configured here.

```python
    logger.setLevel(logging.INFO)
```
The logger-level gate — the *first and cheapest* filter in the chain.
`DEBUG` records are dropped here, before any handler is even consulted.
Records at INFO (20) and above pass.

```python
    if logger.handlers:
        return logger
```
**Idempotency guard.** Because `getLogger` is a singleton, calling
`configure_logging()` twice (two imports, a test suite, a notebook rerun)
would run `addHandler` twice — and every message would print/write **twice**.
If handlers already exist, the logger is already configured: return it as-is.
This is the official docs' recommended pattern.

```python
    formatter = JsonFormatter()
```
One formatter instance, shared by both handlers below — file and console show
identical JSON.

```python
    file_handler = RotatingFileHandler(
        filename=LOG_FILE,
```
The live log file — `logs/app.log`. The handler derives the backup names
itself (`app.log.1`, …).

```python
        maxBytes=2 * 1024,
```
Rotate when the file reaches **2 KB**. Deliberately tiny: the demo's JSON
records are ~153 bytes each, so ~13 records fit per file and the 100-record
loop visibly produces ~8 rotations. (Production would use e.g. `10 * 1024 *
1024`.) The `2 * 1024` form documents the unit in the code.

```python
        backupCount=10,
```
Keep **10 rotated backups** (`app.log.1`…`app.log.10`); the 11th-oldest is
deleted on the next rotation. This is the retention knob: with ~13
records/file, the chain holds ~140 records — comfortably more than the demo's
103, so **nothing is lost** in a demo run.

```python
        encoding="utf-8",
```
The file is written as UTF-8 — explicit so byte-size accounting is predictable
and non-ASCII text round-trips on every platform (Windows defaults would
otherwise vary).

```python
    )
```

```python
    file_handler.setFormatter(formatter)
```
Attach the JSON formatter to the file handler — without this the handler would
use the bare default format, and the log file wouldn't be JSON.

```python
    console_handler = logging.StreamHandler(sys.stdout)
```
Second destination: the terminal. `sys.stdout` is passed **explicitly** — a
bare `StreamHandler()` defaults to `sys.stderr`, so this argument is
load-bearing, not decorative.

```python
    console_handler.setFormatter(formatter)
```
Same JSON on the console — one shape everywhere, tooling stays simple.

```python
    logger.addHandler(file_handler)
```
Wire destination 1. From here on, every record that passes the logger level is
offered to this handler.

```python
    logger.addHandler(console_handler)
```
Wire destination 2. **Both** handlers see **every** record that passes the
logger level — this is fan-out, not either/or: the same line lands in the file
and on the terminal.

```python
    logger.propagate = False
```
Stop records from bubbling up to the root logger after this logger's handlers
have processed them. Without it, root's handlers (from a library or
`logging.basicConfig`) would emit the same record **again** — doubled output.

```python
    return logger
```
Hand the configured singleton back so callers can do `logger =
configure_logging()` and start logging immediately.

---

## 5. Module-level script

```python
logger = configure_logging()
```
Configure at **import time** — running the file just works. A real application
would call this once in its entrypoint instead; the function shape exists so
it *can* be called from anywhere.

```python
logger.info("Application started")
logger.info("Processing request")
logger.warning("Something requires attention")
```
Three records at three levels — all pass the INFO gate and are written by
**both** handlers. The last one proves WARNING ≥ INFO also flows through.

```python
for i in range(100):
    logger.info(
        "Testing centralized logging - message number %s",i,
    )
```
The volume generator: 100 more records. Two deliberate details:

- **Lazy `%`-formatting** (`"...%s", i`): the interpolation happens inside
  `getMessage()` *only if the record is actually emitted*. Passing a pre-frozen
  f-string would format even records that get dropped.
- **The loop is what exercises rotation**: ~103 records × ~153 bytes ≈ 15.5 KB
  total against a 2 KB cap → about 8 size rotations, all retained by
  `backupCount=10`. The loop finishes in milliseconds — rotation here is
  purely size-driven, never time-driven.

---

## 6. Runtime flow of one record

```
logger.info("... %s", i)
        │
        ▼
logger-level gate (INFO ≥ INFO → continue)          configure_logging()
        │
        ├─ file_handler     RotatingFileHandler.emit
        │        ├─ shouldRollover: size(record) ≥ 2 KB? ──► doRollover:
        │        │       close app.log, shift .9→.10 … .1→.2,
        │        │       rename app.log→app.log.1, delete old .10, reopen
        │        ▼
        │   JsonFormatter.format
        │        ├─ dict: timestamp(unix)/level/logger/message (+exception?)
        │        └─ json.dumps → '{"timestamp": 1790744286.03, ...}'  one line
        │        ▼
        │   append to logs/app.log
        │
        └─ console_handler  same format → sys.stdout
```

## 7. The numbers (why nothing gets lost)

| Quantity | Value | From |
|---|---|---|
| One JSON record | ~152–154 bytes | measured (timestamp 32 B + message + scaffolding) |
| Records per file | ~13 | `2048 / ~153` |
| Total demo records | 103 | 3 + 100 |
| Expected rotations | ~8 | `ceil(103 / 13) − 1` |
| Chain capacity | ~143 records | `(backupCount + 1) × 13` |
| Lost records | **0** | capacity > emitted |

## 8. Known limitations

- **Size-only rotation.** A quiet app can keep a stale `app.log` forever —
  there is no time trigger (the old hybrid `TimeAndSizeRotatingHandler` lived
  in git history, commit `d5ff415`).
- **Single-process assumption.** Two processes appending to one chain corrupt
  rotation; multi-worker deployments should log to stdout and let the platform
  collect.
- **No cross-run cleanup.** `backupCount` prunes within the chain; old *files*
  elsewhere in `logs/` are never revisited.
- **`json.dumps` can raise** on non-serializable extras; production formatters
  add `default=str` and merge `record.__dict__` extras (request IDs, timings).
