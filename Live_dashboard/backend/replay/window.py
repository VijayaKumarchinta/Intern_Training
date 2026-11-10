from pathlib import Path

import pandas as pd

def load_dataset(parquet_path: Path) -> pd.DataFrame:
    if not parquet_path.exists():
        raise FileNotFoundError(f"Parquet file not found: {parquet_path}")
    df = pd.read_parquet(parquet_path)
    df = df.sort_values(
        ["event_timestamp", "source_sequence"], kind="stable"
    ).reset_index(drop=True)
    return df

def select_window(
    df: pd.DataFrame,
    window_start: pd.Timestamp,
    window_end: pd.Timestamp,
) -> pd.DataFrame:
    timestamps = pd.to_datetime(df["event_timestamp"])
    mask = (timestamps >= window_start) & (timestamps < window_end)
    return df.loc[mask].reset_index(drop=True)

def list_windows(
    df: pd.DataFrame, window_minutes: int = 10
) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    timestamps = pd.to_datetime(df["event_timestamp"])
    if timestamps.empty:
        return []
    start = timestamps.min().floor(f"{window_minutes}min")
    end = timestamps.max().ceil(f"{window_minutes}min")
    step = pd.Timedelta(minutes=window_minutes)
    windows = []
    cursor = start
    while cursor < end:
        next_cursor = cursor + step
        windows.append((cursor, next_cursor))
        cursor = next_cursor
    return windows
