# Alternative Approaches for a Simple Machine Log Monitor

This document compares common ways to build a system that watches a log file,
picks out `ERROR` entries, writes them to a database, and produces a CSV report.

We chose the APScheduler + one-shot reader approach. Below is why.

---

## 1. The chosen approach: APScheduler + one-shot line reader

### How it works
- `scheduler.py` uses **APScheduler's `BlockingScheduler`** to run one job
  every minute.
- The job calls `monitor_machine_logs()`, which reads **one line** per run
  from `logs/machine.log`.
- Processing (parse → DB insert → CSV report) happens per line.
- When the reader reaches the last line, it closes the file and returns
  `False`, making the job shut the scheduler down (`wait=False`).

### Flow
```text
scheduler.start() ──► job every 1 min ──► read one line
                                       │
                                       ▼
                            parse → store ERROR in DB → regenerate CSV
                                       │
                                       ▼
                            last line? ──yes─► close reader → shutdown → exit
```

### Pros
- **Simple and explicit.** Each scheduled run does a bounded, predictable
  amount of work: one line.
- **No polling loop in user code.** The scheduler handles timing and
  shutdown instead of a `while True: sleep(60)` loop.
- **Decent for sparse logs.** If the log has a few lines per minute, the job
  wakes up, reads a line, does a little work, and goes back to sleep.
- **Idempotent.** `replace_existing=True`, unique DB constraints, and
  `coalesce=True` make re-runs safe.
- **Graceful exit.** The scheduler stops automatically when the log is done.

### Cons
- **Not a continuous tailer.** Once the last line is read, the scheduler stops
  and new log lines are ignored until it is restarted.
- **Per-run DB connection.** A new PostgreSQL connection opens on every job
  run. Fine for light load, wasteful for high-frequency logs.
- **One line per run.** If the log writes bursts of lines faster than one
  per minute, lines can be missed between runs (no queue to buffer them).

---

## 2. Simple `while True` polling loop

### How it works
```python
while True:
    reader.read_next_line()   # reads until EOF
    if not has_more_lines():
        break
    time.sleep(60)
```

### Pros
- **Minimal dependencies.** No external scheduling library needed.
- **Straightforward control flow.** Easy to reason about.
- **Start/stop controllable.** Can join a background thread or run in
  foreground.

### Cons
- **You own the timing logic.** Sleep-based loops drift over time and make
  shutdown handling more manual.
- **Tight loop risk.** If you `sleep(60)` after every run, a burst of lines
  still needs multiple wake-ups; if you `sleep(0)` or short sleep, CPU goes
  up.
- **No built-in job lifecycle.** Coalesce, max_instances, and graceful
  shutdown are all hand-rolled.

### Verdict
A fine fallback if you want zero extra dependencies, but the scheduler adds
less code over time and gives you scheduling guarantees for free.

---

## 3. `tail -f` style continuous watcher

### How it works
Keep the file handle open and wait for the OS to notify you of new data —
either by:
- blocking on `file.read()` until data arrives, or
- using platform-native APIs (`inotify` on Linux, `ReadDirectoryChangesW` on
  Windows, or a library like `watchfiles` / `pyinotify`).

### Pros
- **True real-time.** Catches every new line as it is written, no missed
  bursts.
- **Low CPU.** The watcher sleeps inside the OS, not in a `time.sleep()`.

### Cons
- **Needs a long-running process.** Cannot stop after one log. You usually
  need a service manager (`systemd`, Docker, `nohup`).
- **Cross-platform complexity.** `inotify`/Windows APIs are platform-bound;
  `watchfiles` adds a dependency.
- **More moving parts.** Retry logic, crash-recovery, and "which lines have I
  seen" state become harder to get right correctly.

### Verdict
Choose this only if the log is written in bursts and you must react
immediately, and if you're comfortable running a persistent watcher.

---

## 4. External tooling (`logrotate`, `lnav`, `fail2ban`, `auditd`)

### How it works
- **logrotate** rotates the file itself (often by renaming + creating a new
  one); the app then re-opens on next start.
- **lnav / fail2ban / auditd** are purpose-built log-analysis/security tools
  that can parse, alert, and report.

### Pros
- **Battle-tested.** These tools are optimized for their specific jobs.
- **No application logic.** The OS or a dedicated tool handles rotation,
  filtering, and alerting.

### Cons
- **Not a custom pipeline.** You cannot easily plug a DB insert and CSV
  report into them without additional glue.
- **Coupling.** Changing behavior means changing external config, not your
  code.
