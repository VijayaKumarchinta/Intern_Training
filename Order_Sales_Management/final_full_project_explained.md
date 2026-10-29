# Final Full Project Explained — OrderSalesManagement (OrderSync)

This is the complete, integrated explanation of the **Intern_Training** project `Order_Sales_Management/`: the technology stack, architecture, database design, authentication/authorization, order workflow, reports, frontend structure, and backend structure. It also explains how the frontend, API, and database work together.

---

## 1. What this project is

**OrderSalesManagement** is an order and sales management web application built as an internship training project.

- A **Vue 3 frontend** (Vite + Pinia + Vue Router + Axios).
- A **Flask REST API** (Python + Flask + Flask-SQLAlchemy).
- A **PostgreSQL database** with a pre-created schema `order_sales`.

The app supports:

- Customer and admin roles.
- Registration, email verification, login, and password reset.
- Per-customer order ownership (customers see only their own orders).
- Validated order creation with server-side pricing.
- Strict order status transitions.
- Duplicate order detection.
- Product-wise, date-wise, and monthly sales reports.
- A dashboard with KPIs, revenue chart, latest orders, and duplicate alerts.

---

## 2. Technology stack

| Layer | Technology | Responsibility |
|-------|------------|------------------|
| Frontend | Vue 3 + Vite + Pinia + Vue Router + Axios | Auth screens, order list/detail, status updates, reports |
| Backend | Python + Flask + Flask-SQLAlchemy | API endpoints, validation, business rules, transactions |
| Auth | Flask-JWT-Extended + bcrypt | Login tokens, password hashing, role checks, token revocation |
| Database | PostgreSQL (`order_sales` schema) | Relational data, constraints, indexes, reports |
| Email (dev) | Flask-Mail + dev log | OTP and reset-link delivery (dev) |
| Testing | pytest + Flask test client | Backend test suite |

---

## 3. Architecture

```text
Browser
  -> Vue SPA
    -> Pinia stores
      -> api.js (Axios)
        -> Vite proxy (/api -> http://127.0.0.1:5000)
          -> Flask route
            -> service (business rules)
              -> SQLAlchemy / PostgreSQL
                -> JSON
                  -> store
                    -> Vue component
```

Key rules:

- The browser only talks to Flask over HTTP JSON. Flask never lets the browser touch PostgreSQL directly.
- Flask enforces authentication, authorization, validation, business rules, and report queries.
- The frontend route guards improve UX; the backend decorators are the real security.
- Routes are thin HTTP controllers. Services contain the business logic.
- The database model is normalized: `users`, `customers`, `products`, `orders`, `order_items`.

---

## 4. Database design

### Schema: `order_sales`

The app connects to this schema at startup. The app does **not** create or drop it at runtime.

| Table | Purpose |
|-------|---------|
| `users` | Login credentials, role, verification, password-reset, token version |
| `customers` | Customer profiles; can be linked to one user via `user_id` |
| `products` | Product catalog and current price |
| `orders` | Order header: customer, date, status |
| `order_items` | Products, quantities, historical unit price per order |
| `staging_orders` | Raw CSV rows before import validation |

### Relationships

- `users` 1 ↔ 0..1 `customers`
- `customers` 1 ↔ many `orders`
- `orders` 1 ↔ many `order_items`
- `products` 1 ↔ many `order_items`
- `customers.user_id` unique → one user per customer
- `order_items.order_id` cascades delete → order + items are deleted together

### Design decisions

- `users.email` is unique case-insensitively (`LOWER(email)`).
- Passwords, verification tokens, and reset tokens are stored only as hashes.
- `order_items.unit_price` preserves the price charged at purchase time.
- `products.current_price` is optional catalog data; it is the server-side price used for new orders.
- New-order prices come from the server (`products.current_price`), never from the browser.
- `orders.order_status` is restricted to a fixed set; the app enforces legal transitions.
- Sales reports count only `Shipped` + `Delivered` orders for revenue.
- Reports use `order_items.unit_price` (historic price), not `products.current_price`.

---

## 5. Authentication and authorization

### Account lifecycle

#### 1. Registration (public)

- Input: email, password, full name, customer ID.
- Server:
  - Normalizes email (trim + lowercase).
  - Validates email and password (8–72 bytes).
  - Requires an existing customer ID.
  - Creates a `User` with `role='customer'`, `is_verified=FALSE`, `token_version=0`, and a hashed 6-digit OTP.
  - Sends the OTP via the dev email log.
- Response: `201` with `{ message: "Verification code sent", user_id, email, is_verified: false }`.

#### 2. Verify email (public)

