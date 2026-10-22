# Endpoints Explained — OrderSalesManagement (OrderSync)

All paths are relative to the Flask app. Base URL: `http://127.0.0.1:5000`. In development, Vite proxies requests under `/api` to the Flask server, so the browser calls `/api/*`.

Every request sends `Content-Type: application/json`. Authentication uses:

```
Authorization: Bearer <JWT>
```

---

## 1. Auth endpoints (`/api/auth/*`)

### `POST /api/auth/register`

- **Role:** public (no auth required).
- **Purpose:** Register a new customer account.
- **Request body:**
  ```json
  {
    "email": "customer@example.com",
    "password": "SuperSecret123!",
    "full_name": "Jane Doe",
    "customer_id": "C1001"
  }
  ```
- **Behavior:**
  - Email is trimmed and lowercased.
  - Password must be 8–72 characters (or the request is rejected).
  - `customer_id` is required and must exist.
  - A 6-digit OTP is generated, hashed, and sent to the user (dev: written to `server/logs/dev_emails.log`).
  - User is created with `role='customer'`, `is_verified=FALSE`, `token_version=0`.
- **Success:** `201`
  ```json
  {
    "message": "Verification code sent",
    "user_id": 7,
    "email": "customer@example.com",
    "is_verified": false
  }
  ```
- **Client errors:**
  - `400` — invalid email, password < 8 chars, password > 72 bytes, unknown customer ID, customer/email mismatch, duplicate email.
  - `409` — email already registered (handled as 400 in this codebase).

### `POST /api/auth/verify`

- **Role:** public.
- **Purpose:** Verify the registration OTP and optionally link a customer record.
- **Request:**
  ```json
  {
    "email": "customer@example.com",
    "code": "123456",
    "customer_id": "C1001"
  }
  ```
- **Behavior:**
  - Finds the user by lowercased email.
  - Rejects unknown email, wrong code, expired OTP, already-verified user.
  - Tracked attempts: after 3 wrong tries, asks for a new code.
  - If `customer_id` is supplied, calls the customer link endpoint.
- **Success:** `200`
  ```json
  {
    "message": "Email verified",
    "user_id": 7,
    "is_verified": true
  }
  ```
- **Client errors:** `400` with `error` strings like `Invalid code`, `Code expired`, `Too many attempts - request a new code`.

### `POST /api/auth/resend-verification`

- **Role:** public.
- **Purpose:** Resend a verification OTP.
- **Request:**
  ```json
  { "email": "customer@example.com" }
  ```
- **Behavior:** If the user does not exist or is already verified, it still returns `200` (no enumeration). Otherwise it issues a new OTP and sends it.
- **Success:** `200`
  ```json
  { "message": "If the email needs verification, a new code was sent" }
  ```

### `POST /api/auth/login`

- **Role:** public.
- **Purpose:** Authenticate and get a JWT.
- **Request:**
  ```json
  { "email": "customer@example.com", "password": "SuperSecret123!" }
  ```
- **Behavior:**
  - Missing/invalid credentials return a generic `401`.
  - Unverified accounts are rejected with `401`.
  - On success, creates a JWT with `identity=user.id` and claims: `role`, `email`, `tv` (token version).
