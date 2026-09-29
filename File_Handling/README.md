# File Handling Practice

Two scripts covering everyday file work in Python — opening files in different
modes, dealing with the errors that come with it, and handling structured CSV data.

## [Handle.py](Handle.py) — text files and modes

| Mode | What it does | Error it can raise |
|---|---|---|
| `w` | write / overwrite | — |
| `x` | create-only | `FileExistsError` if the file is already there |
| `a` | append at the end | — |
| `r+` | read and write | `FileNotFoundError` if missing |

Each block sits in its own try/except, so a failure in one mode does not stop
the next one. Running it creates `note.txt` in this folder.

One thing this taught me the hard way: `"x"` is the only mode whose whole job
is to fail loudly when the file already exists. It feels annoying until you
need "make sure this file is fresh" semantics.

## [Csv_Handling.py](Csv_Handling.py) — CSV through a class

`CSVManager` wraps the four operations I kept repeating:

- `write_csv()` — writes a list of dicts, header taken from the first dict's keys
- `read_csv()` — returns rows as dicts
- `append_csv()` — re-reads the header first, so appends never drift out of
  column order
- `count_rows()` — quick row count

It uses `csv.DictReader` / `csv.DictWriter`, so everything is keyed by column
name instead of index positions — much harder to break by reordering columns.

The practice file is called `dataaaa.csv` — three a's, an old typo that stuck.
Renaming it is a one-line change in `CSVManager.__init__`.

## Supporting files

- `note.txt` — output created by Handle.py
- `dataaaa.csv` — CSV written and extended by Csv_Handling.py

---
Back to the [repository guide](../README.md).
