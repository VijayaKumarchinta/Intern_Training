# Backend Files Explained — OrderSalesManagement (OrderSync)

All paths are relative to `Order_Sales_Management/server/app/`. The Flask app factory is created by `server/run.py` with `from app import create_app`. Tests live under `server/tests/` and are run with `pytest`.

---

## 1. `app/__init__.py` — app factory

- **`create_app()`** — builds the Flask application once and wires everything together.
  - Creates the Flask app.
  - Loads settings from `app/config.py` (`app.config.from_object(Config)`).
  - Calls `configure_logging(app)` to set up console and rotating file logging (`logs/app.log`).
  - Initializes the three shared extensions: `db`, `jwt`, `mail`.
  - Registers JWT error handlers:
    - `invalid_token` → `401`
    - `unauthorized_loader` → `401`
    - `expired_token` → `401`
  - Lazily imports and registers the blueprints:
    - `auth_bp` — `/api/auth`
    - `orders_bp` — `/api/orders`
    - `reports_bp` — `/api/reports`
    - `products_bp` — `/api/products`
    - `customers_bp` — `/api/customers`
    - `users_bp` — `/api/users`
  - Adds root routes:
    - `GET /` → `{ status: "ok" }`
    - `GET /health` → `{ status: "ok" }`
- **Role:** the single place that creates and configures the app, wires extensions and blueprints, and hosts the liveness/root routes.

---

## 2. `app/config.py` — configuration

- `BASE_DIR` — points to the project root (parent of `server/`).
- `configure_logging(app)`:
  - Creates `logs/` if missing.
  - Adds a console handler and a rotating file handler (`5 MB`, `3` backups).
  - Sets a readable log format: `%(asctime)s | %(levelname)-7s | %(name)s | %(message)s`.
  - Reduces noise from SQLAlchemy engine/pool and Werkzeug while keeping important app logs.
  - Logs `Server ready` when the reloader starts the process.
- `class Config:` — reads environment variables:
  - `DATABASE_URL` — required; raises `RuntimeError` if missing.
  - `SECRET_KEY` / `JWT_SECRET_KEY` — required.
  - `SQLALCHEMY_DATABASE_URI`, `SQLALCHEMY_TRACK_MODIFICATIONS = False`.
  - `SQLALCHEMY_ENGINE_OPTIONS`:
    - Connection pooling: `pool_pre_ping=True`, `pool_size=5`, `max_overflow=10`.
    - Sets `search_path` from `DB_SCHEMA`, default `order_sales`.
  - `JWT_ACCESS_TOKEN_EXPIRES` — computed from `JWT_ACCESS_TOKEN_EXPIRES_HOURS` (seconds).
  - Mail config: `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_USE_TLS`.
  - Auth TTLs: `VERIFY_TTL_MINUTES`, `VERIFY_MAX_ATTEMPTS`, `RESET_TTL_HOURS`.
- **Role:** single source for Flask config; `.env` / `.env.test` are loaded before the app is created.

---

## 3. `app/constants.py` — role constants

- `class Role(str, Enum):`
  - `ADMIN = "admin"`
  - `CUSTOMER = "customer"`
- `Role.values()` → `{ "admin", "customer" }`.
- `Role.is_valid(value)` → checks membership.
- **Role:** single source of truth for role strings used in decorators, guards, and validation. Using an enum avoids duplicate `\"admin\"` / `\"customer\"` strings scattered across routes.

---

## 4. `app/extensions.py` — shared singletons

- `db = SQLAlchemy()` — ORM engine, session, and model registry.
- `jwt = JWTManager()` — Flask-JWT-Extended integration for login, token verification, and custom JWT error handlers.
- `mail = Mail()` — Flask-Mail configured later in `config.py`; used by `app/utils/email.py`.
- **`hash_password(plain)`**:
  - Type-checks that input is a string.
  - Returns `bcrypt.hashpw(...).decode("utf-8")`.
- **`verify_password(plain, hashed)`**:
  - Returns `False` for empty inputs.
  - Uses `bcrypt.checkpw` and catches `ValueError`/`TypeError` to avoid leaking errors.
- **Role:** reusable, dependency-free helpers shared by routes and services.

---

## 5. `app/models.py` — SQLAlchemy models

### `User`

