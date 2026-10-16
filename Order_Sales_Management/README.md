# Order and Sales Management Application

A web application that simulates order processing and sales operations for a retail or e-commerce business. It uses a normalized PostgreSQL model for customers, products, orders and order items, and adds user registration, email verification, password reset, role-based access (Admin / Customer) and per-customer order ownership.

## 1. Project Objectives

The application supports:

-   Managing customers, products and customer orders.
-   Validating order details before saving them.
-   Supporting multiple products in a single order.
-   Calculating order totals from order-item quantities and prices.
-   Tracking order statuses.
-   Detecting duplicate order identifiers and repeated submissions.
-   Generating product-wise and date-wise sales reports.
-   Importing the supplied CSV dataset into relational tables.
-   Registering and authenticating users, with email verification and password reset.
-   Restricting access by role: customers see only their own orders; admins manage all orders.

## 2. Technology Stack

| Layer | Technology | Responsibility |
|---|---|---|
| Frontend | Vue 3 (Vite, Pinia, Vue Router, Axios) | Auth screens, order lists, status updates, reports |
| Backend | Python, Flask, Flask-SQLAlchemy | API endpoints, validation, business rules, transactions |
| Auth | Flask-JWT-Extended, bcrypt | Login tokens, password hashing, role checks |
| Database | PostgreSQL (schema `order_sales`) | Relational data, constraints, SQL reports |
| API testing | Postman / PowerShell `Invoke-RestMethod` | Requests, responses, error cases |
| Dataset | `Online-Store-Orders-Updated.csv` | Initial order data for import |

## 3. Architecture

```text
Vue 3 Frontend
  Registration, login, orders, status tracking, reports
      |
      | HTTP requests / JSON responses (Authorization: Bearer <JWT>)
      v
Flask REST API
  Authentication, authorization, validation, business logic, duplicate detection
      |
      | SQLAlchemy / parameterized SQL / transactions
      v
PostgreSQL: order_sales
      +-- users
      +-- customers
      +-- products
      +-- orders
      +-- order_items
```

The browser never talks to PostgreSQL. Flask validates every request, checks the caller's identity and role, and runs the database operations. PostgreSQL enforces integrity through primary keys, foreign keys, unique constraints and check constraints.

The application connects to an existing schema. It must not create or drop the schema at startup. Run the setup SQL separately in a controlled environment.

## 4. Database Design

The schema is named `order_sales`.

| Table | Purpose |
|---|---|
| `users` | Login credentials, email verification, password reset, role |
| `customers` | Customer profiles and customer IDs imported from the CSV |
| `products` | Product master data |
| `orders` | Order header: customer, date, status |
| `order_items` | Products, quantities and historical unit prices per order |

### 4.1 Relationships

```text
users     1 -------- 0..1 customers
customers 1 -------- many orders
orders    1 -------- many order_items
products  1 -------- many order_items
```

-   One user can be linked to at most one customer profile.
-   One customer can place multiple orders.
-   One order can contain multiple products.
-   One product can appear in many order items.
-   Each user has one role: `admin` or `customer`.

The CSV supplies order and product data, not login credentials. Do not create accounts automatically for imported customers. Imported customers stay unlinked until their owner registers and an admin links the account (see section 7.5).

### 4.2 Design decisions

-   `users.email` is unique regardless of letter case.
-   Passwords, verification tokens and reset tokens are stored only as hashes. Tokens also carry an expiry.
-   `customers.user_id` links an account to an imported customer profile.
-   `order_items.unit_price` keeps the price charged at purchase time. `products.current_price` is optional catalogue data and is not used to rewrite history.
-   `UNIQUE (order_id, product_id)` assumes a product appears once per order. Remove it if repeated lines are valid and aggregate them in reports.
-   The order total is `SUM(quantity * unit_price)`, calculated on read. It is never stored.

## 5. CSV Dataset Mapping

Source columns: `OrderID`, `Date`, `CustomerID`, `Product`, `Quantity`, `UnitPrice`, `OrderStatus`

