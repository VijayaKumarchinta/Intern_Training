import pandas as pd
import matplotlib.pyplot as plt

orders = pd.read_csv("orders.csv", parse_dates=["created_at"])
print(orders)

customers = pd.read_csv("customers.csv")
print(customers)

orders.info()
print(orders.isna().sum())

orders["total"] = pd.to_numeric(orders["total"], errors="coerce")
print(orders["total"])

orders["status"] = orders["status"].str.strip().str.lower()
print(orders["status"])

orders = orders.drop_duplicates(subset="id").dropna(subset=["total"])
print(orders)

customers["city"] = customers["city"].fillna("Unknown").str.title()
print(customers["city"])

paid = orders.query("status == 'paid'")
print(paid)

merged = paid.merge(customers, left_on="customer_id", right_on="id",
                    how="left", suffixes=("", "_cust"), validate="many_to_one")
print(merged)

report = (merged.groupby("city", as_index=False)
                .agg(orders=("id", "count"), revenue=("total", "sum"))
                .query("orders >= 5")
                .sort_values("revenue", ascending=False))
print(report)

monthly = paid.set_index("created_at")["total"].resample("MS").sum()
print(monthly)

monthly.plot(title="Monthly revenue")
plt.tight_layout()
plt.savefig("monthly_revenue.png", dpi=120)
plt.show()
report.to_csv("city_report.csv", index=False)
print("Saved city_report.csv and monthly_revenue.png")