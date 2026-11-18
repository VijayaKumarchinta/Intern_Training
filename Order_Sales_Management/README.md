# Order & Sales Management (OrderSync)

A full-stack retail/e-commerce simulation built with **Vue 3 + Vite** on the frontend and **Flask + SQLAlchemy + PostgreSQL** on the backend. It covers customer orders, validated order details, calculated order totals, a strict order-status state machine, duplicate-order detection, product-wise and date-wise sales reports, and a complete auth flow (register → OTP verify → login → password reset) with role-based access.

Built during an internship training period as one of three production-shaped projects, alongside the **Machine Sensor API** and the **PlantView / Line 30 Live Dashboard**.

## What it does

- **Authentication** — register with email + OTP verification (2-minute TTL), login with JWT, forgot/reset password with token-version revocation.
- **Roles** — admin and customer, enforced on the backend per request; the role in the JWT is not the authority, the database is.
- **Orders** — create (admin only), list, view, update status via a strict state machine, detect duplicates.
- **Tenancy** — customers see only their own orders; cross-tenant reads return 404, not 403, to avoid leaking order IDs.
- **Pricing** — the server uses `products.current_price` for every line item; client-supplied `unit_price` is ignored.
- **Reports** — admin-only dashboard summary, product-wise and date-wise sales (JSON or CSV). Only `Shipped` + `Delivered` count toward revenue, using historic `order_items.unit_price`.

## Tech stack

- **Frontend:** Vue 3 (Vite), Pinia, Vue Router, Axios
- **Backend:** Flask 3, SQLAlchemy, Flask-JWT-Extended, Flask-Mail (dev simulation), bcrypt
- **Database:** PostgreSQL 14+ with the `order_sales` schema
- **Testing:** pytest (routes, permissions, auth lifecycle, pricing, reports, smoke)

## Repository layout

```
Order_Sales_Management/
├── client/                          # Vue 3 + Vite frontend
│   ├── src/
│   │   ├── router/index.js         # Frontend routes
│   │   ├── services/api.js         # Axios wrapper — attaches JWT
│   │   ├── stores/                 # Pinia stores (auth, summary)
│   │   ├── views/                  # Landing, Login, Register, ForgotPassword, ResetPassword,
│   │   │                           #   MyOrders, Orders, CreateOrder, OrderDetail,
│   │   │                           #   Products, Customers, Users, Reports, Duplicates, Totals
│   │   ├── App.vue                 # Root component
│   │   └── main.js                 # Bootstrap
│   ├── index.html
│   ├── package.json
│   └── vite.config.js              # Dev server + /api proxy to Flask
├── data/
│   └── Online_Store_Orders.csv     # Source dataset for seeding
├── db/
│   ├── init.sql                    # DDL: schema, tables, indexes, constraints
│   ├── DB.md                       # Schema decisions and table relationships
│   ├── load_data.py                # CSV import pipeline (dry-run supported)
│   └── order_sales_backup.sql
├── server/                          # Flask backend
│   ├── app/
│   │   ├── __init__.py             # App factory — create_app(), extensions, blueprints
│   │   ├── config.py               # Env-driven config (.env / .env.test)
│   │   ├── constants.py            # Role enum — single source of truth for role strings
│   │   ├── extensions.py           # db, jwt, mail + password helpers
│   │   ├── models.py               # User, Customer, Product, Order, OrderItem
│   │   ├── routes/                 # Thin HTTP controllers
│   │   │   ├── auth.py
│   │   │   ├── orders.py
│   │   │   ├── reports.py
│   │   │   ├── products.py
│   │   │   ├── customers.py
│   │   │   └── users.py
│   │   ├── services/               # Business logic — no HTTP, no Flask imports
│   │   │   ├── auth_service.py
│   │   │   └── order_service.py
│   │   └── utils/                  # Decorators, permissions, validators, dev email
│   │       ├── decorators.py
│   │       ├── permissions.py
│   │       ├── validators.py
│   │       └── email.py
│   ├── tests/                      # pytest suite
│   │   ├── conftest.py
│   │   ├── test_auth.py
│   │   ├── test_orders.py
│   │   ├── test_permissions.py
│   │   ├── test_pricing.py
│   │   ├── test_reports.py
│   │   └── test_smoke.py
│   ├── logs/
│   │   └── app.log                 # Rotating application log (gitignored)
│   ├── .env                        # Local secrets (gitignored)
│   ├── .env.example                # Template — safe to commit
│   ├── .env.test                   # Test DB config (gitignored)
│   ├── .gitignore
│   ├── manage.py                   # Flask CLI — create-admin
│   ├── pytest.ini
│   ├── requirements.txt
│   ├── run.py                      # Dev entry point
│   └── dev_emails.log              # Captured OTPs/reset links in dev (gitignored)
└── README.md
```