| CSV column | Destination | Transformation |
|---|---|---|
| `OrderID` | `orders.order_id` | Trim and validate identifier |
| `Date` | `orders.order_date` | Strict parse into `DATE` |
| `CustomerID` | `customers.customer_id`, then `orders.customer_id` | Create or match customer |
| `Product` | `products.name`, then `order_items.product_id` | Match product by name |
| `Quantity` | `order_items.quantity` | Positive integer only |
| `UnitPrice` | `order_items.unit_price` | Decimal, non-negative |
| `OrderStatus` | `orders.order_status` | Normalize and validate against allowed statuses |

### Import strategy

1.  Load the CSV into `staging_orders` as text. Keep the original rows.
2.  Validate required fields, strict dates, numeric formats and statuses.
3.  Identify repeated order IDs, conflicting headers and repeated products within an order.
4.  Insert distinct customers and products. Leave customer name and email `NULL` unless a trusted source exists.
5.  Insert one order header per unique order ID, then one order item per valid line.
6.  Run the load in a transaction and produce a reconciliation report: accepted rows, rejected rows, reasons.
7.  Do not hide failures with `ON CONFLICT DO NOTHING`. Report each conflict.

A repeated order ID across rows means multiple items of the same order, not a duplicate header. Do not invent values for missing or malformed fields. A status such as `Received` must be mapped explicitly or flagged, never silently treated as `Delivered`. The regex date check misses impossible dates such as 31 February, so parse dates strictly in Python.

## 6. Validation Rules

Apply validation in the backend and in the database.

-   `order_id` and `customer_id` must be present.
-   The referenced customer and product must exist.
-   `quantity` must be a positive integer.
-   `unit_price` must be non-negative.
-   `order_date` must parse strictly and must not be missing for a confirmed order.
-   `order_status` must be one of: `Pending`, `Received`, `Shipped`, `Delivered`, `Cancelled`, `Returned`.
-   A repeated `order_id` must not create a second order header.
-   An order and its items are saved atomically.
-   Use parameterized SQL (or the ORM). Never concatenate user input into SQL.
-   New-order prices come from server-side pricing, not from the browser.
-   Passwords: minimum 8 characters.

## 7. Authentication and Authorization

These rules are enforced in the Flask API and PostgreSQL. Hiding buttons in Vue is not authorization.

### 7.1 Registration

Vue sends email, password and optional full name. Flask normalizes the email (trim, lowercase), validates the password, hashes it with bcrypt and inserts a user with `role = 'customer'` and `is_verified = FALSE`.

-   Public registration always assigns `customer`. A role field in the request is ignored.
-   Admin accounts are created or promoted through a controlled process, for example:
    `UPDATE order_sales.users SET role = 'admin' WHERE email = '...';`
-   Registration does not link the account to a customer profile. See 7.5.

### 7.2 Email verification

1.  Flask generates a random token with `secrets.token_urlsafe(32)`, stores its SHA-256 hash with an expiry (24 hours), and sends the raw token in a link: `FRONTEND_URL/verify-email?token=...`.
2.  Development: the link is printed to the server console (no SMTP). Production: send through an email provider.
3.  `POST /api/auth/verify-email` hashes the submitted token and runs:

```sql
UPDATE order_sales.users
SET is_verified = TRUE,
    verification_token_hash = NULL,
    verification_expires_at = NULL,
    updated_at = NOW()
WHERE verification_token_hash = %s
  AND is_verified = FALSE
  AND verification_expires_at > NOW()
RETURNING id, email, is_verified;
```

No row returned means the token is invalid, expired or already used.

### 7.3 Login

Flask loads the user by lowercased email and checks the password with bcrypt. Invalid credentials return a generic `401`. Unverified accounts are rejected with `403`. On success Flask returns a JWT access token (default lifetime 12 hours). Vue sends it as `Authorization: Bearer <token>`.

-   The token carries only the user ID. Flask loads the current role from the database on each request, so a role change takes effect immediately.
-   Tokens kept in browser storage are exposed to XSS. Keep the frontend free of unsanitized HTML. For production consider HttpOnly cookies with CSRF protection.

### 7.4 Password reset

1.  `POST /api/auth/forgot-password` always returns the same generic response, whether or not the email exists.
2.  If the user exists, Flask stores the hash of a random single-use token with a 1-hour expiry and prints or sends the link `FRONTEND_URL/reset-password?token=...`.
3.  `POST /api/auth/reset-password` validates the new password and runs:

