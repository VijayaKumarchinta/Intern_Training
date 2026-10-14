# Order & Sales Management Application — Design Documentation

**Version:** 1.0
**Stack:** Vue.js · Flask · PostgreSQL
**Purpose:** Simulate order processing and sales operations for a retail/e-commerce business.

---

## Table of Contents

- [Order \& Sales Management Application — Design Documentation](#order--sales-management-application--design-documentation)
  - [Table of Contents](#table-of-contents)
  - [1. Project Overview](#1-project-overview)
  - [2. Functional Requirements](#2-functional-requirements)
    - [2.1 Order Management](#21-order-management)
    - [2.2 Validation Rules](#22-validation-rules)
    - [2.3 Duplicate Order Detection](#23-duplicate-order-detection)
    - [2.4 Reports](#24-reports)
    - [2.5 Order Status Tracking](#25-order-status-tracking)
  - [3. Non-Functional Requirements](#3-non-functional-requirements)
  - [4. Database Design (Pre-existing Schema)](#4-database-design-pre-existing-schema)
    - [Loading the CSV dataset (one-time)](#loading-the-csv-dataset-one-time)
  - [5. Architecture](#5-architecture)
    - [Backend layers](#backend-layers)
    - [Frontend structure](#frontend-structure)
  - [6. API Design](#6-api-design)
    - [Auth](#auth)
    - [Orders](#orders)
    - [Reports](#reports)
    - [Admin](#admin)
  - [7. Business Logic Details](#7-business-logic-details)
    - [7.1 Order Total Calculation](#71-order-total-calculation)
    - [7.2 Validation (service layer)](#72-validation-service-layer)
    - [7.3 Duplicate Detection](#73-duplicate-detection)
    - [7.4 Status Transition Map](#74-status-transition-map)
  - [8. Auth \& Roles — Decisions](#8-auth--roles--decisions)
  - [9. The 7 Software Engineering Principles Applied](#9-the-7-software-engineering-principles-applied)
  - [10. Setup \& Run](#10-setup--run)
    - [Backend](#backend)
    - [Frontend](#frontend)
  - [11. Deliverables Checklist](#11-deliverables-checklist)

---

## 1. Project Overview

**Goal:** Build an Order & Sales Management Application that simulates the order processing and sales operations of a retail/e-commerce business.

**Core Capabilities:**
- Manage customer orders
- Validate order details
- Calculate order totals
- Track order statuses
- Identify duplicate orders
- Generate product-wise reports
- Generate date-wise reports
- User registration & login (with email verification, password reset)
- Role-based access (Admin / Customer)
- Customers view only their own orders; Admins manage all orders

**Stack:**

| Layer     | Technology                                          |
|-----------|-----------------------------------------------------|
| Frontend  | Vue.js (Vue 3 + Vite + Pinia + Vue Router)          |
| Backend   | Flask (Python) + Flask-JWT-Extended                 |
| Database  | PostgreSQL (pre-existing schema — app only connects)|
| ORM       | SQLAlchemy (Flask-SQLAlchemy)                       |
| Auth      | JWT + bcrypt (passlib)                              |
| Email     | Flask-Mail (SMTP)                                   |

> **Important:** The database is **not created by the application**. The DDL below is provided so the DB/schema/tables exist in advance. The Flask app only connects to the existing schema.

---

## 2. Functional Requirements

### 2.1 Order Management
- Create, read, update, delete orders
- Each order has: OrderID, Date, CustomerID, Product, Quantity, UnitPrice, OrderStatus
- Compute line total = Quantity × UnitPrice
- Compute order total (aggregated per OrderID if multi-line)

### 2.2 Validation Rules

| Field       | Rule                                                             |
|-------------|------------------------------------------------------------------|
| OrderID     | Required, unique, format `ORD####`                               |
| Date        | Required, valid date, not in future                              |
| CustomerID  | Required, must exist in customers table                          |
| Product     | Required, must be in allowed product list                        |
| Quantity    | Integer, > 0, ≤ 1000                                             |
| UnitPrice   | Numeric, ≥ 0                                                     |
| OrderStatus | One of: `Pending`, `Shipped`, `Delivered`, `Cancelled`, `Returned`, `Received` |

**Data issues found in dataset (must be handled by validation):**
- `ORD0016` — Quantity = `"two"` (non-numeric)
- `ORD0123` — Quantity = `-3` (negative)
- `ORD0290` — Quantity = `0` (zero)
- `ORD0624` — UnitPrice = `-15.00` (negative)
- `ORD0702` — UnitPrice = `0.00` (zero)
- `ORD0457`, `ORD0741`, `ORD1200` — missing Date
- Status `Received` appears (ORD0082, ORD0327) — not in canonical list

### 2.3 Duplicate Order Detection
An order is flagged as **potential duplicate** when:
- Same CustomerID + Product + Quantity + UnitPrice + Date (exact match), OR
- Same CustomerID + Product within 24 hours (fuzzy match)

### 2.4 Reports
- **Product-wise:** total quantity sold, total revenue, order count per product
- **Date-wise:** daily/weekly/monthly totals (orders, revenue)
- Filterable by status, date range, product

### 2.5 Order Status Tracking
Status transition state machine:
```
Pending   → Shipped → Delivered → Returned
Pending   → Cancelled
Shipped   → Returned
```
Invalid transitions rejected.

---

## 3. Non-Functional Requirements

- **Security:** JWT auth, bcrypt password hashing, role-based route guards
- **Performance:** indexed queries, pagination on list endpoints
- **Maintainability:** layered architecture (routes → services → repositories → models)
- **Testability:** pure functions for validation & totals
- **Scalability:** stateless API, connection pooling via SQLAlchemy

---

## 4. Database Design (Pre-existing Schema)

> Run these commands **once, manually** in PostgreSQL before starting the app. The Flask app only connects.

```sql
-- =========================================================
-- DATABASE CREATION (run as superuser, once)
-- =========================================================
CREATE DATABASE order_sales_db;

-- Connect to it
\c order_sales_db;

-- =========================================================
-- USERS (for auth: admin + customer)
-- =========================================================
CREATE TABLE users (
    id                  SERIAL PRIMARY KEY,
    email               VARCHAR(255) UNIQUE NOT NULL,
    password_hash       VARCHAR(255) NOT NULL,
    full_name           VARCHAR(255),
    role                VARCHAR(20) NOT NULL DEFAULT 'customer'
                        CHECK (role IN ('admin','customer')),
    is_verified         BOOLEAN NOT NULL DEFAULT FALSE,
    verification_token  VARCHAR(255),
    reset_token         VARCHAR(255),
    reset_token_expires TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =========================================================
-- CUSTOMERS (business entity; links optionally to a user)
-- =========================================================
CREATE TABLE customers (
    customer_id VARCHAR(20) PRIMARY KEY,      -- e.g. C0001
    user_id     INTEGER REFERENCES users(id) ON DELETE SET NULL,
    name        VARCHAR(255),
    email       VARCHAR(255),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =========================================================
-- PRODUCTS (reference list for validation)
-- =========================================================
CREATE TABLE products (
    product_id   SERIAL PRIMARY KEY,
    product_name VARCHAR(100) UNIQUE NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =========================================================
-- ORDERS
-- =========================================================
CREATE TABLE orders (
    order_id     VARCHAR(20) PRIMARY KEY,      -- e.g. ORD0001
    order_date   DATE NOT NULL,
    customer_id  VARCHAR(20) NOT NULL REFERENCES customers(customer_id),
    product      VARCHAR(100) NOT NULL,
    quantity     INTEGER NOT NULL CHECK (quantity > 0 AND quantity <= 1000),
    unit_price   NUMERIC(12,2) NOT NULL CHECK (unit_price >= 0),
    order_status VARCHAR(20) NOT NULL
                 CHECK (order_status IN
                     ('Pending','Shipped','Delivered','Cancelled','Returned','Received')),
    line_total   NUMERIC(14,2) GENERATED ALWAYS AS (quantity * unit_price) STORED,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =========================================================
-- DUPLICATE FLAGS (audit table written by app)
-- =========================================================
CREATE TABLE duplicate_flags (
    id           SERIAL PRIMARY KEY,
    order_id     VARCHAR(20) NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    duplicate_of VARCHAR(20) NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    reason       VARCHAR(255),
    flagged_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (order_id, duplicate_of)
);

-- =========================================================
-- INDEXES
-- =========================================================
CREATE INDEX idx_orders_customer  ON orders(customer_id);
CREATE INDEX idx_orders_date      ON orders(order_date);
CREATE INDEX idx_orders_product   ON orders(product);
CREATE INDEX idx_orders_status    ON orders(order_status);
CREATE INDEX idx_orders_cust_prod ON orders(customer_id, product);
CREATE INDEX idx_users_email      ON users(email);

-- =========================================================
-- SEED PRODUCTS (matching dataset)
-- =========================================================
INSERT INTO products (product_name) VALUES
('Monitor'),('Phone'),('Tablet'),('Chair'),
('Printer'),('Laptop'),('Desk');
```

### Loading the CSV dataset (one-time)

```sql
-- After creating tables and loading customers + products,
-- use \copy from psql:
\copy orders(order_id, order_date, customer_id, product, quantity, unit_price, order_status)
FROM 'Online-Store-Orders-Updated.csv'
WITH (FORMAT csv, HEADER true, NULL '');
```

> **Note:** Rows with invalid values (`two`, `-3`, `0`, missing date) must be cleaned **before** load, or loaded into a `staging_orders` table and validated by the app. Recommended: load into `staging_orders` and let the app's validation endpoint promote valid rows into `orders`.

---

## 5. Architecture

```
┌────────────────────┐        HTTPS/JSON        ┌─────────────────────┐
│  Vue.js SPA        │  ──────────────────────▶ │  Flask REST API     │
│  (Pinia, Router)   │ ◀──────────────────────  │  (JWT Auth)         │
└────────────────────┘                          └──────────┬──────────┘
                                                           │ SQLAlchemy
                                                           ▼
                                                 ┌─────────────────────┐
                                                 │  PostgreSQL         │
                                                 │  (pre-existing)     │
                                                 └─────────────────────┘
```

### Backend layers

```
app/
├── __init__.py          # app factory
├── config.py            # env config
├── extensions.py        # db, jwt, mail, bcrypt
├── models/              # SQLAlchemy models (mirror existing tables)
├── schemas/             # marshmallow validation
├── repositories/        # raw DB access
├── services/            # business logic (totals, dup detection, reports)
├── routes/              # blueprints (auth, orders, reports, admin)
├── utils/               # decorators, helpers
└── run.py
```

### Frontend structure

```
src/
├── main.js
├── router/index.js
├── stores/          # pinia: auth, orders, reports
├── services/api.js  # axios instance
├── views/           # Login, Register, Orders, Reports, AdminUsers
└── components/      # OrderForm, OrderTable, StatusBadge, Filters
```

---

## 6. API Design

### Auth

| Method | Endpoint                          | Role   | Description                        |
|--------|-----------------------------------|--------|------------------------------------|
| POST   | `/api/auth/register`              | public | Register (sends verification email)|
| GET    | `/api/auth/verify/<token>`        | public | Verify email                       |
| POST   | `/api/auth/login`                 | public | Login → JWT                        |
| POST   | `/api/auth/forgot-password`       | public | Request reset link                 |
| POST   | `/api/auth/reset-password/<token>`| public | Reset password                     |
| GET    | `/api/auth/me`                    | any    | Current user profile               |

### Orders

| Method | Endpoint                        | Role                      | Description                    |
|--------|---------------------------------|---------------------------|--------------------------------|
| GET    | `/api/orders`                   | admin: all, customer: own | List + filters + pagination    |
| GET    | `/api/orders/<id>`              | admin / owner             | Get one                        |
| POST   | `/api/orders`                   | admin                     | Create                         |
| PUT    | `/api/orders/<id>`              | admin                     | Update                         |
| PATCH  | `/api/orders/<id>/status`       | admin                     | Status transition              |
| DELETE | `/api/orders/<id>`              | admin                     | Delete                         |
| POST   | `/api/orders/validate`          | admin                     | Dry-run validate payload       |
| GET    | `/api/orders/duplicates`        | admin                     | List duplicate flags           |

### Reports

| Method | Endpoint                        | Role  | Description                    |
|--------|---------------------------------|-------|--------------------------------|
| GET    | `/api/reports/product-wise`     | admin | Product aggregates             |
| GET    | `/api/reports/date-wise`        | admin | Daily/weekly/monthly           |
| GET    | `/api/reports/summary`          | admin | KPIs (total orders, revenue)   |

### Admin

| Method | Endpoint                          | Role  | Description    |
|--------|-----------------------------------|-------|----------------|
| GET    | `/api/admin/users`                | admin | List users     |
| PATCH  | `/api/admin/users/<id>/role`      | admin | Change role    |

---

## 7. Business Logic Details

### 7.1 Order Total Calculation

```python
line_total  = Decimal(quantity) * Decimal(unit_price)
order_total = sum(line_total for line in order_lines)
```
Use `Decimal` (never float) for money.

### 7.2 Validation (service layer)

```python
def validate_order(payload):
    errors = []
    if not re.match(r"^ORD\d{4}$", payload["order_id"]):
        errors.append("Invalid OrderID format")
    if payload["quantity"] <= 0 or payload["quantity"] > 1000:
        errors.append("Quantity must be 1..1000")
    if payload["unit_price"] < 0:
        errors.append("UnitPrice cannot be negative")
    if payload["product"] not in PRODUCTS:
        errors.append("Unknown product")
    if payload["order_status"] not in STATUSES:
        errors.append("Invalid status")
    ...
```

### 7.3 Duplicate Detection

```sql
-- Exact match
SELECT order_id FROM orders
WHERE customer_id = :cid AND product = :prod
  AND quantity = :qty AND unit_price = :price
  AND order_date = :date
  AND order_id <> :current_id;

-- Fuzzy (same customer+product within 24h)
SELECT order_id FROM orders
WHERE customer_id = :cid AND product = :prod
  AND order_date BETWEEN :date - INTERVAL '1 day' AND :date + INTERVAL '1 day'
  AND order_id <> :current_id;
```

### 7.4 Status Transition Map

```python
ALLOWED_TRANSITIONS = {
    "Pending":   {"Shipped", "Cancelled"},
    "Shipped":   {"Delivered", "Returned"},
    "Delivered": {"Returned"},
    "Cancelled": set(),
    "Returned":  set(),
    "Received":  set(),
}
```

---

## 8. Auth & Roles — Decisions

| Question                          | Decision                                                      |
|-----------------------------------|---------------------------------------------------------------|
| Implement registration & login?   | **Yes** — JWT-based                                           |
| Email verification?               | **Yes** — token emailed on register; user cannot log in until verified |
| Password reset?                   | **Yes** — token emailed, expires in 1h                        |
| Roles?                            | **Yes** — `admin`, `customer`                                 |
| Scoping?                          | Customers see only their orders; admins see all               |

**Seeded admin:** create manually after DB setup:

```sql
INSERT INTO users (email, password_hash, full_name, role, is_verified)
VALUES ('admin@store.com', '<bcrypt-hash>', 'Store Admin', 'admin', TRUE);
```

---

## 9. The 7 Software Engineering Principles Applied

| # | Principle                          | How It's Applied                                                                 |
|---|------------------------------------|----------------------------------------------------------------------------------|
| 1 | **Single Responsibility (SRP)**    | Each module has one job: `repositories/` = DB access, `services/` = business rules, `routes/` = HTTP, `schemas/` = validation |
| 2 | **Open/Closed (OCP)**              | Status transition map & product list are data-driven; adding new status = edit config, not code |
| 3 | **Liskov Substitution (LSP)**      | Repository interfaces (`OrderRepository`) can be swapped (SQL vs mock) without breaking services |
| 4 | **Interface Segregation (ISP)**    | Separate blueprints (`auth`, `orders`, `reports`, `admin`) expose only relevant endpoints |
| 5 | **Dependency Inversion (DIP)**     | Services depend on repository abstractions injected via app factory, not direct DB calls |
| 6 | **DRY (Don't Repeat Yourself)**    | Shared validators, `Decimal` money helper, single `api.js` axios instance        |
| 7 | **KISS (Keep It Simple)**          | No microservices, no CQRS, no message queues — monolith Flask + Vue, one Postgres DB |

---

## 10. Setup & Run

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install flask flask-sqlalchemy flask-jwt-extended flask-mail \
            passlib[bcrypt] psycopg2-binary marshmallow python-dotenv
```

Create `.env`:

```
DATABASE_URL=postgresql+psycopg2://user:pass@localhost:5432/order_sales_db
JWT_SECRET_KEY=change-me
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=you@example.com
MAIL_PASSWORD=your-app-password
```

Run:

```bash
flask --app app run --debug
```

### Frontend

```bash
cd frontend
npm create vite@latest . -- --template vue
npm install axios pinia vue-router
npm run dev
```

---

## 11. Deliverables Checklist

- [x] Pre-existing DB DDL (users, customers, products, orders, duplicate_flags, indexes)
- [x] CSV load strategy (staging → validate → promote)
- [x] Flask layered backend design
- [x] Vue 3 SPA structure
- [x] Full auth (register, verify, login, reset)
- [x] Role-based access (admin/customer) with order scoping
- [x] Order CRUD + validation + totals
- [x] Duplicate detection (exact + fuzzy)
- [x] Status transition enforcement
- [x] Product-wise & date-wise reports
- [x] 7 principles explicitly mapped
- [x] No overengineering — single Flask app, single Postgres DB, no queues/cache/microservices

---

**End of document.**