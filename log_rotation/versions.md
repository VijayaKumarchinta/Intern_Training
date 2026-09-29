# Log rotation — version progression

Each `rotation_vN.py` is a runnable snapshot of one stage in the design. All three
write to `logs/`, use the same formatter, and log the same sample traffic, so you
can diff them cleanly. Full line-by-line explanation of the handler internals:
`code_explanation.md`. Concepts (rotation vs retention vs archiving, handler
arguments): `.md`.

| Version | File | Policy | What it adds over the previous |
|---|---|---|---|
| v1 | `rotation_v1.py` | Size only | Baseline: plain `RotatingFileHandler` — 1 KB × 10 backups, no time logic |
| v2 | `rotation_v2.py` | Time **or** size | Hybrid `TimeAndSizeRotatingHandler`: manual wall-clock deadline (`next_rollover_time`) checked in `shouldRollover`, window restarted in `doRollover`; per-run timestamped base file (`app_<ts>.log`) so runs never mix |
| v3 | `rotation_v3.py` | + cross-run retention | Startup sweep `cleanup_old_runs()` deletes `app_*.log*` older than `RETENTION_DAYS=7`, age parsed from the filename's timestamp (not mtime) |

## The story in one line each

- **v1** — the stdlib either/or gap: size rotates, but a quiet app keeps a stale `app.log` forever.
- **v2** — closes v1's gap by adding a time cap; sequence-numbered backups can't collide, and timestamped base names isolate runs. Remaining flaw: `count=10` prunes only *within* one run's chain, so finished runs pile up forever.
- **v3** — closes v2's gap with a retention sweep at startup. Remaining gap: cleanup only runs when the process starts, and old files are deleted, not archived/compressed.

## How to run

```bash
python log_rotation/rotation_v1.py   # size-only baseline
python log_rotation/rotation_v2.py   # hybrid time+size
python log_rotation/rotation_v3.py   # hybrid + retention sweep
```

Each run prints nothing to the console (logs go to `logs/` only); inspect with
`ls logs/` and `head logs/app_*.log`.

## Notes

- v2/v3 demo values (`max_bytes=1024`, `interval=10`) are tuned so a single run
  visibly triggers **both** rotation paths; production values would be far larger.
- v1's fixed base name means repeated runs *append* into the same chain — the
  opposite trade-off of v2/v3 (no mixing, but per-run retention only).
- The current `rotation.py` is kept as-is (identical logic to v2); the versioned
  files are the learning progression, not a replacement.