```sql
UPDATE order_sales.users
SET password_hash = %s,
    reset_token_hash = NULL,
    reset_token_expires_at = NULL,
    updated_at = NOW()
WHERE reset_token_hash = %s
  AND reset_token_expires_at > NOW()
RETURNING id;
```

### 7.5 Linking a user to a customer profile

Do not link an account to a customer based on a matching email or a customer ID typed by the user. Anyone could claim someone else's orders that way.

-   An admin links an account to a customer: `PATCH /api/customers/{customer_id}/link` with `{ "user_id": ... }`.
-   Each user links to at most one customer (`customers.user_id` is unique).
-   An unlinked customer account sees no orders until linked.
-   For a brand-new customer, generate a customer ID that cannot collide with imported IDs.

### 7.6 Roles and ownership

| Action | Customer | Admin |
|---|---|---|
| Register, log in, reset own password | Yes | Yes |
| List orders | Own orders only | All orders |
| View an order | Own only (others return `404`) | Any |
| Create an order | For own customer profile | For any customer |
| Change order status | No | Yes |
| List customers, link users | No | Yes |
| Sales reports | No | Yes |
| Duplicate investigation | No | Yes |

Customer's own orders (the user ID comes from the verified token, never from the request):

```sql
SELECT o.order_id, o.order_date, o.order_status
FROM order_sales.orders AS o
JOIN order_sales.customers AS c ON c.customer_id = o.customer_id
WHERE c.user_id = %s
ORDER BY o.order_date DESC NULLS LAST;
```

Admin order list:

```sql
SELECT o.order_id, o.order_date, o.order_status,
       c.customer_id, c.name AS customer_name, c.email AS customer_email
FROM order_sales.orders AS o
JOIN order_sales.customers AS c ON c.customer_id = o.customer_id
ORDER BY o.order_date DESC NULLS LAST;
```

Return `404`, not `403`, when a customer requests another customer's order so order IDs do not leak. Apply the ownership check to order details, status changes and cancellations.

## 8. Core Business Logic

### Create an order

1.  Receive customer, order items and an optional idempotency key.
2.  Validate required fields and item values.
3.  Confirm that the customer and products exist.
4.  Begin a transaction.
5.  Insert the order header, then all items using server-side prices.
6.  Commit and return the order ID and calculated total.

If any insert fails, roll back so no partial order is saved.

### Calculate an order total

Never trust a total sent by the browser.

```sql
SELECT o.order_id,
       COALESCE(SUM(oi.quantity * oi.unit_price), 0)::NUMERIC(14,2) AS order_total
FROM order_sales.orders AS o
LEFT JOIN order_sales.order_items AS oi ON oi.order_id = o.order_id
WHERE o.order_id = %s
GROUP BY o.order_id;
```

### Track order status

Validate the transition, then update. Suggested workflow (adjust to the business rules):

| From | Allowed next status |
|---|---|
| Pending | Received, Cancelled |
| Received | Shipped, Cancelled |
| Shipped | Delivered, Returned |
| Delivered | Returned |
| Cancelled, Returned | none |

```sql
UPDATE order_sales.orders
SET order_status = %s, updated_at = NOW()
WHERE order_id = %s
RETURNING order_id, order_status, updated_at;
```

If `order_status_history` is enabled, insert the old and new status in the same transaction.

### Detect duplicates

| Type | Handling |
|---|---|
| Duplicate order identifier | Primary key on `orders.order_id` |
| Repeated API submission | Idempotency key scoped to the user, with a hash of the payload. Return the original result for the same key and payload; reject the same key with a different payload |
| Potential business duplicate | Flag for admin review; do not delete automatically |

```sql
SELECT TRIM(order_id) AS order_id, COUNT(*) AS occurrences
FROM order_sales.staging_orders
GROUP BY TRIM(order_id) HAVING COUNT(*) > 1;

SELECT customer_id, order_date, product, quantity, unit_price, COUNT(*) AS occurrence_count
FROM order_sales.staging_orders
GROUP BY customer_id, order_date, product, quantity, unit_price
HAVING COUNT(*) > 1;
```

