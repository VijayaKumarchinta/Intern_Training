# CSV → pandas → Excel

One script, [Excel.py](Excel.py), that takes the raw crypto OHLCV data in
[work.csv](work.csv) (ETHUSD hourly rows) through a cleaning and enrichment
pipeline and saves the result as [Work_sample_processed.xlsx](Work_sample_processed.xlsx).

## The pipeline

```text
read work.csv
  ↓
parse "Date" with format "%Y-%m-%d %I-%p"  (e.g. 2020-03-13 08-PM)
  ↓
split "Symbol" into characters  →  abc becomes ['a', 'b', 'c']
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

## Stories from this file

- **The typo incident:** an earlier version had a column called `Minues`
  instead of `Minute` — caught and called out when the zip was shared. Fixed
  since; the column is now `df["Minutes"]` (from `dt.minute`), which is at
  least a real word.
- `gen_data(n)` accepts a parameter it doesn't use — it just reads `work.csv`.
  It's a leftover from an earlier version that generated rows instead of
  reading a file. Same with the `words` list at the top. Harmless, kept for
  reference.
- The date round-trip matters more than it looks: parse with the exact format
  string, then format back with the same one. If the output format doesn't
  match the source style, every downstream comparison gets confusing.

---
Back to the [repository guide](../README.md).