## API endpoints

### Auth

| Method | Path | Description |
|---|---|---|
| POST | `/api/auth/register` | Register (email, password, full_name, customer_id) → OTP logged to dev_emails.log |
| POST | `/api/auth/verify` | Verify email with OTP; optionally link customer_id |
| POST | `/api/auth/resend-verification` | Resend verification code |
| POST | `/api/auth/login` | Login → JWT access token |
| GET | `/api/auth/me` | Authenticated user profile + linked customer |
| POST | `/api/auth/forgot-password` | Initiate password reset (generic 200) |
| POST | `/api/auth/reset-password` | Reset password with token (invalidates old JWTs) |

### Orders

| Method | Path | Description |
|---|---|---|
| GET | `/api/orders` | List visible orders; admin sees all, customer sees own; supports status filter, customer_id, search, pagination |
| GET | `/api/orders/<id>` | Order detail with line items; 404 for cross-tenant access |
| POST | `/api/orders` | Create an order (admin only); validates order_id format, customer, products, quantities, status |
| PATCH | `/api/orders/<id>/status` | Update status through the strict state machine (admin only) |
| GET | `/api/orders/duplicates` | Duplicate order groups (admin only) |

### Products

| Method | Path | Description |
|---|---|---|
| GET | `/api/products` | List products |
| POST | `/api/products` | Create a product (admin only) |
| PATCH | `/api/products/<id>` | Update a product's price (admin only) |
| DELETE | `/api/products/<id>` | Delete a product if unused (admin only) |

### Customers

| Method | Path | Description |
|---|---|---|
| GET | `/api/customers` | List customers (admin only) |
| POST | `/api/customers` | Create a customer (admin only) |

### Users

| Method | Path | Description |
|---|---|---|
| GET | `/api/users` | List users (admin only) |
| POST | `/api/users` | Create a user (admin only) |
| PATCH | `/api/users/<id>/role` | Update a user's role (admin only) |
| DELETE | `/api/users/<id>` | Delete a user (admin only; blocks self-delete and last-admin) |

### Reports

| Method | Path | Description |
|---|---|---|
| GET | `/api/reports/summary` | Dashboard KPIs, latest orders, duplicate groups, breakdowns (admin only) |
| GET | `/api/reports/product-wise` | Product-wise sales; `?format=csv` for download (admin only) |
| GET | `/api/reports/date-wise` | Daily/monthly sales; `?group=day|month&format=csv` (admin only) |

## Order status state machine

```
Pending
  ├── Received
  ├── Shipped
  └── Cancelled

Received
  └── Shipped
        └── Delivered
              └── Returned

Cancelled / Returned — terminal
```

Invalid transitions are rejected with a 400. The rules live in `order_service.ALLOWED_TRANSITIONS` and are mirrored in the frontend.

## Database schema

All application tables live under the `order_sales` schema:

