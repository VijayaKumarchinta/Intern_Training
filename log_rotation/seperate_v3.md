# `rotation_v3.py` — explained separately

**What v3 is:** v2's hybrid **time + size** rotation policy, plus the one thing v2 lacks — **cross-run retention cleanup**. Every run of the script sweeps `logs/` once at startup and deletes log files from runs older than `RETENTION_DAYS = 7`.

> The handler internals (`__init__`, `shouldRollover`, `doRollover`) are identical to v2 and get their line-by-line treatment in `code_explanation.md`. This file focuses on **what v3 adds** and why it's built the way it is. `versions.md` holds the v1→v3 story in brief.

---

## 0. The problem v3 solves

v2 gives every run its own timestamped base file:

```
app_2026-09-29_16-34-07.log          ← run A's live file
app_2026-09-29_16-34-07.log.1..9     ← run A's rotated backups
app_2026-09-29_16-34-09.log          ← run B (2 s later), separate chain
```

That's great for isolation — runs never mix — but it creates a new gap:

- `count=10` (the parent's `backupCount`) prunes **only within one run's chain**.
- Once a run ends, nobody ever revisits its files. Nothing points at them anymore.
- Result: `logs/` grows **forever** — 100 demo runs leave 100 chains on disk.

v3's answer: a **retention policy** (from the `log_rotation/.md` vocabulary: *deletion*) enforced by a startup sweep.

---

## 1. `cleanup_old_runs(logs_dir, retention_days)` — the new function

```python
def cleanup_old_runs(logs_dir, retention_days):
    cutoff = datetime.now() - timedelta(days=retention_days)
    removed = 0

    for path in glob.glob(os.path.join(logs_dir, "app_*.log*")):
        name = os.path.basename(path)
        stem = name[len("app_"):].split(".log")[0]
        try:
            run_started = datetime.strptime(
                stem, "%Y-%m-%d_%H-%M-%S"
            )
        except ValueError:
            continue  # not one of ours — leave it alone

        if run_started < cutoff:
            os.remove(path)
            removed += 1

    return removed
```

**Purpose:** delete every `app_*.log*` file whose run started more than `retention_days` ago, and report how many.

**Step-by-step:**

**Step 1 — Compute the cutoff:**
```python
cutoff = datetime.now() - timedelta(days=retention_days)
```
*Why compute once, outside the loop?* All files in one sweep are judged against the **same** instant. If the cutoff were recomputed per file, a sweep running across a midnight boundary could inconsistently spare/delete files on either side of the line.

**Step 2 — Match candidates:**
```python
for path in glob.glob(os.path.join(logs_dir, "app_*.log*")):
```
*Why the trailing `*` in `app_*.log*`?* One pattern must catch **both** file kinds:

| Pattern suffix | Matches | Example |
|---|---|---|
| `.log` | a run's live file | `app_2026-09-25_08-30-00.log` |
| `.log.N` | its rotated backups | `app_2026-09-25_08-30-00.log.2` |

`app_*.log` alone would miss every backup; `app_*` alone would grab unrelated files starting with `app_`.

**Step 3 — Extract the timestamp ("stem"):**
```python
stem = name[len("app_"):].split(".log")[0]
```
*Why `split(".log")[0]`?* It normalizes both kinds to the same stem:

```
app_2026-09-25_08-30-00.log      → "2026-09-25_08-30-00"
app_2026-09-25_08-30-00.log.2    → "2026-09-25_08-30-00"
```

*Why is that important?* The **whole chain shares one birth time** — the moment the run started. Parsing it from any member of the chain gives the same answer, so the live file and all its backups age together and get deleted together. (The `.log.2` suffix is discarded; we don't care which backup it was.)

**Step 4 — Parse and guard:**
```python
try:
    run_started = datetime.strptime(stem, "%Y-%m-%d_%H-%M-%S")
except ValueError:
    continue
```
*Why `strptime` with the exact format?* It's the inverse of the `strftime('%Y-%m-%d_%H-%M-%S')` that built the filename — same format string, both directions.

*Why the `try/except`?* Defense against **files that match the glob but aren't ours**: `app_backup.log`, `app_test.log.old`, a hand-renamed file. `strptime` raises `ValueError` on a non-matching stem; `continue` skips such files **without deleting them**. A sweep that deletes files it doesn't understand would be dangerous — this one refuses to.

**Step 5 — Delete:**
```python
if run_started < cutoff:
    os.remove(path)
    removed += 1
```
*Why `< cutoff` (strict)?* A file exactly `retention_days` old is kept one more sweep — consistent with the `>=` "rotate on reaching" conservatism in `shouldRollover`.

**Step 6 — Return the count** so the caller can log it (see §3).

### Design decision: filename timestamp, not `mtime`

The age could have come from `os.path.getmtime(path)`. It deliberately doesn't:

| | Filename timestamp (chosen) | `mtime` (rejected) |
|---|---|---|
| Meaning | When the **run** started | When the file was **last touched** |
| Stability | Immutable — it's in the name | Changes on copy/move/restore — a reorganized folder "ages backwards" |
| Chain behavior | All files of a run share one birth time | Each backup has its own mtime — a chain can be deleted **partially** |
| Cost | Parse + `strptime` | None |

The mtime approach's worst failure: a chain whose newest backup was written seconds before cleanup would survive while its older backups die — a broken, half-deleted history. Parsing the name keeps every chain intact.

---

## 2. `TimeAndSizeRotatingHandler` — unchanged from v2

Identical to `rotation.py` / `rotation_v2.py`; full line-by-line in `code_explanation.md`. Quick recap of the three methods:

| Method | Role in v3 |
|---|---|
| `__init__` | Starts `next_rollover_time = now + interval` **before** `super().__init__` (the parent opens the file immediately, so the first record can hit `shouldRollover`) |
| `shouldRollover` | Time check first (`time.time() >= next_rollover_time`), then the parent's size math: seek to END, measure, size the incoming record in bytes, `current + incoming >= maxBytes` |
| `doRollover` | Parent's sequence-numbered rotation, then restart the time window |

**Why reuse it unchanged?** v3's problem isn't inside the handler — the handler is correct within a run. The gap is *between* runs. Fixing it outside the class (a function + one call) keeps the handler simple and its behavior identical across v2/v3 — easy to diff.

---

## 3. Module-level script — what's new in the wiring

```python
RETENTION_DAYS = 7
```
*Why a named constant at the top?* The one knob of the new feature, in the most visible spot. 7 days ≈ one week of history — the same intuition as v2's old `backup_count=7` for daily rotation, now applied across runs.

**Order of operations — this matters:**
```python
log_file = f"logs/app_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"

os.makedirs("logs", exist_ok=True)

removed = cleanup_old_runs("logs", RETENTION_DAYS)

handler = TimeAndSizeRotatingHandler(filename=log_file, ...)
```

1. `log_file` is computed first but touches nothing (pure string).
2. `os.makedirs` runs **before** the sweep — the sweep needs `logs/` to exist for `glob` to match anything.
3. `cleanup_old_runs` runs **before** the handler is constructed.
   *Why before?* If it ran after, the glob `app_*.log*` would still be safe (the new file's timestamp is *now*, never older than the cutoff) — but doing cleanup first means the handler opens its file into an already-pruned directory, and the sweep can never race with an open log file.
4. Handler, formatter, logger — same wiring as v2.

**The sweep's receipt:**
```python
logger.info(f"Retention sweep removed {removed} old run file(s)")
```
*Why log it through the logger itself?* It becomes the **first line of this run's own log file** — the run records what it destroyed, in the format of the very system doing the rotation. `removed` is 0 on a clean directory, so the line is honest either way. The remaining lines (`Application started`, `Processing request`, the 100-message loop) are the same v2 demo traffic.

---

## 4. Runtime flow

**Startup (once per run):**
```
compute log_file name (string only)
        │
        ▼
os.makedirs("logs")              ensure directory exists
        │
        ▼
cleanup_old_runs("logs", 7)      §1
        │
        ├─ glob logs/app_*.log*
        ├─ parse stem → strptime
        ├─ not parseable?  ──► skip (never delete the unknown)
        ├─ run_started < cutoff?  ──► os.remove
        ▼
construct handler (opens log_file)
        │
        ▼
log "Retention sweep removed N old run file(s)"   ← first line of this run
```

**Per record (same as v2):**
```
emit(record)
   → shouldRollover:  time reached?  or  current+incoming ≥ 1024?
   → if yes: doRollover → shift chain, rename to app_<ts>.log.1,
             restart next_rollover_time
   → write line to logs/app_<timestamp>.log
```

---

## 5. Verified behavior (sandbox run)

Seeded `logs/` with two fake old runs, then ran v3:

| File before | Age | After |
|---|---|---|
| `app_2025-09-01_10-00-00.log` | ~13 months | **deleted** |
| `app_2025-09-01_10-00-00.log.1` | ~13 months | **deleted** |
| `app_2026-09-25_08-30-00.log` | 4 days | kept |
| `app_2026-09-25_08-30-00.log.2` | 4 days | kept |
| `app_2026-09-29_16-34-07.log(.1–.9)` | new run | created |

The new run's first log line: `Retention sweep removed 2 old run file(s)` — the count matches exactly the files destroyed.

---

## 6. Remaining limitations (v4 material)

1. **Sweep runs only at startup.** A long-lived process never cleans up mid-run; `app_*.log*` can still exceed retention *while the process is alive*. A production version would schedule the sweep (timer thread, or piggyback it onto `doRollover`).
2. **Deletion, not archiving/compression.** Old history is destroyed outright. Per the `.md` vocabulary, *archiving* (move to dated archive) or *compression* (zip the chain) would keep the analysis value at a fraction of the space.
3. **Same-second collision.** Two runs starting within the same second share a base name and merge into one chain (inherited from v2 — `%S` is the finest granularity).
4. **Single-process assumption.** The sweep deletes by filename alone; it can't tell that another live process is still writing to an old-enough chain. Fine for one process, unsafe for multi-worker setups sharing `logs/`.

---

## 7. Where v3 sits in the progression

```
v1  size only                    ── gap: no time cap
v2  + time cap, isolated runs    ── gap: finished runs accumulate forever
v3  + startup retention sweep    ── gap: sweep only at startup; delete-not-archive
```

The handler never changed after v2 — v3 is proof that the *policy* around a correct handler (retention, deletion) can be layered on without touching the rotation machinery itself.