- Table `users`.
- Columns:
  - `id` — integer primary key.
  - `email` — `String(255)`, not null, case-insensitive unique in DB (`LOWER(email)`).
  - `password_hash` — `String(255)`, not null.
  - `full_name` — `String(255)`.
  - `role` — `String(20)`, default `customer`; DB check constraint restricts to `admin` / `customer`.
  - `is_verified` — `Boolean`, default `False`.
  - `verification_token_hash`, `verification_expires_at`, `verification_attempts` — email verification state.
  - `reset_token_hash`, `reset_token_expires_at` — password reset state.
  - `token_version` — integer, default `0`; used by JWT revocation.
  - `created_at` / `updated_at` — UTC timestamps; `updated_at` updates automatically.
- `to_dict()` — returns clean JSON-safe fields: `id`, `email`, `full_name`, `role`, `is_verified`, `customer_id`.
- Relationship: `customer` → `Customer` (`uselist=False`), meaning a user can be linked to one customer.

### `Customer`

- Table `customers`.
- Columns:
  - `customer_id` — `String(20)`, primary key.
  - `user_id` — integer FK to `users.id`, `ON DELETE SET NULL`, unique. At most one user can link to a customer.
  - `cust_name`, `email` — optional profile fields.
  - `created_at` — UTC timestamp.
- `to_dict()` → `{ customer_id, user_id, cust_name, email }`.
- Relationship: `orders` → `Order` (lazy select).

### `Product`

- Table `products`.
- Columns:
  - `product_id` — integer primary key.
  - `pro_name` — `String(100)`, unique, not null.
  - `current_price` — `Numeric(12,2)`.
- `to_dict()` returns `product_id`, `pro_name`, and `current_price` (float or null).
- Relationship: `order_items`.

### `Order`

- Table `orders`.
- Columns:
  - `order_id` — `String(20)`, primary key.
  - `customer_id` — FK to `customers.customer_id`, not null.
  - `order_date` — `Date`.
  - `order_status` — `String(20)`, default `Pending`; DB check constraint restricts to valid statuses.
  - `created_at` / `updated_at` — UTC timestamps.
- `to_dict(include_items=False)` → order fields; when `include_items=True`, also includes line items.
- Relationship: `items` → `OrderItem` (ordered by ID).

### `OrderItem`

- Table `order_items`.
- Columns:
  - `order_item_id` — integer primary key.
  - `order_id` — FK to `orders.order_id`, `ON DELETE CASCADE`.
  - `product_id` — FK to `products.product_id`.
  - `quantity` — integer, not null, DB check `quantity > 0`.
  - `unit_price` — `Numeric(12,2)`, not null, DB check `unit_price >= 0`.
  - Unique `(order_id, product_id)` — a product can appear only once per order.
- `to_dict()` returns `order_item_id`, `order_id`, `product_id`, `product_name`, `quantity`, `unit_price`, `line_total`.
- **Role:** defines the data model and JSON serialization only. Business rules live in `services/`.

---

## 6. `app/utils/decorators.py` — auth and authorization

- **`_load_user(uid)`** — loads a user by integer ID; returns `None` on missing/bad input.
- **`_resolve_request_user()`** — used after JWT is required:
  - Reads `get_jwt_identity()` and loads the real user from the DB.
  - Checks `get_jwt()["tv"]` against `user.token_version`. A mismatch means the token is invalid → `401`.
  - Returns `(user, None)` or `(None, (jsonify(response), 401))`.
- **`auth_required(fn)`** — decorator:
  - Forces `@jwt_required()` first.
  - Calls `_resolve_request_user()`.
  - On success sets `g.current_user` for the route to read.
- **`role_required(required_role)`** — decorator factory:
  - Forces JWT, then checks `user.role == required_role`.
  - On failure returns `403` (`"Forbidden"`).
  - On success sets `g.current_user`.
- **Role:** DRY, centralized auth and RBAC for all routes.

---

## 7. `app/utils/permissions.py` — ownership helpers

- `is_admin(user)` — True when role is `admin`.
- `is_customer(user)` — True when role is `customer`.
- `owns_customer(user, customer_id)` — True when the user is logged in and linked to the given customer.
- `can_view_order(user, order)`:
  - Admins can always view.
  - Customers can only view orders whose `customer.user_id` matches their own ID.