- Submit the 6-digit OTP and optional `customer_id`.
- Server checks:
  - Unknown email → `\"Invalid code\"`
  - Missing/expired token
  - Attempt limits (returns remaining attempts on failure)
- On success sets `is_verified=True`, clears OTP state, and links the customer if supplied.

#### 3. Login (public)

- Server:
  - Finds user by lowercased email.
  - Rejects missing/invalid credentials (generic `401`).
  - Rejects unverified accounts (`401`).
- On success, creates a JWT with:
  - `identity = user.id`
  - claims: `role`, `email`, `tv` (token version)

#### 4. Reset password (public)

- Request a reset link via email.
- Submit token + new password.
- Server:
  - Finds user by hashed token; rejects unknown/expired/inactive tokens.
  - Validates the new password.
  - On success: replaces password hash, clears reset/verification state, and increments `token_version`, invalidating old JWTs.

### Role and ownership

- `role_required(Role.ADMIN.value)` protects admin endpoints.
- `auth_required` verifies the JWT and resolves the user from the DB.
- A `token_version` mismatch returns `401`, enabling token revocation.
- `can_view_order(user, order)`:
  - Admins → always true.
  - Customers → orders whose `customer.user_id` matches their own ID.
- Customers trying another customer’s order ID get `404`, not `403`, to avoid leaking order IDs.
- `customers.user_id` unique → a customer record can be linked to at most one user.

### Frontend guards

- Global `beforeEach` guard in `router/index.js`:
  - Protected routes redirect to `/login`.
  - Admin routes redirect non-admins to `/app/orders`.
  - Customer visiting `/app/orders` → `/app/my-orders`.
  - Admin visiting `/app/my-orders` → `/app/orders`.

---

## 6. Order workflow

### Create order

Payload:

```json
{
  "order_id": "ORD1234",
  "customer_id": "C5678",
  "order_date": "2026-10-21",
  "items": [
    { "product_id": 1, "quantity": 2 }
  ]
}
```

Server rules:

- `order_id` must match `ORD####`.
- `customer_id` must match `C####` and exist.
- At least one item required.
- Quantity must be an integer between 1 and 1000.
- Product must exist and have a price.
- No duplicate product within the same order.
- `order_status` optional; default `Pending`.
- Server uses `products.current_price` for all line items. Client `unit_price` is ignored.

Result: order created as `Pending`, with line items and a server-side calculated total.

### Status machine

| From | Allowed next status |
|------|---------------------|
| `Pending` | `Received`, `Shipped`, `Cancelled` |
| `Received` | `Shipped`, `Cancelled` |
| `Shipped` | `Delivered`, `Returned` |
| `Delivered` | `Returned` |
| `Cancelled` | none |
| `Returned` | none |

- The frontend shows only legal next steps.
- The backend rejects illegal transitions with `400`.
- `Cancelled` and `Returned` are terminal states.

### Duplicate detection

A duplicate group is defined by the same:

- `customer_id`
- `product_id`
- `quantity`
- `unit_price`
- `order_date`

Response:

```json
{
  "duplicates": [
    {
      "customer_id": "C5678",
      "product_id": 1,
      "product_name": "Phone",
      "quantity": 2,
      "unit_price": 150.0,
      "order_date": "2026-10-21",
      "occurrences": 2,
      "order_ids": ["ORD9001", "ORD9002"]
    }
  ]
}
```

- Admin-only endpoint.
- UI lets the admin cancel one copy (moves it to `Cancelled`) while keeping the other record.
- Matching rows do not prove a duplicate; a customer may legitimately buy the same product twice.

---

## 7. Sales reporting

- Revenue counts orders with `order_status` `Shipped` + `Delivered` only.
- Report totals use `order_items.unit_price` (historic price), not `products.current_price`.
- `GET /api/reports/summary` returns:
  - KPIs: `revenue`, `sales_orders`, `units_sold`, `awaiting_action`, `total_orders`
  - `status_breakdown`
  - `latest_orders`
  - `duplicate_groups`
  - `product_breakdown`
  - `monthly_breakdown`

### Endpoints

| Endpoint | Auth | Query / format |
|---|---|---|
| `GET /api/reports/summary` | Admin | JSON |
| `GET /api/reports/product-wise?format=csv` | Admin | JSON or CSV |
| `GET /api/reports/date-wise?group=day|month&format=csv` | Admin | JSON or CSV |

- CSV headers: `Product, Items Sold, Units Sold, Revenue (INR)` and `Period (<group>), Orders, Units Sold, Revenue (INR)`.
- Revenue is formatted with two decimals.

---

## 8. Frontend architecture

### Bootstrap

