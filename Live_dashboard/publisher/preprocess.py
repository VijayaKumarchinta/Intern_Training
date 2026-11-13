import hashlib
import json
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SOURCE_FILE = PROJECT_ROOT / "data" / "source" / "Line_Speed_30.xlsx"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

WORKSHEET = "Line_Speed_30"

OUTPUT_FILE = PROCESSED_DIR / "line_speed_30_clean.parquet"
REPORT_FILE = PROCESSED_DIR / "preprocessing_report.json"

EXPECTED_ROWS = 2139
EXPECTED_COLUMNS = 35

def calculate_file_sha256(file_path: Path) -> str:
    sha256 = hashlib.sha256()

    with file_path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            sha256.update(chunk)

    return sha256.hexdigest()

def generate_message_id(
    file_hash: str,
    worksheet: str,
    source_row: int,
) -> str:
    identity = f"{file_hash}:{worksheet}:{source_row}"
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def preprocess() -> None:
    if not SOURCE_FILE.exists():
        raise FileNotFoundError(
            f"Source workbook not found: {SOURCE_FILE}"
        )
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Source: {SOURCE_FILE}")

    file_hash = calculate_file_sha256(SOURCE_FILE)

    df = pd.read_excel(
        SOURCE_FILE,
        sheet_name=WORKSHEET,
        engine="openpyxl",
    )

    original_columns = df.columns.tolist()

    print(f"Records loaded: {len(df)}")
    print(f"Original columns: {len(original_columns)}")

    required_columns = {"Date", "Time"}

    missing_required = required_columns - set(df.columns)

    if missing_required:
        raise ValueError(
            f"Required columns missing: {sorted(missing_required)}"
        )

    if df.empty:
        raise ValueError("The source worksheet contains no records.")

    if df.columns.duplicated().any():
        raise ValueError("Duplicate column names found in source worksheet.")

    if df[["Date", "Time"]].isnull().any().any():
        raise ValueError("Date or Time contains missing values.")

    df["source_row"] = range(2, len(df) + 2)

    timestamp_text = (
        df["Date"].astype(str).str.strip()
        + " "
        + df["Time"].astype(str).str.strip()
    )

    df["event_ts"] = pd.to_datetime(
        timestamp_text,
        format="%m/%d/%Y %H:%M:%S",
        errors="coerce",
    )

    invalid_timestamps = int(df["event_ts"].isna().sum())

    if invalid_timestamps:
        raise ValueError(
            f"Found {invalid_timestamps} invalid event timestamps."
        )

    df["message_id"] = [
        generate_message_id(
            file_hash,
            WORKSHEET,
            int(source_row),
        )
        for source_row in df["source_row"]
    ]

    df["source_file"] = SOURCE_FILE.name
    df["source_sheet"] = WORKSHEET
    df["source_file_sha256"] = file_hash

    df = df.sort_values(
        by=["event_ts", "source_row"],
        kind="stable",
    ).reset_index(drop=True)

    if df["message_id"].duplicated().any():
        raise ValueError("Duplicate message IDs generated.")

    duplicate_rows = int(df[original_columns].duplicated().sum())

    duplicate_timestamps = int(
        df["event_ts"].duplicated().sum()
    )

    missing_values = {
        str(column): int(count)
        for column, count in df[original_columns].isna().sum().items()
    }

    numeric_columns = df[original_columns].select_dtypes(
        include="number"
    )

    all_zero_columns = [
        str(column)
        for column in numeric_columns.columns
        if numeric_columns[column].eq(0).all()
    ]

    intervals = (
        df["event_ts"]
        .diff()
        .dt.total_seconds()
        .dropna()
    )

    interval_statistics = {
        "median_seconds": (
            float(intervals.median()) if not intervals.empty else None
        ),
        "minimum_seconds": (
            float(intervals.min()) if not intervals.empty else None
        ),
        "maximum_seconds": (
            float(intervals.max()) if not intervals.empty else None
        ),
    }

    warnings = []

    if len(df) != EXPECTED_ROWS:
        warnings.append(
            f"Expected {EXPECTED_ROWS} rows, found {len(df)}."
        )

    if len(original_columns) != EXPECTED_COLUMNS:
        warnings.append(
            f"Expected {EXPECTED_COLUMNS} columns, "
            f"found {len(original_columns)}."
        )

    if duplicate_rows:
        warnings.append(
            f"Found {duplicate_rows} duplicate source records."
        )

    if duplicate_timestamps:
        warnings.append(
            f"Found {duplicate_timestamps} duplicate event timestamps."
        )

    if all_zero_columns:
        warnings.append(
            "All-zero numeric columns require source verification: "
            + ", ".join(all_zero_columns)
        )

    df.to_parquet(
        OUTPUT_FILE,
        engine="pyarrow",
        compression="snappy",
        index=False,
    )

    report = {
        "project": "Line Speed 30",
        "source": {
            "file": SOURCE_FILE.name,
            "worksheet": WORKSHEET,
            "sha256": file_hash,
        },
        "output": {
            "file": str(OUTPUT_FILE.relative_to(PROJECT_ROOT)),
            "format": "parquet",
            "compression": "snappy",
        },
        "dataset": {
            "records": len(df),
            "original_columns": len(original_columns),
            "processed_columns": len(df.columns),
            "original_column_names": original_columns,
            "first_event_ts": df["event_ts"].iloc[0].isoformat(),
            "last_event_ts": df["event_ts"].iloc[-1].isoformat(),
            "timezone": "naive - source timezone not established",
        },
        "validation": {
            "missing_values": missing_values,
            "duplicate_source_rows": duplicate_rows,
            "duplicate_event_timestamps": duplicate_timestamps,
            "unique_message_ids": int(df["message_id"].nunique()),
            "invalid_timestamps": invalid_timestamps,
            "all_zero_numeric_columns": all_zero_columns,
            "sampling_interval_seconds": interval_statistics,
            "chronologically_sorted": bool(
                df["event_ts"].is_monotonic_increasing
            ),
        },
        "warnings": warnings,
    }

    with REPORT_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            report,
            file,
            indent=4,
            ensure_ascii=False,
        )

    print("\n========== PREPROCESSING RESULTS ==========")
    print(f"Records processed: {len(df)}")
    print(f"Original columns: {len(original_columns)}")
    print(f"Processed columns: {len(df.columns)}")
    print(f"Unique message IDs: {df['message_id'].nunique()}")
    print(f"Duplicate source rows: {duplicate_rows}")
    print(f"Duplicate timestamps: {duplicate_timestamps}")
    print(f"Chronologically sorted: {df['event_ts'].is_monotonic_increasing}")

    print("\n========== EVENT TIMESTAMP RANGE ==========")
    print("First:", df["event_ts"].iloc[0])
    print("Last: ", df["event_ts"].iloc[-1])

    print("\n========== SAMPLING INTERVAL ==========")
    print(interval_statistics)

    print("\n========== ALL-ZERO NUMERIC COLUMNS ==========")
    print(all_zero_columns if all_zero_columns else "None")

    print("\n========== OUTPUT FILES ==========")
    print(OUTPUT_FILE)
    print(REPORT_FILE)

    print("\n========== WARNINGS ==========")
    print(warnings if warnings else "None")

    print("\nPreprocessing completed successfully.")


if __name__ == "__main__":
    preprocess()
