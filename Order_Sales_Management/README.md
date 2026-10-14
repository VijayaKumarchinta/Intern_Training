# Order and Sales Management Application

A small web app that simulates how an online store handles orders and sales.

You can place orders, track their status, catch duplicate submissions, and see sales reports by product and by date.

**Tech stack:** Vue.js (screens) + Flask (API) + PostgreSQL (data)

---

## What it does

| Feature | In plain words |
|---|---|
| **Manage orders** | Create, view, list and edit orders |
| **Validate orders** | Rejects bad input (negative quantity, wrong date, etc.) with a clear message |
| **Calculate totals** | Total = unit price x quantity, always calculated by the server |
| **Track status** | Pending, Shipped, Delivered, Returned, Cancelled, with rules on what can change to what |
| **Catch duplicates** | Stops double-clicks and retries from creating the same order twice |
| **Sales reports** | Sales grouped by product and by date, with gross and net figures |

---

## How it fits together

```text
  Vue.js (browser)  --->  Flask API  --->  PostgreSQL
   screens & forms        rules & logic      orders table
```

| Part | Job |
|---|---|
| **Frontend (Vue.js)** | Forms, order list, status badges, report tables. It never decides totals. |
| **server (Flask)** | Checks every request, calculates totals, applies status and duplicate rules. |
| **Database (PostgreSQL)** | Stores orders and runs the report queries. |

---

## Quick start (Windows / PowerShell)

**You need:** Python 3.11+, Node.js 18+, PostgreSQL 14+

### 1. Set up the database

The app uses your existing `machine_monitor_db` database. No new database is needed. Run the schema script once:

```powershell
psql -U postgres -d machine_monitor_db -f server\sql\schema.sql
```

This creates a separate `sales_schema` schema with the `orders` table, an order-ID sequence and indexes. Your existing tables stay untouched, because everything lives inside `sales_schema`.

### 2. Configure the server

```powershell
cd server
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item ..\.env.example .env
```