- **Role:** used by `orders.py` to return `404` instead of `403` when a customer requests another customer’s order (avoids leaking order IDs).

---

## 8. `app/utils/email.py` — development email simulation

- `DEV_EMAIL_LOG` — points to `server/logs/dev_emails.log`.
- `_write_dev_email_log(kind, email, payload)` — appends a timestamped line.
- `send_verification_code(email, code)` — logs `VERIFY-OTP` with TTL.
- `send_password_reset(email, token)` — builds the reset link:
  ```text
  FRONTEND_URL/reset-password?token=<token>
  ```
  and logs `RESET-LINK`.
- **Role:** a development-only sender. Production should replace it with a real email provider. The backend never blocks on SMTP: it logs in dev and shows the code/link in `dev_emails.log`.

---

## 9. `app/utils/validators.py` — input validation

- `normalize_email(email)` — trims and lowercases.
- `validate_password(password)`:
  - Returns a message when empty, shorter than 8 characters, or longer than 72 bytes.
- `validate_email(email)`:
  - Returns a message when empty or missing `@`.
- **Role:** used by `auth_service.py` as the single source for account-input validation.

---

## 10. `app/services/__init__.py`

- Empty package marker; no logic.

---

## 11. `app/services/auth_service.py` — authentication business logic

- `_now()` — UTC timestamp.
- `_hash(value)` — SHA-256 hex digest (used for OTP and reset tokens; never the raw value).
- `_new_otp()` — 6-digit zero-padded OTP using `secrets`.
- `_new_reset_token()` — `secrets.token_urlsafe(32)` for reset tokens.
- `_verify_ttl_minutes()`, `_verify_max_attempts()`, `_reset_ttl_hours()` — config-driven values.

### `register(email, password, full_name, customer_id)`

- Normalizes email and trims strings.
- Validates email and password.
- Rejects missing customer ID.
- Rejects duplicate email (case-insensitive).
- Rejects unknown customer ID.
- Rejects when the customer record’s email does not match the given email.
- Creates a `User`:
  - `role='customer'`
  - `is_verified=False`
  - `token_version=0`
  - Hashed password.
  - OTP hash and 2-minute expiry.
- Returns `(user, None)` or `(None, error)`.

### `verify_email(email, code)`

- Finds the user by lowercased email.
- Rejects:
  - Unknown email → `"Invalid code"`
  - Already verified
  - Missing token or expired token
  - Too many attempts (returns remaining attempts).
- On success: clears `verification_token_hash`, `verification_expires_at`, and `verification_attempts`, sets `is_verified=True`.

### `resend_verification_code(email)`

- Returns `(True, None)` for unknown or already-verified users (no email enumeration).
- Otherwise issues a new OTP with a fresh expiry and sends it.

### `link_customer(user, customer_id)`

- Requires a verified user.
- Rejects unknown customer or email mismatch.
- On success:
  - Sets `cust.user_id = user.id`
  - Copies `email` and `cust_name` from the user if empty
- Returns `(True, None)` or `(False, error)`.

### `login(email, password)`

- Finds the user by lowercased email.
- Rejects:
  - Missing/invalid credentials → `"Invalid credentials"`
  - Unverified account → `"Please verify your email first"`
- On success: creates a JWT with `identity=str(user.id)` and claims `role`, `email`, `tv`.

### `forgot_password(email)`

- If the user exists, hashes a new reset token and sets a 1-hour expiry.
- Always returns `(True, None)` for both known and unknown emails.

### `reset_password(token, new_password)`

- Finds user by hashed token; rejects unknown/inactive/expired tokens.
- Validates the new password.
- On success:
  - Replaces `password_hash`
  - Clears `reset_token_hash`, `reset_token_expires_at`, `verification_token_hash`, `verification_expires_at`, `verification_attempts`
  - Increments `token_version` (invalidates old JWTs)

- **Role:** all identity and password logic lives here. No HTTP, no Flask route imports.

---

## 12. `app/services/order_service.py` — order business logic

- `VALID_STATUSES` — allowed statuses.
- `ALLOWED_TRANSITIONS` — exact state machine:
  - `Pending` → `Received`, `Shipped`, `Cancelled`
  - `Received` → `Shipped`, `Cancelled`
  - `Shipped` → `Delivered`, `Returned`
  - `Delivered` → `Returned`
  - `Cancelled` / `Returned` → none