- **Success:** `200`
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "user": {
      "id": 7,
      "email": "customer@example.com",
      "full_name": "Jane Doe",
      "role": "customer",
      "is_verified": true,
      "customer_id": "C1001"
    }
  }
  ```
- **Client errors:** `400` for missing fields, `401` for invalid/expired or unverified credentials.

### `POST /api/auth/forgot-password`

- **Role:** public.
- **Purpose:** Request a password-reset link.
- **Request:**
  ```json
  { "email": "customer@example.com" }
  ```
- **Behavior:** If the user exists, a random reset token is created, hashed, and stored with a 1-hour expiry. The link is emailed (dev: logged).
- **Success:** `200`
  ```json
  { "message": "If the email exists, a reset link was sent" }
  ```
- **Client errors:** `400` if email is missing.

### `POST /api/auth/reset-password`

- **Role:** public (token is used as proof of ownership).
- **Purpose:** Reset the password using the reset token.
- **Request:**
  ```json
  { "token": "<reset_token>", "new_password": "NewSuperSecret123!" }
  ```
- **Behavior:**
  - Finds the user by the hashed token; rejects unknown/expired/unused tokens.
  - Validates the new password.
  - On success: replaces `password_hash`, clears reset/verification state, and increments `token_version` (old JWTs stop working).
- **Success:** `200`
  ```json
  { "message": "Password reset successful" }
  ```
- **Client errors:** `400` for missing token, invalid/expired token, or a password that fails validation.

### `GET /api/auth/me`

- **Role:** authenticated (`auth_required`).
- **Purpose:** Return the current user profile.
- **Success:** `200`
  ```json
  {
    "id": 7,
    "email": "customer@example.com",
    "full_name": "Jane Doe",
    "role": "customer",
    "is_verified": true,
    "customer_id": "C1001",
    "customer": {
      "customer_id": "C1001",
      "cust_name": "Jane Doe"
    }
  }
  ```
- **Client errors:** `401` for missing, malformed, or expired token.

---

## 2. Customer & catalog endpoints

### `GET /api/customers`

- **Role:** admin only.
- **Purpose:** List all customers.
- **Success:** `200`
  ```json
  {
    "customers": [
      { "customer_id": "C1001", "user_id": 7, "cust_name": "Jane Doe", "email": "customer@example.com" }
    ]
  }
  ```
- **Client errors:** `403` for non-admin.

### `POST /api/customers`

- **Role:** admin only.
- **Purpose:** Create a customer record.
- **Request:**
  ```json
  {
    "customer_id": "C1005",
    "cust_name": "New Customer",
    "email": "customer@example.com"
  }
  ```
- **Behavior:** `customer_id` is uppercased. `email` is lowercased or null.
- **Success:** `201`
  ```json
  {
    "customer": {
      "customer_id": "C1005",
      "user_id": null,
      "cust_name": "New Customer",
      "email": "customer@example.com"
    }
  }
  ```
- **Client errors:** `400` for missing `customer_id` or `cust_name`; `409` for duplicate customer ID.

### `PATCH /api/customers/<customer_id>/link`

- **Role:** admin only.
- **Purpose:** Link a customer record to a user account.
- **Request:**
  ```json
  { "user_id": 7 }
  ```
- **Behavior:**
  - Requires a valid `user_id`.
  - Rejects if the customer is already linked to another user.
  - On success: sets `cust.user_id`, copies `email` and `cust_name` from the user if empty.
- **Success:** `200`
  ```json
  {
    "message": "Customer linked successfully",
    "customer": {
      "customer_id": "C1001",
      "user_id": 7,
      "cust_name": "Jane Doe",
      "email": "customer@example.com"
    }
  }
  ```
- **Client errors:** `400`, `404`, `409`.

### `GET /api/products`

- **Role:** authenticated (any role).
- **Purpose:** Product catalog (used for dropdowns).
- **Success:** `200`
  ```json
  {
    "products": [
      {
        "product_id": 1,
        "pro_name": "Phone",
        "current_price": 150.0
      }
    ]
  }
  ```

### `POST /api/products`

- **Role:** admin only.
- **Purpose:** Create a product.
- **Request:**
  ```json
  {
    "pro_name": "USB-C Hub",
    "current_price": 49.99
  }
  ```
- **Success:** `201`
  ```json
  {
    "product": {
      "product_id": 5,
      "pro_name": "USB-C Hub",
      "current_price": 49.99
    }
  }
  ```
- **Client errors:** `400` if name or price is invalid; `409` if product name exists.

### `PATCH /api/products/<id>`

- **Role:** admin only.
- **Purpose:** Update a product’s price.
- **Request:**
  ```json
  { "current_price": 54.99 }
  ```
- **Success:** `200`
  ```json
  {
    "message": "Price updated",
    "product": {
      "product_id": 5,
      "pro_name": "USB-C Hub",
      "current_price": 54.99
    }
  }
  ```
- **Client errors:** `400` invalid price; `404` if missing.

### `DELETE /api/products/<id>`

- **Role:** admin only.
- **Purpose:** Delete a product.
- **Success:** `200`
  ```json
  { "message": "Product deleted" }
  ```
- **Client errors:** `404` if missing; `409` if the product is used in orders (requires archive instead).

---

## 3. Order endpoints (`/api/orders/*`)

### `POST /api/orders`

- **Role:** admin only.
- **Purpose:** Create an order with line items.
- **Request:**
  ```json
  {
    "order_id": "ORD1234",
    "customer_id": "C5678",
    "order_date": "2026-10-21",
    "items": [
      {
        "product_id": 1,
        "quantity": 2
      }
    ]
  }
  ```
- **Behavior:**
  - Server-side validations:
    - `order_id` must match `ORD####`.
    - `customer_id` must match `C####` and exist.
    - `items` is required, at least one item per order.
    - `quantity` must be an integer between 1 and 1000.
    - `product_id` must exist and have a price.
    - No duplicate product entries within the same order.
    - `order_status` is optional; default is `Pending`. If supplied, it must be a valid status.
  - The server **ignores** any `unit_price` the client sends.
  - It inserts order items using the server-side `products.current_price`.
  - The order is created as `Pending`.
  - If the order ID already exists → `409`.
- **Success:** `201`
  ```json
  {
    "order_id": "ORD1234",
    "customer_id": "C5678",
    "order_date": "2026-10-21",
    "order_status": "Pending",
    "total": 300.0,
    "item_count": 1,
    "items": [
      {
        "order_item_id": 12,
        "order_id": "ORD1234",
        "product_id": 1,
        "product_name": "Phone",
        "quantity": 2,
        "unit_price": 150.0,
        "line_total": 300.0
      }
    ],
    "customer": {
      "customer_id": "C5678",
      "cust_name": "John Smith",
      "email": "john@example.com",
      "user_id": 3
    }
  }
  ```
- **Client errors:** `400` with `errors` array; `409` if order ID exists.

### `GET /api/orders`

- **Role:** any authenticated user. Customers only see their own orders.
- **Purpose:** List orders with pagination, optional filters, and search.
- **Query parameters:**
  - `page` — default `1`
  - `per_page` — default `50`, max `200`
  - `status` — one of `Pending`, `Received`, `Shipped`, `Delivered`, `Cancelled`, `Returned`. Unknown value → `400`.
  - `customer_id` — customer/list view filter; non-admin filtering another customer → `403`.
  - `q` — search by `order_id`, `customer_id`, customer name, or email.
- **Success:** `200`
  ```json
  {
    "orders": [
      {
        "order_id": "ORD1234",
        "customer_id": "C5678",
        "order_date": "2026-10-21",
        "order_status": "Pending",
        "total": 300.0,
        "item_count": 1,
        "customer": {
          "customer_id": "C5678",
          "cust_name": "John Smith",
          "email": "john@example.com",
          "user_id": 3
        }
      }
    ],
    "page": 1,
    "per_page": 10,
    "total": 42,
    "pages": 5
  }
  ```
- **Client errors:** `400` invalid `status`; `403` customer trying to filter another customer’s orders.

### `GET /api/orders/<order_id>`

- **Role:** authenticated; owner or admin can view.
- **Purpose:** Get a single order with line items and calculated total.
- **Success:** `200`
  ```json
  {
    "order_id": "ORD1234",
    "customer_id": "C5678",
    "order_date": "2026-10-21",
    "order_status": "Delivered",
    "total": 999.0,
    "item_count": 3,
    "items": [
      {
        "order_item_id": 1,
        "order_id": "ORD1234",
        "product_id": 1,
        "product_name": "Phone",
        "quantity": 3,
        "unit_price": 150.0,
        "line_total": 450.0
      }
    ],
    "customer": {
      "customer_id": "C5678",
      "cust_name": "John Smith",
      "email": "john@example.com",
      "user_id": 3
    }
  }
  ```
- **Client errors:**
  - `401` — missing/invalid token.
  - `404` — order not found, or not owned by the caller (for customers; 404 prevents leaking other customers’ order IDs).

### `PATCH /api/orders/<order_id>/status`

- **Role:** admin only.
- **Purpose:** Update order status with strict state machine enforcement.
- **Request:**
  ```json
  { "order_status": "Shipped" }
  ```
- **Allowed transitions:**
  - `Pending` → `Received`, `Shipped`, `Cancelled`
  - `Received` → `Shipped`, `Cancelled`
  - `Shipped` → `Delivered`, `Returned`
  - `Delivered` → `Returned`
  - `Cancelled` / `Returned` → none
- **Success:** `200` — order JSON with the updated status.
- **Client errors:**
  - `400` — missing status or invalid transition.
  - `404` — order not found.

### `GET /api/orders/duplicates`

- **Role:** admin only.
- **Purpose:** Find duplicate order groups.
- **Group definition:** same `customer_id`, `product_id`, `quantity`, `unit_price`, and `order_date`.
- **Success:** `200`
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
- **Client errors:** `403` for non-admin.

---

## 4. Report endpoints (`/api/reports/*`)

All report endpoints are **admin only**.

### `GET /api/reports/summary`

- **Purpose:** Dashboard KPIs + breakdowns + latest orders + duplicate groups.
- **Behavior:** Revenue, sales orders, and units sold count only `Shipped` + `Delivered` orders. It uses `order_items.unit_price` (historical), not `products.current_price`.
- **Success:** `200`
  ```json
  {
    "revenue": 4567.89,
    "sales_orders": 10,
    "units_sold": 34,
    "awaiting_action": 5,
    "total_orders": 42,
    "status_breakdown": [
      { "status": "Delivered", "count": 10 },
      { "status": "Pending", "count": 8 }
    ],
    "latest_orders": [
      {
        "order_id": "ORD9001",
        "customer_id": "C5678",
        "order_date": "2026-10-21",
        "order_status": "Delivered",
        "total": 300.0
      }
    ],
    "duplicate_groups": [
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
    ],
    "product_breakdown": [
      { "product": "Phone", "items": 20, "units": 60, "revenue": 9000.0 }
    ],
    "monthly_breakdown": [
      { "period": "2026-10", "orders": 3, "units": 9, "revenue": 144.0 }
    ]
  }
  ```

### `GET /api/reports/product-wise`

- **Purpose:** Product-wise sales report.
- **Query parameters:**
  - `format=csv` → returns CSV.
- **JSON success:** `200`
  ```json
  [
    { "product": "Phone", "items": 20, "units": 60, "revenue": 9000.0 }
  ]
  ```
- **CSV success:**
  - Content-Type: `text/csv`
  - `Content-Disposition: attachment; filename=product_wise_report.csv`
  - Header: `Product, Items Sold, Units Sold, Revenue (INR)`
  - Rows: `Phone, 20, 60, 9000.00`

### `GET /api/reports/date-wise`

- **Purpose:** Date-wise / monthly sales report.
- **Query parameters:**
  - `group` — `day` (default) or `month`.
  - `format=csv` → returns CSV.
- **JSON success:** `200`
  ```json
  [
    {
      "period": "2026-10",
      "orders": 3,
      "units": 9,
      "revenue": 144.0
    }
  ]
  ```
- **CSV success:**
  - Header: `Period (month), Orders, Units Sold, Revenue (INR)`
  - Rows: `2026-10, 3, 9, 144.00`

---

## 5. Users endpoints (`/api/users/*`)

All user endpoints are **admin only**.

### `GET /api/users`

- **Purpose:** List users.
- **Success:** `200`
  ```json
  {
    "users": [
      {
        "id": 7,
        "email": "admin@example.com",
        "full_name": "Admin User",
        "role": "admin",
        "is_verified": true,
        "customer_id": "C2001"
      }
    ]
  }
  ```

### `POST /api/users`

- **Purpose:** Create a user account.
- **Request:**
  ```json
  {
    "email": "newadmin@example.com",
    "password": "SuperSecret123!",
    "full_name": "New Admin",
    "role": "admin"
  }
  ```
- **Behavior:** Email is lowercased. `role` defaults to `customer`. Password is hashed with bcrypt. The new user is marked verified.
- **Success:** `201`
  ```json
  {
    "user": {
      "id": 8,
      "email": "newadmin@example.com",
      "full_name": "New Admin",
      "role": "admin",
      "is_verified": true,
      "customer_id": null
    }
  }
  ```
- **Client errors:** `400` for missing email/password; `409` for duplicate email.

### `PATCH /api/users/<id>/role`

- **Purpose:** Change a user’s role.
- **Request:**
  ```json
  { "role": "customer" }
  ```
- **Behavior:** Prevents demoting the last remaining admin.
- **Success:** `200`
  ```json
  {
    "message": "Role updated",
    "user": {
      "id": 8,
      "email": "newadmin@example.com",
      "full_name": "New Admin",
      "role": "customer",
      "is_verified": true,
      "customer_id": null
    }
  }
  ```
- **Client errors:** `400` for invalid role or last-admin rule; `404` if missing.

### `DELETE /api/users/<id>`

- **Purpose:** Delete a user.
- **Behavior:** Blocks self-deletion. Blocks deleting the last remaining admin. Unlinks the customer record before deleting.
- **Success:** `200`
  ```json
  { "message": "User deleted" }
  ```
- **Client errors:** `400` for self-delete or last-admin rule; `404` if missing.

---

## 6. Health and root

### `GET /health`

- **Purpose:** Liveness probe.
- **Success:** `200`
  ```json
  { "status": "ok" }
  ```

### `GET /`

- **Purpose:** Root endpoint.
- **Success:** `200`
  ```json
  { "status": "ok" }
  ```

---

## 7. Full endpoint table

| # | Method | Path | Auth | Description |
|---|--------|------|------|-------------|
| 1 | POST | `/api/auth/register` | public | Register a customer account |
| 2 | POST | `/api/auth/verify` | public | Verify email OTP + link customer |
| 3 | POST | `/api/auth/resend-verification` | public | Resend OTP |
| 4 | POST | `/api/auth/login` | public | Get JWT |
| 5 | POST | `/api/auth/forgot-password` | public | Request reset link |
| 6 | POST | `/api/auth/reset-password` | public | Reset password with token |
| 7 | GET | `/api/auth/me` | auth | Current user |
| 8 | GET | `/api/customers` | admin | List customers |
| 9 | POST | `/api/customers` | admin | Create customer |
| 10 | PATCH | `/api/customers/<id>/link` | admin | Link customer to user |
| 11 | GET | `/api/products` | auth | List products |
| 12 | POST | `/api/products` | admin | Create product |
| 13 | PATCH | `/api/products/<id>` | admin | Update product price |
| 14 | DELETE | `/api/products/<id>` | admin | Delete product |
| 15 | POST | `/api/orders` | admin | Create order |
| 16 | GET | `/api/orders` | auth | List orders (owner/admin) |
| 17 | GET | `/api/orders/<id>` | auth | Order detail |
| 18 | PATCH | `/api/orders/<id>/status` | admin | Change status |
| 19 | GET | `/api/orders/duplicates` | admin | Find duplicates |
| 20 | GET | `/api/reports/summary` | admin | Dashboard summary |
| 21 | GET | `/api/reports/product-wise` | admin | Product sales |
| 22 | GET | `/api/reports/date-wise` | admin | Date/month sales |
| 23 | GET | `/api/users` | admin | List users |
| 24 | POST | `/api/users` | admin | Create user |
| 25 | PATCH | `/api/users/<id>/role` | admin | Change role |
| 26 | DELETE | `/api/users/<id>` | admin | Delete user |
| 27 | GET | `/health` | public | Liveness probe |
| 28 | GET | `/` | public | Root endpoint |

---

## 8. Global request/response rules

- **Auth header:** `Authorization: Bearer <JWT>`.
- **Status codes:**
  - `200` — successful retrieval or update.
  - `201` — resource created.
  - `400` — client error, with `error` or `errors` array.
  - `401` — missing, invalid, or expired token, or unverified account.
  - `403` — authenticated but not allowed (wrong role, forbidden resource).
  - `404` — resource missing, or (for customers) not owned by them.
  - `409` — conflict: duplicate ID/email, idempotency conflict.
  - `500` — unexpected error, without internals.
- **All endpoints return JSON,** unless a report returns CSV (`format=csv`).
- **Password/token handling:** passwords and tokens are hashed with bcrypt/SHA-256; raw values never appear in responses.
- **Pricing rule:** clients may not set order prices. The server uses `products.current_price` for every order item.
- **Status rule:** only legal transitions are accepted; the frontend mirrors the same machine.

---

## 9. Where each endpoint lives in the code

| Endpoint(s) | Route file | Service called |
|-------------|------------|----------------|
| `/api/auth/*` | `app/routes/auth.py` | `app/services/auth_service.py` |
| `/api/customers/*`, `/api/products/*` | `app/routes/customers.py`, `app/routes/products.py` | `Customer`, `Product` models |
| `/api/orders/*`, `/api/orders/duplicates` | `app/routes/orders.py` | `app/services/order_service.py` |
| `/api/reports/*` | `app/routes/reports.py` | `app/services/order_service.py` report functions |
| `/api/users/*` | `app/routes/users.py` | `User` model / DB session |

---

## 10. Example flows

### Register flow

```
POST /api/auth/register
{ email, password, full_name, customer_id }
  -> 201 { message, user_id, email, is_verified: false }

POST /api/auth/verify
{ email, code, customer_id }
  -> 200 { message, user_id, is_verified: true }

POST /api/auth/login
{ email, password }
  -> 200 { access_token, user }
```

### Admin create order flow

```
POST /api/auth/login  (admin)
POST /api/orders
{
  "order_id": "ORD1234",
  "customer_id": "C5678",
  "order_date": "2026-10-21",
  "items": [{ "product_id": 1, "quantity": 2 }]
}
  -> 201 { order_id, items, total, ... }
```

### Customer status update flow

```
GET /api/orders/ORD1234
  -> 200 (customer can only see own orders; others are 404)

PATCH /api/orders/ORD1234/status
{ "order_status": "Shipped" }
  -> 200 (admin only; customer gets 403)
```

---

## 11. Authentication primer (frontend perspective)

- The frontend `api.js` intercepts every request and adds:
  ```js
  Authorization: Bearer <token>
  ```
- On `401` or `422`, `api.js` clears localStorage credentials and redirects to `/login`.
- `auth.js` store stores:
  - `token` — the JWT.
  - `user` — parsed user object.
- `AppLayout.vue` calls `auth.fetchMe()` on load to refresh the user.
- The backend does **not** trust the token’s role claim; it reloads the role from the DB (`token_version` in the JWT helps protect against role/revocation attacks).

---

## 12. Error format

- Generic error: `{ "error": "..." }`
- Validation error: `{ "errors": ["order_id must match ORD####", ...] }`
- DB failure: `{ "error": "Failed to create order" }` (generic, no internals).
- Password/role failures: `{ "error": "Invalid password"`, `{ "error": "Cannot demote the last remaining admin" }`, etc.

---

## 13. Test coverage for these endpoints

Relevant pytest files:

- `server/app/tests/test_auth.py` — register/verify/login/reset, OTP, tokens, expiry, duplicate emails.
- `server/app/tests/test_orders.py` — create, validation, status transitions, pagination, duplicate detection.
- `server/app/tests/test_permissions.py` — RBAC, customer isolation, ownership, token revocation.
- `server/app/tests/test_pricing.py` — server-side price enforcement.
- `server/app/tests/test_reports.py` — report accuracy.
- `server/app/tests/test_smoke.py` — fixture/sample load checks.

Run from `Order_Sales_Management/server`:
```powershell
. ../../.venv/Scripts/activate
python -m pytest tests/ -v
```
Result verified: **82 passed**.
