# Order & Sales Management

A web application for managing customer orders, tracking their status, detecting duplicate orders, and generating sales reports. I built it as an internship learning project to understand how a Vue.js frontend, Flask API, and PostgreSQL database work together in a real application.

The goal was to keep the application straightforward while paying attention to the things that matter beyond basic CRUD operations: authentication, authorization, data validation, database integrity, and testing.

**Tech stack:** Vue 3, Flask 3, PostgreSQL, SQLAlchemy, JWT, and pytest.

## What the application does

The application covers three main areas.

- **Authentication:** Users can register, verify their email, log in, and reset their password. Accounts have either a customer or admin role.
- **Order management:** The application validates order details, calculates order totals, tracks status changes, and identifies potential duplicate orders.
- **Sales reports:** Admins can view product-wise and date-wise sales summaries. Only shipped and delivered orders contribute to revenue.

Customers can access their own order information, while admins can manage orders across the application. These permissions are enforced by the backend, not just by hiding buttons in the frontend.

## Getting started

You'll need Python 3.10 or later, Node.js 18 or later, and PostgreSQL 14 or later.

### 1. Set up the backend

Open PowerShell and navigate to the project:

```powershell
cd F:\Intern_Training\Order_Sales_Management\server

python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

If PowerShell blocks virtual environment activation, check your local execution policy before changing it.

### 2. Configure environment variables

Create a `.env` file from the supplied example:

```powershell
Copy-Item .env.example .env
```

Update the database connection and JWT secret in `.env`:

```env
DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/order_sales_db

JWT_SECRET_KEY=your_generated_random_secret
```

Generate a random secret with:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

Use the generated value for `JWT_SECRET_KEY`. Keep `.env` out of version control and never commit real credentials.

### 3. Create the database and tables

The database schema is created before the application starts. Flask connects to the existing database; it should not be responsible for creating the schema or tables at runtime.

From the project root, create the database:

```powershell
cd F:\Intern_Training\Order_Sales_Management

psql -U postgres -c "CREATE DATABASE order_sales_db;"
```

Load the SQL definitions:

```powershell
psql -U postgres -d order_sales_db -f db/init.sql
```

Make sure `db/init.sql` creates the `order_sales` schema and its required tables, and that the application's database user has the necessary permissions.

### 4. Create an admin account

The intended setup uses a management command to create the first admin account. Public registration creates customer accounts, so an ordinary registration request cannot grant itself administrative access.

If the command is implemented in your current Flask CLI configuration, run:

```powershell
cd server
flask --app manage create-admin
```

Follow the prompts to enter the admin's details.

### 5. Start the backend

```powershell
python run.py
```

The API should be available at:

`http://127.0.0.1:5000`

During development, email verification codes and password-reset details can be written to `server/dev_emails.log` instead of being sent through SMTP, provided the development email implementation is configured that way.

### 6. Start the frontend

Open another PowerShell terminal:

```powershell
cd F:\Intern_Training\Order_Sales_Management\client

npm install
npm run dev
```

Vite will display the local frontend URL in the terminal.

## A closer look at the security model

Authentication answers one question: *Who is making this request?*

Authorization answers another: *What is this user allowed to do?*

Keeping those responsibilities separate is important. A valid JWT should not automatically give someone permission to access every order or administrative endpoint.

### Roles and token revocation

The backend uses JWTs to authenticate requests and loads the current user from the database when applying authorization rules.

The token includes a token-version claim (`tv`). The user's current `token_version` is stored in the database. When the versions do not match, the backend rejects the token.

This provides a simple way to invalidate previously issued tokens. For example, after a password reset, the application can increment the user's token version so that existing tokens stop working.

The role stored in the database is the authority for access decisions. A role claim in a JWT can help the frontend decide what to display, but it must not override the server's authorization checks.

### Protecting customer order data

A customer should never be able to access another customer's orders simply by changing an ID in a URL.

The backend therefore checks ownership when returning order details. Admins can access orders across customers, while customers are restricted to their own records.

Registration also needs to associate the user with the correct customer record. If registration requires a `customer_id`, the backend must verify that the customer exists and that the associated email matches the registering user's email. Otherwise, someone could attempt to link their account to another customer's order history.

The database constraints and backend checks work together to protect these relationships.

### Who can access what?

The following table describes the intended access rules.

| Operation | Public | Customer | Admin |
|---|---|---|---|
| Register, verify email, login, reset password | Yes | Yes | Yes |
| View own profile | No | Yes | Yes |
| List orders | No | Own orders | All orders |
| View an individual order | No | Own orders | Any order |
| Create orders | No | No | Yes |
| Change order status | No | No | Yes |
| View duplicate-order records | No | No | Yes |
| Generate sales reports | No | No | Yes |
| Access protected database information | No | No | Yes |

The table describes application behavior, not just frontend navigation. Each restriction must be checked by the backend and covered by tests.

## Testing the application

Testing is especially important for authentication and permissions because a small mistake can expose data or grant access to the wrong user.

The current test plan contains 78 tests, divided into three main areas:

