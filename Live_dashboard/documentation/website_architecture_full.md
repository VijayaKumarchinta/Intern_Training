# Full Architecture of the web app what is created

## Phase-0 - Prerequisites

Before running anything, make sure you have:

- PostgreSQL 14+ to store the database.
- Python 3.11+ to run the backend.
- Node.js 18+ to run/build the frontend.

## Phase-1 - DB configuration (db/init.sql)

Set up the database with proper credentials and schema first:

1. Confirm the correct database is connected.
2. Create the schema `order_sales` if missing.
3. Create the tables:

- `user` - stores users with hashed passwords, verified status, and tokens.
- `customers` - stores customer details, referenced from `user_id`.
- `products` - stores products separately with unit prices.
- `orders` - stores order details, referenced from `customer_id`.
- `order_items` - stores inline order items, referenced from `order_id` and
  `product_id`, with cascade on `order_id`.

4. Add indexes:

- `orders` indexes on `customer_id`, `order_date`, and `order_status` for fast
  fetching.

5. Add triggers:

- Automatically update `users` and `orders` registered and login times.

6. Add constraints for `order_status`.

After designing, initialize the DB with:

```psql -U postgres -f db/init.sql
```

## Phase-2 - Backend configuration (server/.env)

The config class in `app` reads this file via the `dotenv` module so the
correct database can be connected.

File path: `server/app/config`.

## Phase-3 - First admin bootstrap (server/manage.py)

Create the admin by running:

```flask --app manage create-admin
```

This inserts a user with role `admin`, `is_verified` as true, and
`token_version=0`.

## Phase-4 - Importing of the data (db/load_data.py)

```python db/load_data.py --csv data/Online_Store_Orders.csv --dry-run
```

The pipeline:

1. Reads a CSV file containing columns.
2. Aborts if any column is missing.
3. Parses into rows.
4. Can create customers and products later if needed.
5. Can insert items and orders through the frontend later.

## Phase-5 - Backend process starts (server/run.py)

```python server/run.py
```

Flow:

```text
create_app()
  -> Load credentials
  -> Validate environment
  -> Configure logging (logs/app.log)
  -> Initialize extensions:
       - DB
       - JWT
       - Email
       - Password Hashing
  -> Register JWT error handlers:
       - Invalid, Missing, Expired Token -> 401
  -> Register Blueprints:
       - Auth
       - Orders
       - Customers
       - Products
       - Users
       - Reports
  -> Register health-check routes (/ and /health)
  -> Application Ready
```

During startup:

- `create_app()` in `server/app/__init__.py` runs first.
- Credentials are loaded and the environment is validated.
- Logging is configured and stored in `logs/app.log`.
- Extensions are initialized in `server/app/extensions.py`:
  - DB object
  - JWT object
  - Email object
  - Password hashing check/verification
- JWT error callbacks are registered for invalid, missing, and expired tokens,
  returning `401`.
- Blueprints are registered:
  - `auth`
  - `orders`
  - `customers`
  - `products`
  - `users`
  - `reports`
- Health checks are registered at `/` and `/health`.
- Flask listens on port `5000` with debug mode enabled, allowing reload on
  file changes.

## Phase-6 - Frontend process starts (client/)

```sh
cd client && npm run dev
```

Flow:

```text
Vite reads vite.config.js
  -> Configures /api proxy to http://127.0.0.1:5000
  -> Starts frontend at http://localhost:5173
  -> client/index.html loads /src/main.js
  -> Creates Vue app (App.vue)
  -> Initializes Pinia stores (auth.js, summary.js) from localStorage
       (token, user)
  -> Registers Vue Router (router/index.js)
  -> Mounts app to #app
  -> Frontend Ready
```

Startup steps:

1. Vite reads `vite.config.js` and checks the `/api` proxy to the backend.
2. The frontend usually runs on port `5173` with localhost.
3. `client/index.html` loads `src/main.js`.
4. Pinia initializes from localStorage (`token`, `user`).
5. Vue Router is initialized.
6. The app mounts to `#app`.

## Phase-7 - When a visitor opens the link in browser

### Landing (/ -> Landing.vue)

- Open `/` -> Load `Landing.vue`.
- Check `authStore.token`:
  - Token exists? Yes -> show Login.
  - Token exists? No -> show Register.
- No API call is made for the initial check.
- The landing page explains what the app is used for and shows the paths.
- From the landing page, the visitor either enters the login page (`/login`)
  or the register page (`/register`).

### Registration (/register -> Register.vue)

- Submit Registration Form -> `handleRegister()`.
- `POST /api/auth/register` -> `routes/auth.py::register_route` ->
  `auth_service.register()`.
- Normalize and validate email/password.
- `auth_service.register()`:
  - Check email uniqueness.
  - If `customer_id` is provided: validate customer exists, is unlinked, and
    email matches.
  - Create an unverified user.
  - Generate an OTP.
  - Hash OTP and set a 2-minute TTL.
  - `send_verification_code()`.
  - Log the OTP to `server/logs/dev_emails.log` (development).
  - Return `201`.
- UI switches to the Enter-Code step.

