import pandas as pd

words = ["abc","def","ghi","jkl","mno","pqr","stu","vwx","yza"]
op_proc = "Work_sample_processed.xlsx"

def gen_data(n):
    df = pd.read_csv("work.csv")
    return df

def processed_date(df):
    df["Date"] = pd.to_datetime(df["Date"],format="%Y-%m-%d %I-%p")
    df["Split_out_the_string"] = df["Symbol"].apply(list)
    df["Unix_timestamp"] = df["Date"].astype("int64") // 10**6

    df["Day"] = df["Date"].dt.day
    df["Month"] = df["Date"].dt.month
    df["Year"] = df["Date"].dt.year
    df["Hours"] = df["Date"].dt.hour
    df["Minutes"] = df["Date"].dt.minute
    df["seconds"] = df["Date"].dt.second

    df = df.fillna(0)
    df["Date"] = df["Date"].dt.strftime("%Y-%m-%d %I-%p")

    return df 

def save_to_excel(df,fn):
    with pd.ExcelWriter(fn, engine="openpyxl") as wt:
        df.to_excel(wt, index = False, sheet_name = "Sheet1")
        ws = wt.sheets["Sheet1"]
        for col in ws.columns:
            max_len = 0
            for c in col:
                if c.value is not None:
                    max_len = max(max_len,len(str(c.value)))
            col_let = col[0].column_letter
            ws.column_dimensions[col_let].width = max(max_len + 3,10)

if __name__ == "__main__":
    df_raw = gen_data("work.csv")

    print(f"Raw Data shape: {df_raw.shape}")
    print("\nRaw data is being printing......:")
    print(df_raw)

    print("\nProcessed data is being printing.....")
    df_processed = processed_date(df_raw.copy())
    print(df_processed)
    save_to_excel(df_processed,op_proc)

    print("\nThe processed Data is being printing in Dictionary format")
    data_dict = df_processed.to_dict(orient="records")

    for rec in data_dict:
        print(rec)