- `main.js`:
  - Creates the Vue app.
  - Registers Pinia and Vue Router.
  - Mounts to `#app`.
- `style.css`: design tokens and base styles (`--bg-app`, `--ink`, `--blue`, `--lime`, `--radius-card`, etc.).

### Routing and guards

- `router/index.js`:
  - Public routes: `/`, `/login`, `/register`, `/forgot-password`, `/reset-password`.
  - Protected `/app` layout with children:
    - `/app/orders`
    - `/app/my-orders`
    - `/app/orders/:id`
    - `/app/products`, `/app/customers`, `/app/reports`, `/app/duplicates`, `/app/new-order`, `/app/users`, `/app/totals`
  - Guard:
    - `requiresAuth` → redirect to `/login`
    - `requiresAdmin` → redirect non-admins to `/app/orders`
    - Customer on `/app/orders` → `/app/my-orders`
    - Admin on `/app/my-orders` → `/app/orders`

### HTTP client

- `services/api.js`:
  - Base URL `/api`; Vite proxies to Flask.
  - Attaches `Authorization: Bearer <token>` on every request.
  - On `401` or `422`, clears localStorage credentials and redirects to `/login`.

### Pinia stores

- `stores/auth.js`:
  - `token`, `user`
  - `isAuthenticated`, `isAdmin` getters
  - `login()`, `fetchMe()`, `logout()`
- `stores/summary.js`:
  - `data`, `loading`, `error`
  - `fetch(force)` — cached summary from `/reports/summary`

### Global utilities

- `utils/format.js`:
  - `money(value)` → ₹ formatting
  - `number(value)`
  - `percent(part, whole)`
  - `percentLabel(part, whole)`
  - `formatDate(iso)`
  - `initials(name)`

### Pages

| Page | Auth scope | Role |
|------|------------|------|
| `Landing.vue` | public | Marketing homepage |
| `Login.vue` | public | Login |
| `Register.vue` | public | Two-step registration + OTP |
| `ForgotPassword.vue` | public | Password-reset request |
| `ResetPassword.vue` | token | Password reset |
| `MyOrders.vue` | customer | Customer’s own orders |
| `Orders.vue` | admin | Order list, pagination, status updates |
| `CreateOrder.vue` | admin | New order form |
| `OrderDetail.vue` | owner/admin | Order detail + status UI |
| `Reports.vue` | admin | Dashboard (KPI, chart, latest orders, duplicates) |
| `Customers.vue` | admin | Customer list + create/link |
| `Products.vue` | admin | Product catalog + price edit |
| `Duplicates.vue` | admin | Duplicate investigation |
| `Users.vue` | admin | User list |
| `Totals.vue` | admin | Full-lifetime totals |

### Shared components

- `components/Icon.vue` — inline SVG icon renderer.
- `components/AuthShell.vue` — public auth layout wrapper.
- `layouts/AppLayout.vue` — dashboard shell with navigation.

---

## 9. Backend architecture

### App factory and config

- `app/__init__.py`: `create_app()`
- `config.py`: environment settings, logging, DB/JWT/Mail configuration
- `extensions.py`: `db`, `jwt`, `mail`, `hash_password`, `verify_password`

### Models

- `models.py`: `User`, `Customer`, `Product`, `Order`, `OrderItem`

### Auth helpers

- `constants.py`: `Role` enum
- `decorators.py`: `auth_required`, `role_required`
- `permissions.py`: `is_admin`, `is_customer`, `owns_customer`, `can_view_order`
- `validators.py`: email/password validation
- `email.py`: dev email simulation

### Business logic

- `services/auth_service.py`: registration, verification, login, password reset, customer linking
- `services/order_service.py`: order creation/validation, status transitions, duplicates, reports

### HTTP layer

| Route file | Base path | Endpoints |
|------------|-----------|-----------|
| `routes/auth.py` | `/api/auth` | register, verify, resend, login, forgot-password, reset-password, me |
| `routes/orders.py` | `/api/orders` | list, detail, create, status, duplicates |
| `routes/customers.py` | `/api/customers` | list, create, link |
| `routes/products.py` | `/api/products` | list, create, update, delete |
| `routes/reports.py` | `/api/reports` | summary, product-wise, date-wise |
| `routes/users.py` | `/api/users` | list, create, role update, delete |

---

## 10. End-to-end flow

### Login flow

1. User enters email and password.
2. `Login.vue` calls `auth.login()`.
3. `api.js` POSTs to `/api/auth/login`.
4. Flask route calls `auth_service.login()`.
5. Flask creates a JWT with `identity` and `tv`.
6. Browser stores token and user.
7. Router guard allows access to protected routes.