- **25 permission tests:** Role restrictions, customer ownership, isolation between customers, and token revocation.
- **27 authentication tests:** Registration, verification, login, password reset, invalid codes, expired codes, and duplicate registrations.
- **24 order tests:** Order creation, input validation, foreign-key checks, status transitions, pagination, and duplicate detection.
- **2 smoke tests:** Basic application startup and test-database checks.

Run the tests from the backend directory:

```powershell
cd F:\Intern_Training\Order_Sales_Management\server

pytest tests/ -v
```

The expected result, if the current suite matches this breakdown, is:

```text
78 passed
```

Execution time depends on the machine and test environment.

### Keeping tests away from real data

Tests should never use the development database by accident.

The intended configuration uses `.env.test` when `FLASK_ENV=test` is set, with `conftest.py` setting the environment before the application is imported. The test configuration points to a separate database, `order_sales_test_db`.

Before running the suite, create that test database and load the required schema and reference data into it. Confirm the effective database URL before executing destructive test fixtures.

Between tests, fixtures can truncate application data and remove the SQLAlchemy session to prevent state from leaking between test cases. Reference data, such as products, can be seeded once per test session if the tests rely on it.

Authentication tests can replace email-sending functions with test doubles that capture verification codes and reset tokens. That avoids SMTP dependencies and makes the tests easier to repeat.

## How the backend is organized

The backend separates HTTP handling from business logic and database models. This keeps individual parts easier to understand, test, and change.

Order_Sales_Management/
│
├── client/                              # Vue 3 frontend (Vite)
│   ├── src/
│   │   ├── router/
│   │   │   └── index.js                 # Frontend route definitions (login, register, orders, reports)
│   │   ├── services/
│   │   │   └── api.js                   # Axios/fetch wrapper — attaches the JWT to every request
│   │   ├── stores/                      # Pinia stores for shared state (auth token, current user)
│   │   ├── views/
│   │   │   ├── Login.vue                # Login screen
│   │   │   ├── Register.vue             # Registration + email verification screen
│   │   │   ├── Orders.vue               # Order list / details (role-aware UI)
│   │   │   └── Reports.vue              # Admin-only sales reports dashboard
│   │   ├── App.vue                      # Root component — layout, nav, mount point
│   │   └── main.js                      # Vue app bootstrap
│   ├── index.html                       # Vite HTML entry
│   ├── package.json                     # Node dependencies and scripts
│   └── vite.config.js                   # Vite config (dev server, proxy to Flask API)
│
├── data/                                # Raw input data (not used at runtime)
│   └── Online_Store_Orders.csv          # Source dataset used to seed the database
│
├── db/                                  # Database setup — version-controlled schema
│   ├── DB.md                            # Notes on schema decisions and table relationships
│   └── init.sql                         # Full DDL: schema, tables, indexes, constraints
│
├── server/                              # Flask backend
│   ├── app/                             # Application package
│   │   ├── routes/                      # HTTP layer — thin controllers, no business logic
│   │   │   ├── auth.py                  # /api/auth/* endpoints (register, verify, login, reset, me)
│   │   │   ├── orders.py                # /api/orders/* endpoints (CRUD, validate, status, duplicates)
│   │   │   └── reports.py               # /api/reports/* endpoints (product-wise, date-wise)
│   │   │
│   │   ├── services/                    # Business logic — no HTTP, no Flask imports
│   │   │   ├── auth_service.py          # Registration, verification, login, password reset rules
│   │   │   └── order_service.py         # Validation, transitions, totals, duplicates, report queries
│   │   │
│   │   ├── utils/                       # Cross-cutting helpers used everywhere
│   │   │   ├── decorators.py            # @auth_required and @role_required — enforce JWT + role
│   │   │   ├── permissions.py           # Role hierarchy and ownership predicates (can_view_order, etc.)
│   │   │   ├── validators.py            # Email / password format checks (single source of truth)
│   │   │   └── email.py                 # Email dispatch — writes to dev_emails.log in dev
│   │   │
│   │   ├── __init__.py                  # App factory — create_app(), blueprint registration
│   │   ├── config.py                    # Env-driven config — loads .env or .env.test based on FLASK_ENV
│   │   ├── constants.py                 # Role enum — the single source of truth for role strings
│   │   ├── extensions.py                # Shared singletons (db, jwt, mail) + password hashing helpers
│   │   └── models.py                    # SQLAlchemy models — pure data, no business logic
│   │
│   ├── tests/                           # pytest suite (78 tests)
│   │   ├── __init__.py                  # Marks the folder as a Python package
│   │   ├── conftest.py                  # Shared fixtures: app, db, client, admin/customer tokens
│   │   ├── test_permissions.py          # RBAC matrix, ownership, revocation (25 tests)
│   │   ├── test_auth.py                 # Register / verify / login / reset lifecycle (27 tests)
│   │   ├── test_orders.py               # Order creation, validation, transitions, duplicates (24 tests)
│   │   └── test_smoke.py                # Sanity checks — app boots, DB is the test DB (2 tests)
│   │
│   ├── logs/
│   │   └── app.log                      # Rotating application log (gitignored)
│   │
│   ├── .env                             # Local secrets (gitignored)
│   ├── .env.example                     # Template — safe to commit, no real secrets
│   ├── .env.test                        # Test DB config (gitignored)
│   ├── .gitignore                       # Excludes .env, .env.test, logs/, __pycache__, .pytest_cache
│   ├── manage.py                        # Flask CLI — `flask --app manage create-admin`
│   ├── pytest.ini                       # pytest config — test paths, verbose output
│   ├── requirements.txt                 # Python dependencies
│   ├── run.py                           # Dev entry point — `python run.py`
│   └── dev_emails.log                   # Captured OTPs and reset links during development (gitignored)
│
└── README.md                            # This file