- **Operational overhead.** You manage another daemon/tool.

### Verdict
Only relevant if one of these tools already covers your exact need (e.g., a
security alerting pipeline). Not a fit for a flexible DB + CSV workflow.

---

## 5. Message-queue / event-driven approach (Kafka, RabbitMQ, AWS S3 + Lambda)

### How it works
- The log writer publishes events to a queue.
- A consumer (Lambda, worker, stream processor) picks them up, parses,
  stores to DB, writes CSV.

### Pros
- **Scalable and resilient.** Handles high-throughput and service
  interruptions gracefully.
- **Decoupled.** Producers and consumers do not share state.

### Cons
- **Overkill for one file.** Requires running a broker, network, schemas, and
  monitoring.
- **High operational cost.** Heavy for a "monitor one file and write a CSV"
  task.

### Verdict
Reserve for distributed, high-volume, or multi-producer pipelines.

---

## 6. File-change polling (`os.path.getmtime` + `watchdog`)

### How it works
Poll the file's modification time every N seconds; if it changed, seek to
the end and read new lines (or re-read from a tracked offset).

### Pros
- **Catches new content** without waiting for the scheduler's fixed interval.
- **Simple to implement** with the `watchdog` library.

### Cons
- **Polling overhead** and potential missed writes between polls.
- **No built-in grace period** for the scheduler's one-shot behavior.
- **Still not a continuous tail** unless you manage the offset yourself.

### Verdict
A middle ground between a raw loop and a real watcher, but the scheduler
approach already provides the timing layer more cleanly.

---

## Summary comparison

| Approach | Real-time? | Complexity | Dependencies | Best for |
|---|---|---|---|---|
| **APScheduler + one-shot reader** (chosen) | No (per-minute ticks) | Low | APScheduler, psycopg2 | Light, predictable, simple |
| `while True` polling | No | Low | None | Zero deps, simple control flow |
| `tail -f` / inotify watcher | Yes | Medium | Platform libs | Bursty logs, persistent service |
| External tooling (logrotate, lnav, fail2ban) | Varies | Medium | External daemons | Dedicated analysis/security |
| Message queue / event-driven | Yes | High | Kafka/RabbitMQ/etc. | High-throughput distributed |
| File-change polling (`watchdog`) | Mostly | Low | watchdog | Simple change detection |

---

## Why we chose the APScheduler approach

1. **The requirement is "monitor on a schedule," not "tail forever."** The
   current design stops when the log's last line is read, which matches a
   one-shot batch model. APScheduler's `interval` trigger is the direct fit
   for "run this every minute, stop when done."
2. **Simplicity wins.** APScheduler handles interval timing, idempotency
   (`replace_existing`), single-instance guard (`max_instances`), and
   coalescing (`coalesce`) with a few lines — the same as a manual loop,
   but with guaranteed scheduling semantics.
3. **It's the existing building block.** The rest of the project (reader,
   parser, insert, reporter) is already structured around the scheduler's
   job function. Adding a different runtime would require re-architecting
   the shared reader and retry logic.
4. **Heavy alternatives were avoided by necessity.** A DB + CSV pipeline
   with SQLite/PostgreSQL as the storage target does not benefit from a
   message broker, and the log volume does not justify a `tail -f` or a
   queue.
5. **Trade-off accepted and documented.** The one-shot behavior means the
   scheduler exits at EOF. If future requirements make real-time feeding
   necessary, the natural next step is switching to a `tail -f`-style
   continuous watcher and adding offset-tracking persistence.

---

## If you want different behavior, the switch is straightforward

| Desired behavior | What to change |
|---|---|
| **Continuous, always-on** | Replace the scheduler with a `tail -f`/inotify watcher that keeps the reader open and never shuts down |
| **Immediately on new lines** | Poll `mtime`/size, or use `watchdog`, and batch-read instead of one-line-per-run |
| **Never miss a burst** | Buffer lines in memory/BlockingQueue between runs instead of one-line-per-run |
| **Faster DB writes** | Batch inserts per run (e.g., `executemany`) instead of one statement per line |
| **Fail-safe restart** | Persist the reader's `last_line_position` to a state file, so a restart resumes from where it stopped |

---

## Recommendation

Keep the **APScheduler + one-shot reader** approach for this project. It
matches the current workflow, is the least complex, has the smallest
dependency footprint, and its non-tailing behavior is a documented,
acceptable trade-off that can be revisited later by swapping in a
continuous watcher if the requirement changes.