Matching rows do not prove a duplicate. A customer may legitimately buy the same product twice.

## 9. SQL Reporting Queries

Define what counts as a sale first. These examples count `Shipped` and `Delivered` orders.

### 9.1 Product-wise sales

```sql
SELECT p.product_id, p.name AS product_name,
       SUM(oi.quantity) AS units_sold,
       SUM(oi.quantity * oi.unit_price)::NUMERIC(14,2) AS total_sales
FROM order_sales.order_items AS oi
JOIN order_sales.products AS p ON p.product_id = oi.product_id
JOIN order_sales.orders   AS o ON o.order_id   = oi.order_id
WHERE o.order_status IN ('Shipped', 'Delivered')
GROUP BY p.product_id, p.name
ORDER BY total_sales DESC;
```

### 9.2 Date-wise sales

```sql
SELECT o.order_date,
       SUM(oi.quantity) AS units_sold,
       SUM(oi.quantity * oi.unit_price)::NUMERIC(14,2) AS daily_sales
FROM order_sales.orders AS o
JOIN order_sales.order_items AS oi ON oi.order_id = o.order_id
WHERE o.order_status IN ('Shipped', 'Delivered')
  AND o.order_date BETWEEN %s AND %s
GROUP BY o.order_date
ORDER BY o.order_date;
```

### 9.3 Monthly sales

```sql
SELECT DATE_TRUNC('month', o.order_date)::DATE AS sales_month,
       SUM(oi.quantity * oi.unit_price)::NUMERIC(14,2) AS monthly_sales
FROM order_sales.orders AS o
JOIN order_sales.order_items AS oi ON oi.order_id = o.order_id
WHERE o.order_status IN ('Shipped', 'Delivered')
GROUP BY DATE_TRUNC('month', o.order_date)
ORDER BY sales_month;
```

### 9.4 Other useful queries

```sql
-- Order totals
SELECT o.order_id, o.order_date, o.customer_id, o.order_status,
       COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS order_total
FROM order_sales.orders AS o
LEFT JOIN order_sales.order_items AS oi ON oi.order_id = o.order_id
GROUP BY o.order_id, o.order_date, o.customer_id, o.order_status
ORDER BY o.order_date DESC NULLS LAST;

-- Products never ordered
SELECT p.product_id, p.name
FROM order_sales.products AS p
LEFT JOIN order_sales.order_items AS oi ON oi.product_id = p.product_id
WHERE oi.product_id IS NULL
ORDER BY p.name;

-- Orders by status
SELECT order_status, COUNT(*) AS order_count
FROM order_sales.orders
GROUP BY order_status ORDER BY order_count DESC;
```

Reports expose business-wide data, so restrict them to admins.

## 10. REST API Endpoints

| Method | Endpoint | Purpose | Access |
|---|---|---|---|
| `POST` | `/api/auth/register` | Register a customer account | Public |
| `POST` | `/api/auth/verify-email` | Verify an email token | Public |
| `POST` | `/api/auth/login` | Authenticate, return JWT | Public |
| `POST` | `/api/auth/forgot-password` | Request a reset link | Public |
| `POST` | `/api/auth/reset-password` | Set a new password | Public (token) |
| `GET` | `/api/auth/me` | Current user and role | Authenticated |
| `GET` | `/api/customers` | List customers | Admin |
| `PATCH` | `/api/customers/{customer_id}/link` | Link a user to a customer | Admin |
| `GET` | `/api/products` | List products | Authenticated |
| `GET` | `/api/orders` | Customer: own orders. Admin: all (filters: `status`, `page`, `per_page`) | Authenticated |
| `POST` | `/api/orders` | Create an order with items | Authenticated |
| `GET` | `/api/orders/{order_id}` | Order details and total | Owner or admin |
| `PATCH` | `/api/orders/{order_id}/status` | Update status | Admin |
| `GET` | `/api/orders/duplicates` | Duplicate investigation | Admin |
| `POST` | `/api/import/orders` | Import and validate a CSV | Admin |
| `GET` | `/api/reports/product-sales` | Product-wise sales | Admin |
| `GET` | `/api/reports/daily-sales` | Date-wise sales | Admin |
| `GET` | `/api/reports/monthly-sales` | Monthly sales | Admin |