The form sends `POST /api/auth/register` with:

```text
name, email, password, customer_id
```

### Entering the code (/register -> OTP verification)

- Submit Email & OTP -> `handleVerify()`.
- `POST /api/auth/verify` -> `routes/auth.py::verify_route` ->
  `auth_service.verify_email()`.
- `auth_service.verify_email()`:
  - Increment verification attempts.
  - Attempts > 3? Reject.
  - Otherwise: validate OTP and expiry.
  - Invalid/Expired? Return `400` with attempts left.
  - Valid? Set `is_verified=true` and clear OTP hash.
  - If `customer_id` is provided:
    - Check link availability.
    - Link available: set `customers.user_id = user.id`.
    - Link unavailable: return `linked=false` with a warning.
  - Return `200`.
- UI shows the Link Warning if any, then moves to login.

The form sends `POST /api/auth/verify` with:

```text
email, code, customer_id?
```

### Login (/login -> Login.vue)

- Open `/login` -> Load `Login.vue`.
- Submit Email & Password -> `handleLogin()`.
- `POST /api/auth/login` -> `auth_service.login()`.
- `auth_service.login()`:
  - Load user by email.
  - Verify password (bcrypt).
  - Check `is_verified`.
  - Invalid credentials or unverified user? Return error.
  - Valid? Generate JWT (`sub`, `role`, `email`, `tv=token_version`).
  - Return `access_token` and `user`.
- `auth.js::login()`:
  - Save token and user to Pinia state.
  - Save token and user to localStorage.
- Check user role:
  - Admin: redirect to `/app/reports`.
  - Customer: redirect to `/app/my-orders`.

After successful registration, the user is redirected to the login page and
sends `POST /api/auth/login` with:

```text
email, password
```

### Password reset (/forget_password, /reset_password)

#### ForgetPassword (/forget_password -> ForgetPassword.vue)

- Open Forgot Password Page -> submit email.
- `ForgetPassword.vue::handleSubmit()` sends `POST /api/auth/forgot-password`.
- `auth_service.forgot_password()`:
  - Return Generic `200` to prevent email enumeration.
  - If user exists:
    - Generate reset token.
    - Hash with SHA-256.
    - Store hash and 1-hour TTL.
    - `send_password_reset()`.
    - Log reset link to development logs.
  - If user does not exist: no reset token is created.
  - Display generic success response.

#### ResetPassword (/reset_password -> ResetPassword.vue)

- Open reset link and extract token from URL query.
- Submit new password.
- `ResetPassword.vue::handleSubmit()` sends `POST /api/auth/reset-password?token=...`.
- `auth_service.reset_password()`:
  - Verify token hash and expiry.
  - Invalid/Expired? Return error.
  - Valid? Hash new password (bcrypt).
  - Update password hash.
  - Clear reset token.
  - Increment `token_version`.
  - Return success.
  - Older JWTs are rejected by `token_version` validation on subsequent
    requests.
- Redirect to login.

## Phase-8 - The first page load (client/src/layouts/AppLayout.Vue)

- Open `/app/*` -> Mount `AppLayout.vue`.
- `onMounted()` -> `auth.fetchMe(true)`.
  - Force refresh `GET /api/auth/me` (bypass 30-second cache).
  - Update current user and role.
- `enforceRoleForCurrentRoute()`:
  - Admin on `/app/my-orders`? Redirect to `/app/orders`.
  - Customer on `/app/orders`? Redirect to `/app/my-orders`.
  - Admin-only route (`meta.requiresAdmin`)? Redirect to `/app/orders`.
  - Otherwise: stay on the current route.
- `visibleLinks()`:
  - Render role-appropriate navigation links.
- User clicks Logout -> `handleLogout()`:
  - Clear authentication state and localStorage.
  - Redirect to `/login`.

## Phase-9 - Authorization on every request

Every API request passes through two gates, in frontend and backend:

### Frontend gates

- `services/api.js`:
  - Request interceptor: attaches the JWT as a Bearer token.
  - Response interceptor:
    - `401`: force logout (`/login`).
    - `403`: check role-guarded endpoints and force logout when out of role.
    - Other errors: propagate to the caller.

### Backend gates

- `utils/decorators.py`:
  - Loads and checks the user against the JWT.
  - Compares JWT `tv` with `users.token_version`.
  - `auth_required` gets the current user.
  - `role_required` checks the required role.
- `utils/permission.py`:
  - Role check against the user.
  - Ownership checks for the particular ID.
  - `can_view_order` for the user (admin/customer).

### Order visibility

- Backend `order_service.visible_orders_for(user)`:
  - Admin: returns all orders.
  - Customer: returns only orders related to that user.

## Phase-10 - User flow with roles

### Customer flow (client/src/views/MyOrders.Vue)

- Open `/app/my-orders`.
- `onMounted()` -> `fetchOrders()`.
- `GET /api/orders?per_page=200`.
- Backend `list_orders()` -> `visible_orders_for(user)`:
  - Admin: fetches all orders.
  - Customer: fetches only orders associated with their account.
- Returns the filtered orders.
- Frontend uses `countByStatus()` to group orders by status for display:

