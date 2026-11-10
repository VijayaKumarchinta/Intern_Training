from pathlib import Path
import json
import pandas as pd
from openpyxl import load_workbook
PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = PROJECT_ROOT / 'data' / 'reports'
CANDIDATE_PATHS = [PROJECT_ROOT / 'data' / 'raw' / 'Line_Speed_30.xlsx', PROJECT_ROOT / 'data' / 'Line_Speed_30.xlsx']

def locate_workbook():
    for path in CANDIDATE_PATHS:
        if path.exists():
            return path
    raise FileNotFoundError('Line_Speed_30.xlsx was not found. Expected it under data/raw/ or data/.')

def profile_column(series):
    unique_count = int(series.nunique(dropna=True))
    try:
        constant = series.nunique(dropna=False) <= 1
    except TypeError:
        constant = False
    return {'column': str(series.name), 'dtype': str(series.dtype), 'total_rows': len(series), 'missing_count': int(series.isna().sum()), 'missing_percentage': round(float(series.isna().mean() * 100), 2), 'unique_values': unique_count, 'constant_column': bool(constant), 'sample_values': json.dumps(series.dropna().head(5).tolist(), default=str, ensure_ascii=False)}

def main():
    workbook_path = locate_workbook()
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    print('=' * 65)
    print('LINE SPEED 30 - DATASET PROFILING')
    print('=' * 65)
    print(f'Workbook: {workbook_path}')
    print(f'Size: {workbook_path.stat().st_size:,} bytes')
    workbook = load_workbook(workbook_path, read_only=True, data_only=True)
    sheet_metadata = []
    for worksheet in workbook.worksheets:
        sheet_metadata.append({'sheet_name': worksheet.title, 'max_rows': worksheet.max_row, 'max_columns': worksheet.max_column, 'state': worksheet.sheet_state})
    workbook.close()
    sheets = pd.read_excel(workbook_path, sheet_name=None, engine='openpyxl')
    column_profiles = []
    numeric_summaries = []
    duplicate_summaries = []
    report_lines = []
    report_lines.extend(['# Line Speed 30 - Dataset Profiling Report', '', f'Source workbook: `{workbook_path.name}`', '', '## 1. Workbook inventory', '', '| Worksheet | Rows (including header) | Columns | State |', '|---|---:|---:|---|'])
    for metadata in sheet_metadata:
        report_lines.append(f"| {metadata['sheet_name']} | {metadata['max_rows']} | {metadata['max_columns']} | {metadata['state']} |")
    for sheet_name, df in sheets.items():
        print(f'\nWorksheet: {sheet_name}')
        print('-' * 65)
        row_count, column_count = df.shape
        duplicate_count = int(df.duplicated().sum())
        print(f'Rows: {row_count:,}')
        print(f'Columns: {column_count:,}')
        print(f'Duplicate complete rows: {duplicate_count:,}')
        duplicate_summaries.append({'sheet_name': sheet_name, 'total_rows': row_count, 'duplicate_complete_rows': duplicate_count})
        report_lines.extend(['', f'## 2. Worksheet: {sheet_name}', '', f'- Data rows: {row_count:,}', f'- Columns: {column_count:,}', f'- Duplicate complete rows: {duplicate_count:,}', '', '### Column profile', '', '| Column | Data type | Missing | Missing % | Unique | Constant |', '|---|---|---:|---:|---:|---|'])
        for column in df.columns:
            profile = profile_column(df[column])
            profile['sheet_name'] = sheet_name
            column_profiles.append(profile)
            report_lines.append(f"| {profile['column']} | {profile['dtype']} | {profile['missing_count']} | {profile['missing_percentage']}% | {profile['unique_values']} | {profile['constant_column']} |")
            print(f"{profile['column']!r}: {profile['dtype']}, missing={profile['missing_count']}, unique={profile['unique_values']}")
        numeric_df = df.select_dtypes(include='number')
        if not numeric_df.empty:
            description = numeric_df.describe().T.reset_index()
            description = description.rename(columns={'index': 'column'})
            description.insert(0, 'sheet_name', sheet_name)
            numeric_summaries.append(description)
        temporal_candidates = [str(column) for column in df.columns if any((token in str(column).lower() for token in ('date', 'time', 'millitm', 'timestamp')))]
        report_lines.extend(['', '### Possible date/time columns', '', ', '.join((f'`{column}`' for column in temporal_candidates)) if temporal_candidates else 'No obvious candidates found.', ''])
        print('Possible date/time columns:', temporal_candidates or 'None identified')
    pd.DataFrame(sheet_metadata).to_csv(REPORT_DIR / 'sheet_inventory.csv', index=False, encoding='utf-8-sig')
    pd.DataFrame(column_profiles).to_csv(REPORT_DIR / 'column_profile.csv', index=False, encoding='utf-8-sig')
    pd.DataFrame(duplicate_summaries).to_csv(REPORT_DIR / 'duplicate_summary.csv', index=False, encoding='utf-8-sig')
    if numeric_summaries:
        pd.concat(numeric_summaries, ignore_index=True).to_csv(REPORT_DIR / 'numeric_summary.csv', index=False, encoding='utf-8-sig')
    report_path = REPORT_DIR / 'dataset_profile.md'
    report_path.write_text('\n'.join(report_lines), encoding='utf-8')
    print('\n' + '=' * 65)
    print('PROFILING COMPLETED')
    print(f'Reports saved in: {REPORT_DIR}')
    print('=' * 65)
if __name__ == '__main__':
    main()