### Create order flow

1. Admin opens `/app/new-order`.
2. `CreateOrder.vue` loads products and customers.
3. On submit, Vue POSTs `/api/orders`.
4. Route calls `order_service.create_order()`.
5. Backend:
   - Validates `order_id`, `customer_id`, dates.
   - Checks product existence and price.
   - Inserts order header as `Pending`.
   - Inserts order items with server-side `unit_price`.
6. Returns order JSON with `total` and `item_count`.
7. UI redirects to the new order detail page.

### Customer order flow

1. Customer logs in.
2. `MyOrders.vue` calls `GET /api/orders`.
3. Backend returns only orders where `customers.user_id == current_user.id`.
4. UI shows the customer’s orders with totals.
5. Customer can open an order detail page, but cannot change status.

### Admin status flow

1. Admin clicks a status button on `Orders.vue` or `OrderDetail.vue`.
2. UI PATCHes `/api/orders/<id>/status`.
3. Backend checks `ALLOWED_TRANSITIONS`.
4. If valid, updates the order status and commits.
5. UI refreshes the summary.

### Report flow

1. Admin opens `/app/reports`.
2. UI calls `GET /api/reports/summary`.
3. Backend computes product/date/monthly breakdowns, revenue, sales orders, units sold, and duplicate groups.
4. UI renders KPIs, chart, latest orders, and duplicate alerts.

### Duplicate investigation flow

1. Admin opens `/app/duplicates`.
2. UI calls `GET /api/orders/duplicates`.
3. Backend returns groups with `occurrences > 1`.
4. UI shows order IDs, customer, product, quantity, price, date.
5. Admin can cancel one copy to keep the other record.

---

## 11. Where to find things in the code

| Task | Start here |
|------|------------|
| Add a public page | `client/src/views/NewView.vue` + `client/src/router/index.js` |
| Add an authenticated page | Add route with `meta: { requiresAuth: true }` |
| Add an admin page | Add route with `meta: { requiresAdmin: true }` |
| Add a new REST endpoint | `app/services/...` for logic, then `app/routes/...`, then tests |
| Change auth rules | `services/auth_service.py`, `decorators.py`, `models.py` |
| Change order creation | `services/order_service.py`, `models.py`, `routes/orders.py` |
| Change pricing rule | `order_service.py` (use server-side price) |
| Change status transitions | `order_service.py` (`ALLOWED_TRANSITIONS`) and frontend |
| Change reports | `services/order_service.py` report functions |
| Change layout | `layouts/AppLayout.vue`, `components/AuthShell.vue`, `components/Icon.vue` |

---

## 12. Testing

Run from `Order_Sales_Management/server`:

```powershell
python -m pytest tests/ -q
```

Result verified: **84 passed**

Test areas:

- `test_auth.py` — registration, OTP verification, login, password reset
- `test_permissions.py` — RBAC, customer isolation, ownership, token revocation
- `test_orders.py` — creation, validation, status transitions, pagination, duplicates
- `test_pricing.py` — server-side price enforcement
- `test_reports.py` — report accuracy
- `test_smoke.py` — fixtures and test DB checks

---

## 13. Verification performed

- Backend dependency resolution: passed.
- Test suite: **84 passed** (auth, permissions, pricing, reports, order workflow, smoke).
- Source files for this documentation were read from all `server/app/**/*.py` and all `client/src/**/*` Vue/JS/CSS files.
- No client-side build or live API ran in this environment (no local database process and no browser), so frontend runtime behavior and DB integration are not covered by an automated check here.

---

# Final one-paragraph summary

**OrderSalesManagement** is a Vue 3 + Flask + PostgreSQL order and sales management app with a clean three-layer architecture (Vue SPA → Flask REST API → PostgreSQL `order_sales` schema). The frontend handles public auth (`Landing`, `Login`, `Register`, `ForgotPassword`, `ResetPassword`), customer views (`MyOrders`), and admin panels (`Orders`, `CreateOrder`, `OrderDetail`, `Products`, `Customers`, `Users`, `Reports`, `Duplicates`, `Totals`) through Pinia stores, Vue Router with role guards, and an Axios client that attaches JWTs. The backend enforces JWT and role checks, customer ownership rules (customers only see their own orders), strict state-machine status transitions, server-side pricing, validation, and duplicate detection, then serves JSON plus CSV reports and a dashboard summary. Email verification and password reset work through hashed OTP/reset tokens, with dev-only email sim that writes to `server/logs/dev_emails.log`. The whole backend is covered by a passing pytest suite (**84 passed**), and the documented files in `docpack/` explain every frontend file, every endpoint, and every backend layer.
