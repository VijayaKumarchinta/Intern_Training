#!/usr/bin/env python3
"""Structured encoder for the full web app architecture documentation.

This file keeps the pasted architecture text in structured Python data
(sections, phases, steps, and notes). Running it prints the same documentation
in markdown form, so the docs have a single source of truth.
"""

# Top-level sections in the documentation.
SECTIONS = [
    {
        "title": "Full Architecture of the web app what is created",
        "sections": [
            {
                "number": "Phase-0",
                "title": "Prerequisites",
                "body": [
                    "- PostgreSQL 14+ to store the database.",
                    "- Python 3.11+ to run the backend.",
                    "- Node.js 18+ to run/build the frontend.",
                ],
            },
            {
                "number": "Phase-1",
                "title": "DB configuration (db/init.sql)",
                "body": [
                    "Set up the database with proper credentials and schema first:",
                    "1. Confirm the correct database is connected.",
                    "2. Create the schema `order_sales` if missing.",
                    "3. Create the tables:",
                    "   - `user` - stores users with hashed passwords, verified status, and tokens.",
                    "   - `customers` - stores customer details referenced from `user_id`.",
                    "   - `products` - stores products separately with unit prices.",
                    "   - `orders` - stores order details referenced from `customer_id`.",
                    "   - `order_items` - stores inline order items referenced from `order_id` and `product_id`, with cascade on `order_id`.",
                    "4. Add indexes:",
                    "   - `orders` indexes on `customer_id`, `order_date`, and `order_status` for fast fetching.",
                    "5. Add triggers:",
                    "   - Automatically update `users` and `orders` registered and login times.",
                    "6. Add constraints for `order_status`.",
                    "After designing, initialize the DB with:",
                    "```psql -U postgres -f db/init.sql```",
                ],
            },
            {
                "number": "Phase-2",
                "title": "Backend configuration (server/.env)",
                "body": [
                    "The config class in `app` reads this file via the `dotenv` module so the correct database can be connected.",
                    "File path: `server/app/config`.",
                ],
            },
            {
                "number": "Phase-3",
                "title": "First admin bootstrap (server/manage.py)",
                "body": [
                    "Create the admin by running:",
                    "```flask --app manage create-admin```",
                    "This inserts a user with role `admin`, `is_verified` as true, and `token_version=0`.",
                ],
            },
            {
                "number": "Phase-4",
                "title": "Importing of the data (db/load_data.py)",
                "body": [
                    "```python \"db/load_data.py\" --csv data/Online_Store_Orders.csv --dry-run```",
                    "The pipeline:",
                    "  - reads the CSV file that contains columns.",
                    "  - if any column is missing, the operation aborts.",
                    "  - parses into rows.",
                    "  - can create customers and products later if needed.",
                    "  - can insert items and orders through frontend later.",
                ],
            },
            {
                "number": "Phase-5",
                "title": "Backend process starts (server/run.py)",
                "body": [
                    "```python server/run.py```",
                    "Flow:",
                    "  create_app()",
                    "    -> Load credentials and validate environment.",
                    "    -> Configure logging (logs/app.log).",
                    "    -> Initialize extensions: DB, JWT, Email, Password Hashing.",
                    "    -> Register JWT error handlers: Invalid, Missing, Expired Token -> 401.",
                    "    -> Register Blueprints: Auth, Orders, Customers, Products, Users, Reports.",
                    "    -> Register health-check routes (/ and /health).",
                    "    -> Application Ready.",
                    "create_app() in server/app/__init__.py executes:",
                    "  - loads credentials and ensures the environment is ready.",
                    "  - configures logging and stores it in logs/app.log.",
                    "  - initializes extensions (db, jwt, email) and password hashing/checking in server/app/extensions.py.",
                    "  - registers JWT error callbacks (invalid, missing, expired -> 401).",
                    "  - registers blueprints: auth, orders, customers, products, users, reports.",
                    "  - registers health checks (/ and /health).",
                    "Flask listens on port 5000 with debug enabled, allowing reload on file changes.",
                ],
            },
            {
                "number": "Phase-6",
                "title": "Frontend process starts (client/)",
                "body": [
                    "```cd client && npm run dev```",
                    "Flow:",
                    "  Vite reads vite.config.js and configures the /api proxy to http://127.0.0.1:5000.",
                    "  Starts frontend at http://localhost:5173.",
                    "  client/index.html loads /src/main.js.",
                    "  Creates Vue app (App.vue).",
                    "  Initializes Pinia stores (auth.js, summary.js) from localStorage (token, user).",
                    "  Registers Vue Router (router/index.js).",
                    "  Mounts app to #app.",
                    "  Frontend Ready.",
                    "Starting the frontend:",
                    "  - vite reads its config file (vite.config.js) and checks the /api proxy to backend.",
                    "  - normally the frontend runs on port 5173 with localhost.",
                    "  - client/index.html loads src/main.js.",
                    "  - Pinia initializes from localStorage, then routes are initialized.",
                ],
            },
            {
                "number": "Phase-7",
                "title": "When a visitor opens the link in browser",
                "items": [
                    {
                        "name": "Landing (/ -> Landing.vue)",
                        "body": [
                            "Open / -> Load Landing.vue.",
                            "Check authStore.token.",
                            "  - Token exists? Yes: Show Login.",
                            "  - Token exists? No: Show Register.",
                            "  - No API call.",
                            "The landing page shows what the app is used for and the paths.",
                            "From the landing page, the visitor either enters the login page (/login) or the register page (/register).",
                        ],
                    },
                    {
                        "name": "Registration (/register -> Register.vue)",
                        "body": [
                            "Submit Registration Form -> handleRegister().",
                            "POST /api/auth/register -> routes/auth.py::register_route -> auth_service.register().",
                            "  Normalize & Validate Email/Password.",
                            "  auth_service.register():",
                            "    - Check Email Uniqueness.",
                            "    - If customer_id Provided: Validate Customer Exists, Is Unlinked & Email Matches.",
                            "    - Create Unverified User.",
                            "    - Generate OTP.",
                            "    - Hash OTP & Set 2-Minute TTL.",
                            "    - send_verification_code().",
                            "    - Log OTP to server/logs/dev_emails.log (Development).",
                            "    - Return 201.",
                            "  UI Switches to Enter-Code Step.",
                            "Request payload: name, email, password, customer_id.",
                        ],
                    },
                    {
                        "name": "Entering the code",
                        "body": [
                            "Submit Email & OTP -> handleVerify().",
                            "POST /api/auth/verify -> routes/auth.py::verify_route -> auth_service.verify_email().",
                            "  Check attempts; if > 3, reject.",
                            "  Validate OTP & Expiry.",
                            "  Invalid/Expired: Return 400 with Attempts Left.",
                            "  Valid: Set is_verified=true & Clear OTP Hash.",
                            "  If customer_id Provided:",
                            "    - Link Available: Set customers.user_id = user.id.",
                            "    - Link Unavailable: Return linked=false with Warning.",
                            "  Return 200.",
                            "UI Shows Link Warning (if any) & Move to Login.",
                            "Request payload: email, code, customer_id?.",
                        ],
                    },
                    {
                        "name": "Login (/login -> Login.vue)",
                        "body": [
                            "Open /login -> Load Login.vue.",
                            "Submit Email & Password -> handleLogin().",
                            "POST /api/auth/login -> auth_service.login().",
                            "  Load User by Email.",
                            "  Verify Password (bcrypt).",
                            "  Check is_verified.",
                            "  Invalid Credentials or Unverified User? Return Error.",
                            "  Valid? Generate JWT (sub, role, email, tv=token_version).",
                            "  Return access_token & user.",
                            "auth.js::login():",
                            "  Save Token & User to Pinia State + localStorage.",
                            "  Check User Role.",
                            "  Admin: Redirect to /app/reports.",
                            "  Customer: Redirect to /app/my-orders.",
                            "Request payload: email, password.",
                        ],
                    },
                    {
                        "name": "Password reset (/forget_password, /reset_password)",
                        "body": [
                            "ForgetPassword (/forget_password -> ForgetPassword.vue):",
                            "  Open Forgot Password Page -> Submit Email.",
                            "  ForgetPassword.vue::handleSubmit() sends POST /api/auth/forgot-password.",
                            "  auth_service.forgot_password():",
                            "    - Return Generic 200 to Prevent Email Enumeration.",
                            "    - If User Exists: Generate Reset Token, Hash with SHA-256, Store Hash & 1-Hour TTL, send_password_reset(), log reset link to dev logs.",
                            "    - No: No Reset Token Created.",
                            "    - Display Generic Success Response.",
                            "ResetPassword (/reset_password -> ResetPassword.Vue):",
                            "  Open Reset Link -> Extract Token from URL Query.",
                            "  Submit New Password -> ResetPassword.vue::handleSubmit() -> POST /api/auth/reset-password?token=...",
                            "  auth_service.reset_password():",
                            "    - Verify Token Hash & Expiry.",
                            "    - Invalid/Expired: Return Error.",
                            "    - Valid: Hash New Password (bcrypt), Update Password Hash, Clear Reset Token, Increment token_version.",
                            "    - Return Success.",
                            "    - Older JWTs Rejected by token_version Validation on Subsequent Requests.",
                            "  Redirect to Login.",
                        ],
                    },
                ],
            },
            {
                "number": "Phase-8",
                "title": "The first page load (client/src/layouts/AppLayout.Vue)",
                "body": [
                    "Open /app/* -> Mount AppLayout.vue.",
                    "onMounted() -> auth.fetchMe(true):",
                    "  - Force Refresh GET /api/auth/me (Bypass 30-Second Cache).",
                    "  - Update Current User & Role.",
                    "enforceRoleForCurrentRoute():",
                    "  - Admin on /app/my-orders? Redirect to /app/orders.",
                    "  - Customer on /app/orders? Redirect to /app/my-orders.",
                    "  - Admin-only route (meta.requiresAdmin)? Redirect to /app/orders.",
                    "  - Otherwise: Stay on Current Route.",
                    "visibleLinks(): render role-appropriate navigation links.",
                    "handleLogout(): clear authentication state and localStorage; redirect to /login.",
                ],
            },
            {
                "number": "Phase-9",
                "title": "Authorization on every request",
                "body": [
                    "Every API request passes through two gates: frontend and backend.",
                    "Frontend gates: services/api.js -> request interceptor (attach JWT as Bearer token) and response interceptor (401 force logout -> /login, 403 role-guarded force logout -> /login, other errors propagate to caller).",
                    "Backend gates:",
                    "  utils/decorators.py: load and check users against the JWT, compare JWT tv with users.token_version, auth_required gets the current user, role_required checks the required role.",
                    "  utils/permission.py: role check, ownership check for the particular ID, can_view_order for admin/customer.",
                    "Order visibility: order_service.visible_orders_for(user): admin returns all orders, customer returns only orders related to that user.",
                ],
            },
            {
                "number": "Phase-10",
                "title": "User flow with roles",
                "items": [
                    {
                        "name": "Customer flow (client/src/views/MyOrders.Vue)",
                        "body": [
                            "Open /app/my-orders.",
                            "onMounted() -> fetchOrders().",
                            "GET /api/orders?per_page=200.",
                            "Backend list_orders() -> visible_orders_for(user):",
                            "  - Admin: Fetches all orders.",
                            "  - Customer: Fetches only orders associated with their account.",
                            "Frontend groups orders by status with countByStatus(): Pending / Received / Shipped / Cancelled / Delivered / Returned.",
                            "Customer clicks an order:",
                            "  - GET /api/orders/:id.",
                            "  - permissions.can_view_order().",
                            "  - Yes: return order details.",
                            "  - No: return 404 to hide order existence.",
                        ],
                    },
                    {
                        "name": "Admin flow: Orders (client/src/views/Orders.vue)",
                        "body": [
                            "Open /app/orders.",
                            "fetchOrders() -> GET /api/orders.",
                            "Query includes status filter, debounced search q, and pagination.",
                            "Backend list_orders(): eager-load order items and customer (joined_load), _order_response() serializes order and computed total.",
                            "Render Orders List.",
                            "Admin changes status:",
                            "  - Cancelled/Returned? Ask browser confirm().",
                            "  - Confirmed? PATCH /api/orders/:id/status.",
                            "  - order_service.change_status() -> can_transition(ALLOWED_TRANSITIONS).",
                            "  - Valid transition? Yes -> update status in database.",
                            "  - Valid transition? No -> return 400 error.",
                            "  - Refresh orders.",
                            "  - summaryStore.fetch(true) bypasses cache and updates the dashboard summary.",
                        ],
                    },
                    {
                        "name": "Admin flow: Create order (client/src/views/CreateOrder.vue)",
                        "body": [
                            "Open /app/orders/new.",
                            "onMounted():",
                            "  - GET /api/products (any authenticated user).",
                            "  - GET /api/customers (admin only).",
                            "Load Products & Customers into Form.",
                            "Admin Submits Order -> handleSubmit().",
                            "POST /api/orders (one item).",
                            "Backend order_service.create_order():",
                            "  - Check Admin Role.",
                            "  - order_service.validate_order_payload(): validates Order ID, Date, Customer, Items, Duplicate Products, Quantity (1-1000) & Product Existence.",
                            "  - Fetch Current Product Price from Database (Ignore Client-Sent unit_price).",
                            "  - Validation Passed? Yes: continue.",
                            "  - Validation Failed? No: return validation error.",
                            "  - Begin Database Transaction.",
                            "  - Insert Order Header (Pending) + Order Items.",
                            "  - Duplicate order_id? Yes: rollback & return 409 Conflict.",
                            "  - Other Failure? Rollback All Changes.",
                            "  - Success? Commit Transaction & Return 201 Created.",
                            "  - Redirect to /app/orders/:id.",
                        ],
                    },
                    {
                        "name": "Admin flow: Products (client/src/views/Products.Vue)",
                        "body": [
                            "Open /app/products.",
                            "fetchProducts() -> GET /api/products (any authenticated user can view products).",
                            "savePrice() -> PATCH /api/products/:id (admin only, update product price, return success, refresh product list).",
                            "createProduct() -> POST /api/products (admin only, validate and insert product, return success, refresh product list).",
                            "deleteProduct() -> DELETE /api/products/:id (admin only, return 409 if product used in order_items, otherwise delete and return success, refresh product list).",
                        ],
                    },
                    {
                        "name": "Admin flow: Users (client/src/views/users.vue)",
                        "body": [
                            "Open /app/users.",
                            "fetchUsers() -> GET /api/users (admin authorized).",
                            "createUser() -> POST /api/users (validate details, create, return success, refresh user list).",
                            "updateUserRole() -> PATCH /api/users/role (admin only, validate role, protect last admin, update role, return success, refresh user list).",
                            "deleteUser() -> DELETE /api/users (admin only, prevent self-deletion and last-admin deletion, delete and return success, refresh user list).",
                        ],
                    },
                    {
                        "name": "Duplicates (/duplicates -> Duplicates.vue)",
                        "body": [
                            "Open /duplicates.",
                            "load() -> GET /api/orders/duplicates.",
                            "Backend find_duplicates(): identify and group duplicate orders, return groups.",
                            "Render Duplicates for Review.",
                            "Admin reviews duplicate group -> select Copy to Cancel -> cancelCopy().",
                            "PATCH /api/orders/:id/status: backend validates request and updates order status, return success, refresh duplicate list.",
                            "It always deletes after reviewing.",
                        ],
                    },
                    {
                        "name": "Reports (/reports, /totals -> Reports.Vue, Totals.Vue)",
                        "body": [
                            "Both share summaryStore.fetch(force).",
                            "Backend order_service.get_dashboard_summary(): join all orders, items, products, filter by status, return respective values.",
                            "Format via utils/format.js: money, number, percentage, date.",
                            "Product-wise and date-wise reports can be viewed in the dashboard.",
                        ],
                    },
                ],
            },
            {
                "number": "Implementation notes",
                "body": [
                    "app = Flask(__name__): creates the centralized application object that holds URL mapping, app config, error handlers, templates, and registered extensions. The app name is used for imports.",
                    "Python review: practice aggregation functions, window functions, and when to use particular keywords.",
                    "Live streaming: identify the proper terminology and architecture used.",
                    "Use dynamic values with f strings.",
                    "Do not implement blindly; know why a keyword or function is used and keep it simple.",
                    "Learn Python tracebacks and how to handle them.",
                    "Keep Git and documentation practices consistent.",
                    "Document everything that is built.",
                    "Investigate MQTT use cases across the internet.",
                    "Review deployment practices.",
                ],
            },
        ],
    },
]

if __name__ == "__main__":
    import sys
    from pathlib import Path

    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("documentation/website_architecture_full.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# " + SECTIONS[0]["title"] + "\n\n"]
    for section in SECTIONS[0]["sections"]:
        lines.append("## " + section["number"] + " - " + section["title"] + "\n\n")
        for body_line in section.get("body", []):
            lines.append(body_line + "\n")
        for item in section.get("items", []):
            if isinstance(item, dict):
                lines.append("### " + item["name"] + "\n\n")
                for line in item.get("body", []):
                    lines.append(line + "\n")
            else:
                lines.append("- " + item + "\n")
        lines.append("\n")
    out.write_text("".join(lines), encoding="utf-8")
    print(out)