Status codes:

| Code | Use |
|---|---|
| `200` | Successful retrieval or update |
| `201` | Resource created |
| `400` | Malformed input, with field-level errors |
| `401` | Missing, invalid or expired token; bad credentials |
| `403` | Authenticated but not allowed (wrong role, unverified account) |
| `404` | Resource missing, or not owned by the caller |
| `409` | Conflicting ID, email already registered, idempotency key reuse with different data |
| `500` | Unexpected error, without exposing credentials or stack traces |

## 11. Example API Flow: Create Order

```text
Vue order form
   | POST /api/orders  (Bearer token)
   v
Flask route -> verify JWT -> load user and role
   v
Validate payload; customers may only order for their own linked profile
   v
Check customer and products; select server-side prices
   v
Begin transaction -> insert order -> insert items -> calculate total -> commit
   v
Return order ID, items, status and total
   v
Vue displays confirmation
```

On validation failure return a client error with field-level details. On a database failure roll back and return a generic error.

## 12. Project Structure

```text
Order_Sales_Management/
├── server/                      Flask backend
│   ├── .env                     not committed
│   ├── .env.example
│   ├── requirements.txt
│   ├── run.py
│   └── app/
│       ├── __init__.py          app factory, blueprint registration
│       ├── config.py            reads .env, sets DB schema
│       ├── extensions.py        db, jwt, mail
│       ├── models.py            User, Customer, Product, Order, OrderItem
│       ├── routes/
│       │   ├── auth.py
│       │   ├── orders.py
│       │   ├── customers.py
│       │   ├── products.py
│       │   └── reports.py
│       ├── services/
│       │   ├── auth_service.py
│       │   ├── order_service.py     validation, totals, status rules, ownership scope
│       │   └── report_service.py
│       └── utils/
│           └── decorators.py    role_required, current_user
├── client/                      Vue 3 frontend
│   └── src/
│       ├── router/index.js
│       ├── stores/              auth, orders, reports (Pinia)
│       ├── services/api.js      Axios instance with token interceptor
│       └── views/               Login, Register, VerifyEmail, ForgotPassword,
│                                ResetPassword, Orders, OrderDetail, Reports
├── db/
│   ├── init.sql                 schema and tables
│   └── load_data.ps1            CSV -> staging -> tables
├── data/
│   └── Online-Store-Orders-Updated.csv
└── README.md
```

Services hold business rules and contain no HTTP code. Routes parse requests, call a service and return JSON. Start with the smallest structure that keeps them understandable.

## 13. Database Setup and Configuration

1.  Create the schema and tables with `db/init.sql` (psql or pgAdmin), separately from the application.
2.  Give the application's database user only the permissions it needs.
3.  Configure settings through environment variables in `server/.env`.
4.  Confirm schema and table names match what Flask uses.
5.  Load the CSV through the controlled import workflow.
6.  Verify row counts, rejected records and sample order totals.

Example `.env.example`:

```dotenv
FLASK_ENV=development
DB_SCHEMA=order_sales
DATABASE_URL=postgresql+psycopg2://app_user:change_me@localhost:5432/your_database
JWT_SECRET_KEY=replace_with_a_long_random_string
JWT_ACCESS_TOKEN_EXPIRES_HOURS=12
FRONTEND_URL=http://localhost:5173
```

Never commit the real `.env` or production credentials. Use a secret manager or deployment environment variables in production.

Run the backend (Windows PowerShell):

```powershell
cd server
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
```

## 14. Indexing and Performance

Primary keys and unique constraints create their own indexes. The schema adds:

| Index | Supports |
|---|---|
| `idx_orders_customer_date` | A customer's orders, by date |
| `idx_orders_status` | Status filters and counts |
| `idx_order_items_product` | Product-wise reports |
| `uq_users_email_lower` | Case-insensitive unique login lookup |

Add more only for real query patterns, and check them with `EXPLAIN ANALYZE`.

## 15. Testing Checklist