```text
Pending / Received / Shipped / Cancelled / Delivered / Returned
```

- Customer clicks an order:
  - `GET /api/orders/:id`.
  - `permissions.can_view_order()`.
  - Order owned by customer or user is admin? Yes -> return order details.
  - No -> return `404` to hide order existence.

### Admin flow: Orders (client/src/views/Orders.vue)

- Open `/app/orders`.
- `fetchOrders()` -> `GET /api/orders`.
- Query includes status filter, debounced search `q`, and pagination.
- Backend `list_orders()`:
  - Eager-load order items and customer (`joined_load`).
  - `_order_response()` serializes the order and computed total.
- Returns orders and renders the list.
- Admin changes status:
  - Cancelled/Returned? Ask browser `confirm()`.
  - Confirmed? Send `PATCH /api/orders/:id/status`.
  - `order_service.change_status()` -> `can_transition(ALLOWED_TRANSITIONS)`.
  - Valid transition? Yes -> update status in the database.
  - Valid transition? No -> return `400` error.
  - After status change, refresh orders.
  - `summaryStore.fetch(true)` bypasses cache and updates the dashboard
    summary.

### Admin flow: Create order (client/src/views/CreateOrder.vue)

- Open `/app/orders/new`.
- `onMounted()`:
  - `GET /api/products` (any authenticated user).
  - `GET /api/customers` (admin only).
- Load products and customers into the form.
- Admin submits order -> `handleSubmit()`.
- `POST /api/orders` (one item).
- Backend `order_service.create_order()`:
  - Requires admin role.
  - `order_service.validate_order_payload()` validates:
    - Order ID, date, customer, items, duplicate products, quantity
      (1–1000), and product existence.
  - Fetch current product price from the database (ignore client-sent
    `unit_price`).
  - Validation passed? Continue.
  - Validation failed? Return validation error.
  - Begin a database transaction.
  - Insert order header (Pending) + order items.
  - Duplicate `order_id`? Yes -> rollback and return `409` Conflict.
  - Other failure? Rollback all changes.
  - Success? Commit transaction and return `201 Created`.
  - Redirect to `/app/orders/:id`.

### Admin flow: Products (client/src/views/Products.vue)

- Open `/app/products`.
- `fetchProducts()` -> `GET /api/products`.
- Any authenticated user can view products.
- `savePrice()` -> `PATCH /api/products/:id`.
  - Admin only.
  - Update product price.
  - Return success.
  - Refresh product list.
- `createProduct()` -> `POST /api/products`.
  - Admin only.
  - Validate and insert product.
  - Return success.
  - Refresh product list.
- `deleteProduct()` -> `DELETE /api/products/:id`.
  - Admin only.
  - Return `409` if product is used in `order_items`.
  - Otherwise delete product and return success.
  - Refresh product list.

### Admin flow: Users (client/src/views/users.vue)

- Open `/app/users`.
- `fetchUsers()` -> `GET /api/users`.
- Admin only.
- `createUser()` -> `POST /api/users`.
  - Validate user details and create user.
  - Return success.
  - Refresh user list.
- `updateUserRole()` -> `PATCH /api/users/role`.
  - Admin only.
  - Validate role.
  - Protect last admin.
  - Update user role.
  - Return success.
  - Refresh user list.
- `deleteUser()` -> `DELETE /api/users`.
  - Admin only.
  - Prevent self-deletion and last-admin deletion.
  - Delete user and return success.
  - Refresh user list.

### Admin flow: Duplicates (/duplicates -> Duplicates.vue)

- Open `/duplicates`.
- `load()` -> `GET /api/orders/duplicates`.
- Backend `find_duplicates()`:
  - Identify and group duplicate orders.
  - Return duplicate groups.
- Render duplicates for review.
- Admin reviews duplicate group -> selects Copy to Cancel -> `cancelCopy()`.
- `PATCH /api/orders/:id/status`:
  - Backend validates the request.
  - Updates order status.
  - Return success.
  - Refresh duplicate list.
- It always deletes after reviewing.

### Reports (/reports, /totals -> Reports.Vue, Totals.Vue)

- Both share `summaryStore.fetch(force)`.
- Backend `order_service.get_dashboard_summary()`:
  - Joins orders, items, and products.
  - Filters by status and returns the respective values.
- Format values with `utils/format.js`:
  - `money`
  - `number`
  - `percentage`
  - `date`
- Product-wise and date-wise reports can be viewed in the dashboard.

---

## Implementation notes

- `app = Flask(__name__)` creates the centralized application object that holds
  the URL mapping, app config, error handlers, templates, and registered
  extensions. The app name is used for imports.
- For Python review, practice aggregation functions, window functions, and when
  to use particular keywords.
- For live streaming, identify the proper terminology and architecture used.
- Use dynamic values with `f` strings.
- Do not implement blindly; know why a keyword or function is used and keep it
  simple.
- Learn Python tracebacks and how to handle them.
- Keep Git and documentation practices consistent.
- Document everything that is built.
- Investigate MQTT use cases across the internet.
- Review deployment practices.