The exact layout should match the files present in the repository.

### Why separate routes and services?

Routes handle incoming HTTP requests, read request data, invoke the appropriate service, and return HTTP responses.

Services contain the application rules: validating an order, calculating totals, checking duplicates, or deciding whether a status change is legal.

Models describe the database entities and their relationships.

This separation avoids putting the same business rules into multiple routes. It also makes service-level testing easier because business logic can be tested independently of HTTP request handling.

Authorization decorators provide a consistent way to protect endpoints. For example, an authentication decorator checks that a request has a valid identity, while an admin-role decorator checks whether the current user has administrative privileges.

## Database design

The application uses PostgreSQL, with its application tables grouped under the `order_sales` schema. The full table definitions and constraints belong in `db/init.sql`.

The main tables serve different purposes:

- **`users`** stores login details, password hashes, roles, verification state, password-reset information, and token-version data.
- **`customers`** stores customer information and can link a customer record to a user account.
- **`products`** stores product names and current prices.
- **`orders`** stores the customer associated with an order, its date, and its current status.
- **`order_items`** stores the products, quantities, and unit prices associated with each order.

Separating orders from order items allows a single order to contain multiple products without repeating the order's customer, date, and status for every line.

The order-item table should also enforce a unique constraint on `(order_id, product_id)` if the business rule is that each product appears only once per order. Quantities and prices should use appropriate numeric types, with database constraints to reject invalid values where applicable.

Passwords must be stored as secure hashes, never as plain text. Email uniqueness, foreign keys, allowed roles, and other important data rules should be enforced at the database or application layer as appropriate.

The application reads and writes data through its database connection. Schema creation and structural changes remain a separate setup or database-maintenance task.

## Order status workflow

Orders move through a defined workflow rather than accepting arbitrary status changes.

The intended transitions are:

```text
Pending
  ├── Received
  ├── Shipped
  └── Cancelled

Received
  └── Shipped

Shipped
  └── Delivered

Delivered
  └── Returned
```

`Cancelled` and `Returned` are terminal states in this workflow. Once an order reaches either state, further transitions are rejected.

For example, attempting to move an order directly from `Pending` to `Delivered` should return a validation error rather than silently updating the record.

These rules belong in the order service, where they can be tested consistently regardless of which API endpoint requests the change.

## Sales reports

The reporting endpoints provide product-wise and date-wise summaries.

For this application, only orders with a status of `Shipped` or `Delivered` count toward revenue. Pending and cancelled orders are excluded, as are other statuses that do not qualify under the reporting rule.

Revenue should be calculated using the order item's recorded unit price and quantity, rather than the product's current price. This preserves the amount associated with the original transaction if a product's price changes later.

The report queries should apply the same status filter consistently so that product totals and date totals agree.

## Scope and trade-offs

This project focuses on core order-processing behavior, basic account security, database integrity, and backend testing. It is not intended to be a complete production deployment.

Some improvements would be necessary before exposing it to real customers:

- **Rate limiting:** Login, registration, verification, and password-reset endpoints should have appropriate request limits.
- **HTTPS:** Production traffic must use HTTPS, with secure deployment and secret management.
- **Email delivery:** The development email mechanism needs to be replaced or disabled in favor of a properly configured email provider.
- **Refresh-token strategy:** The current access-token lifecycle should be reviewed if longer-lived sessions are required.
- **Account-enumeration protection:** Authentication responses should be designed carefully to avoid revealing whether an email address is registered.
- **Database migrations:** A migration tool such as Alembic would make schema changes safer and easier to track.
- **Automated deployment:** A CI pipeline could run tests on every change and catch regressions before deployment.

These are reasonable next steps rather than reasons to complicate the initial implementation. The priority is to make the required behavior correct and testable first.

## A couple of Windows development notes

When generating files through PowerShell, be careful with text encoding. Some commands can write a UTF-8 byte-order mark (BOM), which may cause problems for configuration files or SQL scripts.

For predictable UTF-8 output without a BOM, use:

```powershell
$content = @'
Your file content goes here.
'@

[System.IO.File]::WriteAllText(
    "README.md",
    $content,
    [System.Text.UTF8Encoding]::new($false)
)
```

Also, `Select-String` does not accept a `-Recurse` parameter directly. Pipe files from `Get-ChildItem` instead:

```powershell
Get-ChildItem -Recurse -File |
    Select-String -Pattern "search term"
```

## License and project context

This is an internal training project associated with Triniti Advanced Software Labs Pvt. Ltd.

Built by Vijayakumar Chinta during internship training, October 2026.