- `SALE_STATUSES` — `{ Shipped, Delivered }`; only these count toward revenue.

### `validate_order_payload(payload)`

Returns a list of errors:

- `order_id` must match `ORD####`.
- `order_date` must be parseable as `YYYY-MM-DD`.
- `customer_id` must match `C####` and exist.
- At least one item required.
- Each `product_id` must exist, have a price, and not repeat in the same order.
- Each `quantity` must be an integer between 1 and 1000.
- Optional `order_status` must be in `VALID_STATUSES`.

### `create_order(payload)`

- Runs validation; returns `(None, errors, 400)` if invalid.
- Rejects duplicate `order_id` (`409`).
- Creates the order as `Pending`.
- Inserts `order_items` using `product.current_price` (server-side pricing).
- Commits in a transaction; rolls back and re-raises unexpected errors.
- Returns `(order, None, 201)`.

### `visible_orders_for(user)`

- Admin → all orders.
- Customer → orders joined to customers where `customer.user_id == user.id`.
- None/unknown user → empty query.
- **Role:** enforces per-customer order visibility.

### `can_transition(old_status, new_status)`

- Validates statuses and checks `ALLOWED_TRANSITIONS`.

### `change_status(order, new_status)`

- Returns `(False, message)` for an illegal transition.
- On success, updates `order_status`, commits, returns `(True, None)`.

### `product_wise_report()`

- Joins `order_items` and `orders`, filters `Shipped` + `Delivered`.
- Groups by product:
  - `items` — count of order items
  - `units` — sum of quantity
  - `revenue` — sum of `quantity * unit_price`
- Ordered by revenue descending.

### `date_wise_report(group='day')`

- Bucket:
  - `month` → `date_trunc('month', order_date)`
  - `day` → `order_date`
- Groups by bucket, counts distinct orders, sums units and revenue.

### `find_duplicates()`

- Joins orders, order items, and products.
- Groups by:
  - `customer_id`, `product_id`, `quantity`, `unit_price`, `order_date`
- Returns only groups with `occurrences > 1`.
- Each result includes `customer_id`, `product_id`, `product_name`, `quantity`, `unit_price`, `order_date`, `occurrences`, `order_ids`.

### `get_dashboard_summary()`

- Computes:
  - `revenue`, `sales_orders`, `units_sold` — Shipped + Delivered only
  - `awaiting_action` — Pending + Received
  - `total_orders` — all orders
- Fetches:
  - `latest_orders` (top 6, with `order_id`, `customer_id`, `order_date`, `order_status`, `total`)
  - `duplicate_groups` (top 3 from `find_duplicates()`)
  - `product_breakdown`
  - `monthly_breakdown`
  - `status_breakdown`
- Returns the flat dict consumed by the summary endpoint.

- **Role:** all order/catalog/report business logic here, with no HTTP code.

---

## 13. `app/routes/__init__.py`

- Empty package marker.

---

## 14. `app/routes/auth.py` — auth HTTP layer

- `auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')`
- `_json()` — safe JSON request parser.
- `register_route()` → `register()`; returns `201`, or `400` with `error`.
- `verify_route()` → `verify_email()`; returns `200`, or `400`/`409` on link failure.
- `resend_route()` → `resend_verification_code()`; generic `200`.
- `login_route()` → `login()`; returns `access_token` and user, or `401`.
- `forgot_route()` → `forgot_password()`; generic `200`.
- `reset_route()` → `reset_password()`; `200`/`400`.
- `me_route()` → `auth_required`; returns full user profile + linked customer info.
- **Role:** thin HTTP controller. All business logic is in `auth_service`.

---

## 15. `app/routes/customers.py` — customer HTTP layer

- `customers_bp = Blueprint('customers', __name__, url_prefix='/api/customers')`.
- `list_customers()`:
  - Admin only; returns `{ customers: [...] }`.
- `create_customer()`:
  - Admin only; uppercases `customer_id`, lowercases `email`.
  - Returns `201`, or `400` for missing fields, `409` for duplicate ID.