- **`users`** — id, email (case-insensitive unique), password_hash, full_name, role, is_verified, verification/reset token state, token_version, created_at/updated_at
- **`customers`** — customer_id (PK), user_id (FK → users, unique, ON DELETE SET NULL), cust_name, email, created_at
- **`products`** — product_id, pro_name (unique), current_price
- **`orders`** — order_id (PK), customer_id (FK → customers), order_date, order_status, created_at/updated_at
- **`order_items`** — order_item_id, order_id (FK → orders, ON DELETE CASCADE), product_id (FK → products), quantity, unit_price, unique (order_id, product_id)
- **`staging_orders`** — raw CSV import table (no business constraints; validated before insert into normalized tables)

Indexes cover `users.email` (lowercased), `orders(customer_id, order_date)`, `orders.order_status`, and `order_items.product_id`.

## Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+

### Backend

```bash
cd Order_Sales_Management/server

python -m venv .venv
. .venv/bin/activate   # or .venv\Scripts\Activate.ps1 on Windows

pip install -r requirements.txt
```

Copy `.env.example` to `.env` and configure:

```
DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/order_sales_db
JWT_SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
```

Create the database and load the schema:

```bash
psql -U postgres -c "CREATE DATABASE order_sales_db;"
psql -U postgres -d order_sales_db -f ../db/init.sql
```

Create the first admin:

```bash
flask --app manage create-admin
```

Start the backend:

```bash
python run.py
```

The API is available at `http://127.0.0.1:5000`.

In development, OTP codes and password-reset links are written to `server/logs/dev_emails.log` instead of being sent via SMTP.

### Frontend

```bash
cd Order_Sales_Management/client

npm install
npm run dev
```

Vite proxies `/api` to the Flask backend and serves the app on `http://localhost:5173`.

## Seeding the dataset

The raw CSV lives at `data/Online_Store_Orders.csv`. The intended load path is staged so bad rows can be reviewed before they reach the normalized tables:

1. Load `db/init.sql` to create the schema and `staging_orders`.
2. `COPY` the CSV into `order_sales.staging_orders`.
3. Run the staging validation queries in `db/DB.md`.
4. Insert distinct customers and products.
5. Insert orders and order items with validation.
6. Reconcile any rows that were not imported.

`db/load_data.py` provides a Python pipeline with a `--dry-run` mode for the same flow.

## Testing

```bash
cd Order_Sales_Management/server

# Create and load the test database first (order_sales_test_db, per .env.test)
python -m pytest tests/ -v
```

The suite covers auth lifecycle, permissions/ownership, order creation + status machine + duplicates, server-side pricing, report accuracy, and smoke checks. Tests use a separate test database and truncate application tables between cases; products are seeded once per session.

## Security model

- **Auth vs authorization:** a valid JWT proves identity; the database decides permissions. Roles are reloaded from the DB per request.
- **Token revocation:** JWTs carry a `token_version` claim; after a password reset the user's `token_version` is incremented, so formerly issued tokens stop working.
- **Role integrity:** the role claim in a JWT helps the frontend decide what to render, but it cannot override the server's checks.
- **Customer isolation:** cross-tenant order access returns 404, not 403, to avoid leaking order IDs.
- **Registration linkage:** registering with a `customer_id` verifies the customer exists, is unlinked, and its email matches the registering email.

## Scope and trade-offs

This is an internship training project, not a production deployment. Reasonable next steps before real exposure include rate limiting on auth endpoints, HTTPS, a real email provider, a refresh-token strategy, account-enumeration protection, Alembic migrations, and a CI pipeline. The priority here is correct, testable behavior first.

## Documentation

Deeper explanations of the backend files, frontend files, API endpoints, and full flow are in the `docpack/` folder:

- `docpack/backend_files_explained.md`
- `docpack/frontend_files_explained.md`
- `docpack/api_endpoints_documentation.md`
- `docpack/Flow.md`
- `docpack/frontend_backend_communication.md`

Schema detail is in `db/DB.md`.

## Project context

Part of an internship training portfolio (Triniti Advanced Software Labs Pvt. Ltd., Aug–Nov 2026), alongside the **Machine Sensor API** and the **PlantView / Line 30 Live Dashboard**. The same habits — layered backend, secrets in `.env`, validate at the boundary, roles as the source of truth, tests covering permissions and pricing — are applied across all three.