Open `.env` and fill in your own values (see [Configuration](#configuration)).

### 3. Load the sample data (optional)

```powershell
python scripts\load_orders.py --csv ..\data\Online-Store-Orders-Updated.csv
```

The loader prints a summary and saves unusable rows to `data\rejected_orders.csv`. See [About the sample data](#about-the-sample-data).

### 4. Start the server

```powershell
python run.py
```

API runs at `http://localhost:5000`. Check it: `http://localhost:5000/api/health`

### 5. Start the frontend

```powershell
cd ..\frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

---

## Configuration

Settings live in `server/.env`. **Never commit this file.** It is already in `.gitignore`.

| Setting | What it is | Example |
|---|---|---|
| `DB_HOST` | Database server | `localhost` |
| `DB_PORT` | Database port | `5432` |
| `DB_NAME` | Existing database | `machine_monitor_db` |
| `DB_USER` | Database user | `postgres` |
| `DB_PASSWORD` | Database password | *(your own)* |
| `DB_SCHEMA` | Schema holding the tables | `sales_schema` |

---

## How an order works

### The order fields

| Field | Rule |
|---|---|
| `customer_id` | Like `C0001` (letter C plus 4 or more digits) |
| `product` | Required text, for example `Laptop` |
| `quantity` | Whole number greater than 0 |
| `unit_price` | Number, 0 or more, up to 2 decimals |
| `order_date` | `YYYY-MM-DD`, a real date, not in the future |

New orders always start as **Pending**. You cannot send a total. The server calculates it.

### Status rules

```text
Pending   -->  Shipped  or  Cancelled
Shipped   -->  Delivered  or  Returned
Delivered -->  Returned
Cancelled, Returned  =  final (cannot change)
```

Anything else is rejected with `409 INVALID_STATUS_TRANSITION`.

Only an admin (using `ADMIN_API_TOKEN`) can change a status or edit an order. Orders can be edited only while they are **Pending**.

### Duplicate protection

Every create request must include an `Idempotency-Key` header. Use a new random value (UUID) for each new order.

| What you send | What happens |
|---|---|
| New key | Order is created (`201`) |
| Same key, same data (retry) | You get the original order back (`200`), with no second order |
| Same key, different data | Rejected (`409 IDEMPOTENCY_KEY_REUSED`) |
| New key, but identical customer, product, quantity, price and date to an existing order | Rejected (`409 DUPLICATE_SUSPECTED`). If it really is a repeat order, resend with `"allow_duplicate": true` |

---

## API guide

Base URL: `http://localhost:5000`

| Method | Endpoint | What it does | Admin only |
|---|---|---|---|
| POST | `/api/orders` | Create an order | No |
| GET | `/api/orders` | List orders (filters: `status`, `customer_id`, `start_date`, `end_date`, `page`, `page_size`) | No |
| GET | `/api/orders/<id>` | Get one order with its total | No |
| PATCH | `/api/orders/<id>` | Edit a Pending order (`product`, `quantity`, `unit_price`) | Yes |
| PATCH | `/api/orders/<id>/status` | Change status | Yes |
| GET | `/api/reports/sales/by-product` | Sales per product | No |
| GET | `/api/reports/sales/by-date` | Sales per day (`start_date`, `end_date`) | No |
| GET | `/api/health` | Is the server running? | No |

Admin requests need the header `Authorization: Bearer <ADMIN_API_TOKEN>`.

### Example: create an order (PowerShell)

```powershell
$body = @{
  customer_id = "C1203"
  product     = "Laptop"
  quantity    = 2
  unit_price  = "500.00"
  order_date  = "2026-10-14"
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://localhost:5000/api/orders `
  -ContentType "application/json" `
  -Headers @{ "Idempotency-Key" = [guid]::NewGuid().ToString() } `
  -Body $body
```

Response:

```json
{
  "data": { "order_id": "ORD1203", "status": "Pending", "total": "1000.00" }
}
```

### Example: ship an order

```powershell
Invoke-RestMethod -Method Patch -Uri http://localhost:5000/api/orders/ORD1203/status `
  -ContentType "application/json" `
  -Headers @{ Authorization = "Bearer $env:ADMIN_API_TOKEN" } `
  -Body '{"status":"Shipped"}'
```

### Errors

Every error looks the same:

```json
{ "error": { "code": "VALIDATION_ERROR", "message": "quantity must be a positive integer." } }
```

| Code | HTTP | Meaning |
|---|---|---|
| `VALIDATION_ERROR` | 400 | Bad or missing input |
| `UNAUTHORIZED` / `FORBIDDEN` | 401 / 403 | Missing or wrong admin token |
| `NOT_FOUND` | 404 | Order does not exist |
| `DUPLICATE_SUSPECTED` | 409 | Looks like an accidental repeat order |
| `IDEMPOTENCY_KEY_REUSED` | 409 | Same key used with different data |
| `INVALID_STATUS_TRANSITION` | 409 | That status change is not allowed |
| `ORDER_NOT_EDITABLE` | 409 | Only Pending orders can be edited |
| `INTERNAL_ERROR` | 500 | Unexpected problem (details stay in server logs) |

---

## Sales reports

Both reports show **gross** and **net** sales:

| Figure | Meaning |
|---|---|
| **Gross sales** | All orders, whatever their status |
| **Net sales** | Excludes `Cancelled` and `Returned` orders |

| Report | Grouped by | Columns |
|---|---|---|
| By product | Product | `order_count`, `net_order_count`, `quantity_sold`, `gross_sales`, `net_sales` (highest net first) |
| By date | `order_date` | same columns, sorted by date |

Date filters are inclusive. `start_date` must not be after `end_date`. Tax, discounts, shipping and refunds are not included.

---

## About the sample data

`data/Online-Store-Orders-Updated.csv` has 1,202 order rows. Some are intentionally messy, so the loader checks each row and sets aside the bad ones.

| Issue | Rows | What the loader does |
|---|---|---|
| Quantity is `two`, `-3` or `0` | ORD0016, ORD0123, ORD0290 | Rejected |
| Negative price | ORD0624 | Rejected |
| Blank date | ORD0457, ORD0741, ORD1200 | Rejected |
| Status `Received` (not a valid status) | ORD0082, ORD0327 | Rejected |
| Copies of earlier orders (new ID, same details) | ORD1195-ORD1199, ORD1201 | Set aside as `DUPLICATE_CONTENT` for review |
| Price is `0.00` | ORD0702 | Loaded, with a warning |

Everything set aside goes to `data/rejected_orders.csv` with the reason. About 1,187 rows load cleanly. The loader prints the exact numbers each run. Loading happens in one transaction, so a failure leaves the database unchanged.

---

## Project layout

```text
order-sales-management/
|-- client/              Vue.js app (components, views, services, router)
|-- server/
|   |-- app/
|   |   |-- routes/        orders.py, reports.py       (HTTP endpoints)
|   |   |-- services/      order_service.py, report_service.py   (business rules)
|   |   |-- repositories/  order_repository.py, report_repository.py   (SQL)
|   |   |-- validators/    order_validator.py
|   |   `-- config.py
|   |-- scripts/           load_orders.py
|   |-- sql/               schema.sql
|   |-- tests/
|   |-- requirements.txt
|   `-- run.py
|-- data/                  sample CSV and rejected_orders.csv
|-- docs/                  api-contracts.md, business-rules.md, database-discovery.md
|-- .env.example
`-- README.md
```

Request flow: **route** receives the request, **validator** checks it, **service** applies rules, **repository** runs the SQL.

---

## Running the tests

Use a separate test database. Never test against real data.

```powershell
cd server
pytest
```

| Area | What is checked |
|---|---|
| Orders | Create, fetch, list, edit rules |
| Validation | Missing fields, bad quantity, bad price, bad date |
| Totals | Correct math, rounding, client-sent totals ignored |
| Duplicates | Retries, key reuse, concurrent requests, genuine repeat orders |
| Status | Every allowed and disallowed change, admin token required |
| Reports | Gross vs net, date boundaries, empty ranges |
| Loader | Rejected rows, quarantined copies, rollback on failure |

---

## Design decisions worth knowing

| Topic | Decision |
|---|---|
| One product per order | Matches the dataset. Multi-product orders would need a new table. |
| No customer or product tables | Customer IDs are checked by format only. Prices come from the order itself, because the data has no price list. |
| Totals are not stored | Always calculated as `quantity x unit_price` using exact decimal math. |
| Safe SQL | All queries are parameterized. Multi-step writes use transactions. |
| Limited database changes | The app only creates the objects in `server/sql/schema.sql`, inside `sales_schema`. |
| Simple admin security | A single token protects admin actions. This is fine for a simulation but is not full user authentication. |

---

## Troubleshooting

| Problem | Likely fix |
|---|---|
| `/api/health` fails | Check the server is running and `.env` values are correct |
| Database connection error | Confirm PostgreSQL is running and `DB_*` settings match |
| `relation "orders" does not exist` | Run `schema.sql` (step 1) |
| Browser CORS error | Make sure `FRONTEND_ORIGIN` matches the frontend address exactly |
| `400` on create with a missing key message | Add the `Idempotency-Key` header |
| `403` on status change | Send `Authorization: Bearer <ADMIN_API_TOKEN>` |
| PowerShell blocks the venv script | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once |

---

## Security notes

- Keep `.env` out of Git. Use `.env.example` for placeholders only.
- If a password was ever shared or committed, change it.
- Error responses never show SQL, credentials or stack traces.