- `link_customer_route(<customer_id>)`:
  - Admin only; validates user and link rules.
  - Copies `email` / `cust_name` from the user if empty.
  - Returns `200`, or `400/404/409`.
- **Role:** thin HTTP layer over `Customer` and the DB session.

---

## 16. `app/routes/orders.py` — order HTTP layer

- `orders_bp = Blueprint('orders', __name__, url_prefix='/api/orders')`.
- `g.current_user` is set by `auth_required` / `role_required`.
- `_json()` — safe JSON body parser.
- `_order_response(order, include_items)` — builds JSON with items, computed `total`, and `customer` info.
- `list_duplicates()` → admin only → `{ duplicates: find_duplicates() }`.
- `list_orders()`:
  - Requires auth; `visible_orders_for(user)` scopes admin/customer results.
  - Validates `status`, `customer_id`, and `q` search.
  - Paginates with Flask-SQLAlchemy: `page=1` default, `per_page=50` default, capped at 200.
  - Returns `{ orders, page, per_page, total, pages }`.
- `get_order(order_id)`:
  - Auth required; 404 if missing or if the customer requests another customer’s order.
- `create_order()`:
  - Admin only; calls `create_order_service()`.
  - Catches `IntegrityError` → `409`; generic DB errors → `400`.
  - Returns validation errors or the created order JSON.
- `update_status(order_id)`:
  - Admin only; `400` for missing status, `404` for missing order, `400` for invalid transition.
- **Role:** thin HTTP layer over `order_service`.

---

## 17. `app/routes/products.py` — product HTTP layer

- `products_bp = Blueprint('products', __name__, url_prefix='/api/products')`.
- `list_products()` → auth required; returns product list.
- `create_product()` → admin only; enforces unique name and non-negative price.
- `update_product_price(<id>)` → admin only; rejects invalid prices.
- `delete_product(<id>)` → admin only; rejects deletion while the product is used in orders (`409`).
- **Role:** thin HTTP layer over `Product` and DB session.

---

## 18. `app/routes/reports.py` — report HTTP layer

- `reports_bp = Blueprint('reports', __name__, url_prefix='/api/reports')`.
- `dashboard_summary()` → admin only → `get_dashboard_summary()`.
- `product_wise()` → admin only; JSON or CSV (`format=csv`).
- `date_wise()` → admin only; `group=day|month`, JSON or CSV; returns `400` for invalid group.
- `_generate_product_csv(data)`:
  - CSV header: `Product, Items Sold, Units Sold, Revenue (INR)`
- `_generate_date_csv(data, group)`:
  - CSV header: `Period (<group>), Orders, Units Sold, Revenue (INR)`
  - Returns `Response` with `Content-Disposition` for download.
- **Role:** thin HTTP layer that converts service report data to JSON or CSV.

---

## 19. `app/routes/users.py` — users HTTP layer

- `users_bp = Blueprint('users', __name__, url_prefix='/api/users')`.
- `list_users()` → admin only → `{ users: [...] }`.
- `create_user()`:
  - Admin only; lowercases email, enforces password, defaults `role='customer'`.
  - Returns `201` with the new user, or `400`/`409`.
- `update_user_role(<id>)`:
  - Admin only; validates role; prevents demoting the last admin (`400`).
- `delete_user(<id>)`:
  - Admin only; blocks self-delete and last-admin deletion.
  - Unsets the linked customer’s `user_id` before deletion.
  - Returns `200`/`400`/`404`.
- **Role:** thin HTTP layer; business controls live in this module (self-delete, last-admin, customer unsets).

---

## 20. `app/__init__.py` — app factory

- Already described in section 1.

---

## 21. `app/config.py`

- Already described in section 2.

---

## 22. `app/constants.py`

- Already described in section 3.

---

## 23. `app/extensions.py`

- Already described in section 4.

---

## 24. `app/models.py`

- Already described in section 5.

---

## 25. `app/utils/decorators.py`, `permissions.py`, `email.py`, `validators.py`

- Already described in sections 6–9.

---

## 26. `app/services/auth_service.py`, `order_service.py`

- Already described in sections 11 and 12.

---

## 27. `tests/conftest.py` — test fixtures and DB plumbing

