# What I Learned — in Plain Words

| | |
|---|---|
| **Author** | Chinta Vijayakumar |
| **Company** | Triniti Advanced Software Labs Pvt Ltd |
| **Period** | 17 August 2026 – 28 September 2026 (six weeks) |

This is the whole training period reduced to one page: no architecture
diagrams, no scorecards — just what I actually learned, grouped by theme.
The full record lives in [TRAINING_DOCUMENTATION.md](TRAINING_DOCUMENTATION.md);
this page is the short human version.

---

## 1. Python & OOP

- Classes, inheritance in all 5 flavors ([OOP/](OOP/README.md)), and how Python
  decides which parent to check first (MRO).
- Encapsulation: Python's "private" is a gentlemen's agreement, not a locked
  door — `__name` mangling hides it, it doesn't guard it.
- Exceptions belong where failure is *plausible*, not everywhere.

## 2. Files & Data

- Different file modes exist for different promises — `x` mode is "fail loudly
  if it exists."
- Dict-based CSV handling survives column reordering; index-based doesn't.
- With pandas and dates, the format string must be exact both ways —
  approximate parsing is where silent bugs are born. (The `Minues` column typo
  taught: proofread the *output*, not just the code.)

## 3. Databases

- Parameterized queries always (`%s`); f-strings only for table names, never
  data.
- Transactions: commit on success, rollback on failure, `rowcount` to know if
  anything actually happened.
- `CREATE DATABASE` can't run inside a transaction — autocommit is the key.
- Connection pooling + context managers: reusable shopping carts instead of
  buying a new one per customer, and the cart always goes back.

## 4. APIs

- Layering earns itself: routes (HTTP) → services (SQL) → database
  (connections). Flat scripts got unmanageable, so structure came from a real
  problem, not from fashion.
- Honest status codes: a client's mistake is 400/409, not 500. A duplicate
  machine is "conflict," not "server broke."
- Numbers should arrive as numbers — a `Decimal` sneaking through as `"42.0"`
  in JSON taught where types must be fixed.
- A browser only speaks GET; Postman exists because the other verbs need a
  proper client.

## 5. MQTT

- Pub/sub: nobody talks directly, the broker stands in the middle.
- The immediate return code answers "did my *request* go out?" — the callback
  answers "what did the broker *do*?" Both checks matter.
- TLS/mTLS end to end with openssl: who proves what, and why the SAN entry
  saves you from regenerating everything.

## 6. Production Engineering — the big shift

- The dev server with `debug=True` is a wide-open door; a real service gets a
  real front door (waitress).
- Timeouts are chess clocks: a hung query loses in 15 seconds, loudly — not
  silently forever.
- Fail-fast config: every setting is checked at the door before the app wakes
  up.
- Secrets live in `.env`, never in code.
- Log rotation is a diary that archives itself; the disk can't fill.
- Data integrity: only enforce claims you can *prove*. The unique constraint
  multiplied one file ~211× into 11.8M rows — the hash ledger (fingerprint the
  source file) fixed it for good.
- One bad input shouldn't kill a 500k-row batch: validate per row, skip, count.

## 7. Testing

- Tests are smoke alarms — [53 of them](MQTT/Machine_Sensor_API/readme.md),
  run in ~1.5 seconds, no live database needed (a fake pool in place of the
  real thing).
- The alarms caught a real bug the first week: whitespace-only machine names
  slipped through validation.
- Lesson that bit once: services grab `db` at import time, so the test fixture
  must patch it in each service module.
- Testability was the weakest score (2.5/5) until tests existed; now it's the
  strongest habit.

## 8. Working Habits

- Versioned changes: build the fix as a parallel copy, verify both chains
  behave identically, *then* promote. Rollback becomes trivial by construction.
- Review the live tree, not the archive — an independent review flagged code
  that didn't exist in the live files.
- The 8 principles are constraints, not excuses: no change without a concrete
  problem to solve (KISS wins).
- Docs: every README opens with a simple version a non-technical reader can
  follow — if it would embarrass me in review, the code isn't ready.
- Dead code gets deleted (`count_machines()`, YAGNI); copy-pasted logic gets
  unified (one filter builder, one validator set — fix it in one place,
  everywhere fixed).

---

## The one-line version

> I went from *writing code that runs* to *designing code that survives
> failures, concurrency, and review* — and now I can prove it with tests.

---

*For the how and why behind every point above:*
[TRAINING_DOCUMENTATION.md](TRAINING_DOCUMENTATION.md) (full record) ·
[PRODUCTION_COMPARISON.md](PRODUCTION_COMPARISON.md) (code vs 10 production
repos) · [Machine_Sensor_API readme](MQTT/Machine_Sensor_API/readme.md)
(the capstone, simple + engineer).