### Authentication
-   [ ] Register a customer; the role is always `customer`, even if the request sends another role.
-   [ ] Reject a duplicate email, including one that differs only by letter case.
-   [ ] Reject a password shorter than 8 characters.
-   [ ] Verification works once; an expired or reused token fails.
-   [ ] An unverified account cannot log in.
-   [ ] Wrong credentials return a generic `401`.
-   [ ] Forgot-password gives the same response for known and unknown emails.
-   [ ] Reset works once; an expired or reused token fails; the old password stops working.

### Authorization
-   [ ] A customer sees only their own orders.
-   [ ] A customer requesting another customer's order ID gets `404`.
-   [ ] A customer cannot change status, call admin endpoints or view reports (`403`).
-   [ ] An admin can list and manage all orders.
-   [ ] No token returns `401`.
-   [ ] An unlinked customer account sees no orders.

### Order management
-   [ ] Create an order with one product and with multiple products.
-   [ ] Retrieve order details and the calculated total.
-   [ ] Update status with an allowed transition; reject a disallowed one.
-   [ ] Reject unknown customers and products.

### Validation
-   [ ] Reject missing required fields, invalid or missing dates, zero or negative quantities, non-numeric quantities, negative prices.
-   [ ] Handle unsupported statuses explicitly.

### Duplicate handling
-   [ ] Reject a repeated order ID.
-   [ ] An idempotent retry does not create another order.
-   [ ] Suspicious matching lines are flagged, not deleted.

### Reporting
-   [ ] Product-wise units and amounts are correct.
-   [ ] Date-wise totals are correct.
-   [ ] The cancelled and returned policy is applied consistently.
-   [ ] Orders with no items do not produce wrong totals.

### Reliability and security
-   [ ] Failed multi-table writes roll back.
-   [ ] SQL is parameterized.
-   [ ] Credentials and tokens stay out of source control and logs.
-   [ ] Error responses do not expose internals.

## 16. Implementation Plan

Each phase has a deliverable and a check.

| Step | Work | Verify |
|---|---|---|
| 1. Database setup | Run `init.sql`: schema, auth tables, business tables, constraints, indexes | Foreign keys, unique and check constraints reject bad rows |
| 2. CSV ingestion | Load into `staging_orders` as text; validate fields, dates, numbers, statuses, conflicts | Staging count matches the file; invalid rows are recorded |
| 3. Data migration | Insert customers, products, orders, order items in transactions; reconciliation report | Every source row is imported or documented as rejected |
| 4. Backend skeleton | Config, extensions, models, app factory, `/health` | Server boots; `/health/db` returns counts |
| 5. Authentication | Register, hashed tokens, verify, login, reset, `/api/auth/me` | Section 15, Authentication |
| 6. Roles and ownership | `role_required`, ownership scope on order endpoints, admin link endpoint | Section 15, Authorization |
| 7. Order processing | Validation, server-side prices, totals, transactions, idempotency | Bad input rejected; failures leave no partial data |
| 8. Status and reports | Status transitions, optional history, product, daily and monthly reports | Totals match line items; filters work |
| 9. Vue frontend | Auth screens, order history, details, admin management, reports | Loading, success, validation, unauthorized and error states handled |
| 10. Integration and deployment | End-to-end tests, env-based secrets, HTTPS, narrow CORS, logs, backups | Authorization, duplicates, token expiry, bad CSV rows, report accuracy covered |

## 17. Scope and Assumptions

-   PostgreSQL is the source of truth for persistent data.
-   `orders` is the order header; `order_items` holds its products.
-   Each order item stores the unit price charged at purchase time.
-   Sales reports use an explicit status rule (`Shipped`, `Delivered`).
-   CSV records are validated before being treated as confirmed data.
-   Email delivery is simulated in development by printing links to the server console.
-   Included in scope: registration, email verification, password reset, Admin and Customer roles, per-customer order ownership.
-   Out of scope unless added: inventory reservation, payments, refunds, shipping integrations, multi-factor authentication, social login.
-   The schema is a design baseline. Adapt constraints and status transitions to the real business rules.

## Conclusion

The normalized design separates customers, products, order headers and order items, so multi-product orders need no duplicated customer or product data. PostgreSQL constraints protect integrity. Flask implements business rules, authentication, role checks and ownership rules. Vue provides the interface. The same model supports order totals, duplicate checks, status tracking and product-wise and date-wise sales reports, and keeps each customer's data private.