- Forces `FLASK_ENV=test` before importing app.
- App fixture: `create_app()` with `TESTING=True`.
- Session-scoped autouse fixture seeds products once per session.
- Autouse per-test fixture truncates `order_sales.order_items`, `orders`, `customers`, `users` (with `RESTART IDENTITY CASCADE`); products survive.
- `sample_product` returns the seeded product.
- `_make_user(...)` creates users plus linked customers with `customer_id`.
- `_login(client, email, password)` helper.
- Fixtures: `admin_user`, `customer_user`, `other_customer`, `sample_order`, `other_customer_order`, plus token/headers.

---

## 28. `tests/test_auth.py`

Covers registration, OTP verification, login, password reset, and the loyalty-card ownership model:

- Registration with/without `customer_id`, email/cust mismatch, unknown customer, already-linked.
- OTP attempts, expiry, wrong code.
- Unverified login, generic 401.
- Forgot/reset token lifecycle and `token_version` bump.

---

## 29. `tests/test_orders.py`

Covers order creation, validation, status transitions, pagination, and duplicates.

- Admin create with/without client price, forbidden values, duplicate product, duplicate `order_id`.
- Status machine: valid flow, terminal-state lock, invalid transition.
- List filters, pagination, status filter, search.
- Duplicate detection endpoint.

---

## 30. `tests/test_permissions.py`

RBAC regression tests:

- Health/root public, auth required, malformed tokens.
- Customer blocked from reports, duplicates, order creation, status updates.
- Admin can access reports and duplicates.
- Customer-only order visibility; customer `customer_id` filter rules.
- Order `404` vs `200` for owner vs other customer.
- Token version bump revokes tokens; new login works.
- Role cannot be forged via JWT.
- Deleted user token returns `401`.

---

## 31. `tests/test_pricing.py`

Server-side pricing enforcement:

- Creates an order with a client `unit_price` and asserts the stored item price equals `products.current_price`.
- Order without `unit_price` succeeds.
- Wildly inflated `unit_price` is ignored.

---

## 32. `tests/test_reports.py`

Report accuracy:

- Only Shipped/Delivered count toward revenue; assertions for `units_sold`, `sales_orders`, `product_breakdown`.
- Summary contains all sections: KPIs, latest orders, duplicate groups, product and monthly breakdowns.
- Empty DB returns zeros and empty arrays.

---

## 33. `tests/test_smoke.py`

- Plumbing checks: fixtures, admin/customer headers, seeded product.
- App uses the test database (`order_sales_test_db`).

---

# Backend summary

## Layers

| Layer | Files | Purpose |
|-------|-------|---------|
| App factory / config | `__init__.py`, `config.py` | App creation, DB/JWT/Mail init, logging, env config |
| Extensions | `extensions.py` | `db`, `jwt`, `mail`, password helpers |
| Models | `models.py` | `User`, `Customer`, `Product`, `Order`, `OrderItem` |
| Auth rules | `constants.py`, `decorators.py`, `permissions.py`, `validators.py`, `email.py` | Roles, JWT/role checks, ownership, input validation, dev email |
| Business logic | `services/auth_service.py`, `services/order_service.py` | Accounts, verification, reset, order creation, status machine, reports |
| HTTP | `routes/*.py` | Thin controllers that parse requests, call services, return JSON |
| Tests | `tests/*.py` | pytest coverage for auth, permissions, pricing, reports, orders, smoke |

## Key design decisions

- **Single source of truth:** `constants.Role` replaces string literals like `\"admin\"` / `\"customer\"` across routes, decorators, and tests.
- **Auth:** JWTs only carry `user.id` plus a `token_version` claim; roles and name/email are reloaded from the DB per request.
- **Ownership:** customer routes show only orders whose `customers.user_id` matches the caller; cross-tenant access returns `404`, not `403`, to avoid order-ID leakage.
- **Pricing:** `products.current_price` is the server-side price; client-sent prices are ignored in order creation.
- **Status machine:** `ALLOWED_TRANSITIONS` is enforced in `order_service` and mirrored in the frontend.
- **Reports:** revenue counts only `Shipped` + `Delivered`, using historic `order_items.unit_price`.

---

# Backend verification

- Backend dependency resolution: passed.
- Test suite:
  ```powershell
  cd Order_Sales_Management/server
  python -m pytest tests/ -q
  ```
- Result verified: **84 passed**
