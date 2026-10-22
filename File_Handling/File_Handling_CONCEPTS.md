# File Handling Concepts — Intern Training

**Source:** `File_Handling/Handle.py`, `File_Handling/Csv_Handling.py`, `File_Handling/README.md`

> Text files (`Handle.py`) and CSV files (`Csv_Handling.py`) — two scripts covering everyday file work in Python.

---

## 1. File modes — Handle.py

**What:** Opening files in different modes, each with its own error handling.

| Mode | What it does | Error it can raise |
|---|---|---|
| `w` | write / overwrite | — |
| `x` | create-only | `FileExistsError` if the file is already there |
| `a` | append at the end | — |
| `r+` | read and write | `FileNotFoundError` if missing |

**Concepts learned:**
- `x` mode exists specifically to **fail loudly** when a file already exists — "create-if-fresh" semantics.
- Each block sits in its own try/except, so a failure in one mode does not stop the next.
- Running it creates `note.txt` in the folder.

**Pros:**
- `x` gives "make sure this file is fresh" semantics — fails rather than silently overwriting.

**Cons/drawbacks:**
- `w` silently truncates an existing file.
- `r+` requires the file to exist → `FileNotFoundError` if missing.

**Errors encountered & causes:**
- `FileExistsError` with `x` on an existing file → intended behaviour; guard with `try/except`.
- `FileNotFoundError` with `r+` on a missing file → guard separately.

**Use cases:**
- `w`: overwrite/create a file.
- `x`: create a file and fail if it already exists (config/artifact generation — "fresh file" semantics).
- `a`: append logs/records without losing prior content.
- `r+`: read-modify-write when the file must already exist.

**Usage:**
```python
with open("note.txt", "x") as f:
    f.write("fresh")

try:
    with open("note.txt", "r+") as f:
        f.read()
except FileNotFoundError:
    print("missing file")
```

---

## 2. Dict-based CSV access — Csv_Handling.py

**What:** `CSVManager` wraps four CSV operations built on `csv.DictReader` / `csv.DictWriter`.

| Method | What it does |
|---|---|
| `write_csv()` | writes a list of dicts, header from the first dict's keys |
| `read_csv()` | returns rows as dicts |
| `append_csv()` | re-reads the header first, so appends never drift out of column order |
| `count_rows()` | quick row count |

**Concepts learned:**
- Dict-based CSV access beats index-based: **reordering columns cannot silently corrupt row handling**.
- `append_csv()` re-reads the existing header before writing, so appends never drift out of column order.
- Everything is keyed by column name instead of index positions.

**Pros:**
- Resilient to column reordering.
- Self-documenting (column names instead of indices).

**Cons/drawbacks:**
- Slightly more verbose than index-based access.
- `CSVManager` hard-codes an absolute `F:\` path in `__init__` (portability debt).

**Errors encountered & causes:**
- Appending to a CSV with a mismatched header → fixed by re-reading the header before each append.

**Use cases:**
- Any CSV read/write/append where column order may change.
- Logging and data-export scripts.

**Usage:**
```python
manager = CSVManager("data.csv")
manager.write_csv([{"name": "a", "value": 1}])
manager.append_csv([{"name": "b", "value": 2}])
rows = manager.read_csv()
print(manager.count_rows())
```

---

## 3. Supporting files

- `note.txt` — output created by `Handle.py`.
- `dataaaa.csv` — CSV written and extended by `Csv_Handling.py`.
- `README.md` — per-folder documentation.

> `dataaaa.csv` is named with three "a"s — an old typo that stuck. Renaming it is a one-line change in `CSVManager.__init__`.

---

**Quick reference — all file-handling files**
| File | Role |
|---|---|
| Handle.py | Text-file modes `w`/`x`/`a`/`r+`, each with per-mode error handling |
| Csv_Handling.py | `CSVManager` wrapping DictReader/DictWriter CRUD + append + count |
| README.md | Per-folder documentation |

**Status:** 2 scripts + README, runnable standalone.
