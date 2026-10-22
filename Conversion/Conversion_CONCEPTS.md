# Conversion Concepts — Intern Training

**Source:** `Conversion/README.md`, `Conversion/Excel.py`

> One script, `Excel.py`, that takes raw crypto OHLCV data (`work.csv`) through a cleaning and enrichment pipeline and saves the result as `Work_sample_processed.xlsx`.

---

## 1. CSV → pandas → Excel pipeline

**What (the pipeline):**

```
read work.csv
  ↓
parse "Date" with format "%Y-%m-%d %I-%p"  (e.g. 2020-03-13 08-PM)
  ↓
split "Symbol" into characters  →  abc becomes ['a','b','c']
  ↓
unix timestamp (ms) from the parsed date
  ↓
pull out Day / Month / Year / Hours / Minutes / seconds
  ↓
fillna(0) for missing values
  ↓
format Date back to "%Y-%m-%d %I-%p" so the output matches the input style
  ↓
write the Excel file with auto-sized columns (openpyxl)
  ↓
print every row as a dict — df.to_dict(orient="records")
```

**Concepts learned:**
- Date round-trips need the **exact** format string both ways (`%Y-%m-%d %I-%p`); approximate parsing is where silent data bugs begin.
- `df.astype("int64") // 10**6` converts datetime64 nanoseconds → Unix milliseconds.
- Column-dimension sizing via `ws.column_dimensions[col.column_letter]` makes generated spreadsheets actually readable.
- `gen_data(n)` accepts a parameter it doesn't use — a leftover from an earlier version that generated rows instead of reading a file.

**Pros:**
- pandas makes heterogeneous CSV cleaning + enrichment readable and concise.
- Deterministic date round-trip keeps the output schema stable.
- Excel export with openpyxl supports auto-sized columns for readability.

**Cons/drawbacks:**
- Sensitive to format-string mismatches → silent data corruption.
- `gen_data(n)` has a dead parameter (leftover debt).
- Pipeline is tightly coupled to `work.csv`'s exact shape.

**Errors encountered & causes:**
- `Minues` / `Minute` column typo in Excel output → caught in review → fixed to `Minutes` from `dt.minute`.
- Date round-trip mismatches → silent downstream comparison bugs → fixed by using the exact same format string for parse and format.

**Use cases:**
- Financial / time-series CSV cleaning + reporting.
- Excel generation from DataFrames.
- Timestamp normalisation and human-readable date formatting.

**Usage:**
```python
df = pd.read_csv("work.csv")
df["Date"] = pd.to_datetime(df["Date"], format="%Y-%m-%d %I-%p")
df["unix_ms"] = df["Date"].astype("int64") // 10**6
df["Symbol"] = df["Symbol"].apply(list)
df["Minutes"] = df["Date"].dt.minute
df = df.fillna(0)
df["Date"] = df["Date"].dt.strftime("%Y-%m-%d %I-%p")
# then Excel export with openpyxl + auto-sized columns
```

---

## 2. Lessons from this file (the why)

- **The date round-trip matters more than it looks:** parse with the exact format string, then format back with the same one. If the output format doesn't match the source style, every downstream comparison gets confusing.
- **Proofread generated column names:** an earlier version had a `Minues` typo — caught and called out at review. Fixed since; the column is now `df["Minutes"]` from `dt.minute`.
- **Remove dead parameters:** `gen_data(n)` accepts a param it doesn't use — a leftover from an earlier version. Clean it up.

---

**Quick reference — all conversion files**
| File | Role |
|---|---|
| Excel.py | CSV → pandas → Excel pipeline |
| README.md | Per-folder documentation |

**Status:** 1 script + README, runnable standalone.
