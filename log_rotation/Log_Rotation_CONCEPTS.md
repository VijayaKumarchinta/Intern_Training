# Rotating JSON Logging Concepts — Intern Training

**Source:** `log_rotation/code_explanation.md`, `log_rotation/rotation.py`

> One hybrid handler demo: every log record is formatted as **one-line JSON** (unix-epoch timestamp, level, logger name, message, exception block when present), written to a **rotating file chain** (`app.log` → `app.log.1` → … → `app.log.10`) **and** to the console.

---

## 1. The hybrid logging setup

**What the file does in one sentence:** Format every log record as **one-line JSON**, write it to a **rotating file chain** (`app.log` → `app.log.1` → … → `app.log.10`) **and** to the **console**, using unix-epoch timestamps.

**Imports:**
```python
import json          # for the output format
import logging       # standard logging frameworks
import pathlib       # build root directories
import sys           # standard streams (stdin, stdout, stderr)
from logging.handlers import RotatingFileHandler  # size-based rotation triggers
```

**Path constants:**
```python
BASE_DIR = pathlib.Path(__file__).resolve().parent   # current file is root directory
LOG_DIR = BASE_DIR / "logs"                          # logs folder
LOG_DIR.mkdir(exist_ok=True)                         # create if not exists
LOG_FILE = LOG_DIR / "app.log"                       # live log file
```

---

## 2. JsonFormatter

```python
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": record.created,     # unix timestamp
            "level": record.levelname,       # info/warning/error
            "logger": record.name,           # logger name
            "message": record.getMessage(),  # raw text
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)
```

**Concepts learned:**
- Every log record is one-line JSON → machine-parseable for log collectors.
- Timestamp is unix-epoch → unambiguous sorting and comparison.
- `exc_info` carries the exception block when present.

**Pros:**
- JSON-per-line is what log collectors want to see (ELK, Loki, Splunk, etc.).
- Structured fields are queryable instead of free-text.

**Cons/drawbacks:**
- RotatingFileHandler is size-based only — no age-based retention (no timestamps in filenames).
- `configure_logging` must be called before the first log → module-level call.
- Duplicate handler attachment can double-log on re-import.

**Errors encountered & causes:**
- Earlier rotation attempts were split across multiple demos → log lines went missing between demos → fixed by consolidating into one hybrid handler.
- Duplicate handler attachment on re-import → guard with `if logger.handlers: return`.

**Use cases:**
- Any long-running service needing stdout + rotating, parseable logs.
- Front-end for log aggregation (ELK, Loki, Splunk).

**Usage:**
```python
logger = logging.getLogger("application")
logger.setLevel(logging.INFO)
if logger.handlers:
    return logger

formatter = JsonFormatter()
file_handler = RotatingFileHandler(
    filename=LOG_FILE,
    maxBytes=2 * 1024,
    backupCount=10,
    encoding="utf-8",
)
file_handler.setFormatter(formatter)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(console_handler)
logger.propagate = False
return logger
```

---

## 3. Key design notes

| Topic | What was learned |
|---|---|
| Rotation | `RotatingFileHandler.maxBytes` + `backupCount` = a diary that archives itself; the disk can never fill |
| Propagation | `logger.propagate = False` stops records from reaching the root logger |
| Handler dedup | `if logger.handlers: return` guards against duplicate handler attachment on re-imports |
| Format | JSON-per-line is the format log collectors want; free-text logs are for humans only |

**Pros:**
- Structured, machine-parseable output.
- Size-based rotation prevents unbounded log growth.
- Console + file gives immediate response and persistence.

**Cons/drawbacks:**
- No age-based retention (only size-based).
- Must initialise before the first log.
- Duplicate handlers possible on re-import.

**Errors encountered & causes:**
- Split demos → log lines missing → one hybrid handler.
- Duplicate handlers → idempotent attach guard.

**Use cases:**
- Long-running services requiring stdout + rotating structured logs.
- Observability pipelines.

**Usage:**
- One logger per app, one place it is wired in, idempotent attach, `propagate=False`.

---

## 4. Module-level script example

```python
logger = configure_logging()
logger.info("Application started")
logger.info("Processing request")
logger.warning("Something requires attention")
for i in range(100):
    logger.info("Testing centralized logging - message number %s", i)
```

**Concepts learned:**
- `logger.exception(...)` logs the message WITH the full traceback — used in every error path.
- `logger.info(...)` is the normal flow message.

**Pros:**
- Easy to see what is happening and where.

**Cons/drawbacks:**
- `exc_info` must be present to capture exception context.

**Use cases:**
- Application bootstrap + request processing + warnings + loops.

**Usage:**
- Use `logger.exception()` in every `except` block; `logger.info()` for normal flow.

---

**Quick reference — all log_rotation files**
| File | Role |
|---|---|
| rotation.py | One hybrid JSON + rotating handler demo |
| code_explanation.md | Per-folder documentation |

**Status:** 1 script + README, runnable standalone.
