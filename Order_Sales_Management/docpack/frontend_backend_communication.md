# How the Frontend and Backend Communicate (Line-Level)

This file shows the exact files, functions, and lines where the Vue frontend and Flask backend exchange data for `OrderSalesManagement`.

All paths are relative to the repository root `Order_Sales_Management/`.

---

## 1. Global communication contract

### Request path

The browser does not call the Flask server directly. Vite rewrites `/api` requests during development.

- `client/vite.config.js`
  - `server.proxy['/api'] = 'http://127.0.0.1:5000'`
  - Result: a request to `http://localhost:5173/api/orders` is forwarded by Vite to `http://127.0.0.1:5000/api/orders`.

### Authentication header

Every authenticated request adds the JWT in one place.

- `client/src/services/api.js`
  - `api.interceptors.request.use((config) => { ... })`
  - Adds `Authorization: Bearer <token>` from `localStorage.getItem('token')`.
  - Applied to every request made through `api.get('/orders')`, `api.post('/auth/login')`, etc.

### Response error handling

- `client/src/services/api.js`
  - `api.interceptors.response.use((res) => res, (err) => { ... })`
  - On `401` or `422`, removes stale `token` and `user` from `localStorage` and redirects to `/login`.

### Authentication state

- `client/src/stores/auth.js`
  - `auth.login(email, password)` saves `res.data.access_token` and the user object.
  - `auth.fetchMe()` refreshes the user on load.
  - `auth.logout()` clears `token`, `user`, and both `localStorage` keys.

---

## 2. Step-by-step request flow

### Step 1: UI dispatch

- `client/src/views/Login.vue`
  - `handleLogin()` calls `await auth.login(email, password)`.
  - `auth.login(email, password)` is defined in `client/src/stores/auth.js`.

### Step 2: API call

- `client/src/stores/auth.js`
  - `const res = await api.post('/auth/login', { email, password })`
  - `api` is imported from `client/src/services/api.js`.

### Step 3: HTTP interception

- `client/src/services/api.js`
  - `api.interceptors.request.use(...)` adds `Authorization: Bearer <token>`.
  - The request is sent to `http://127.0.0.1:5000/api/auth/login` through the Vite dev proxy.

### Step 4: Flask route handling

- `server/app/routes/auth.py`
  - `auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')`
  - `auth_bp.post('/login')` calls `login_route()`.
  - `login_route()` calls `auth_service.login()`.

### Step 5: Service logic

- `server/app/services/auth_service.py`
  - `login(email, password)` loads the user, checks the password, and creates the JWT.
  - Returns `{"access_token": token, "user": user}`.

### Step 6: Return to frontend

- `client/src/stores/auth.js`
  - `this.token = res.data.access_token`
  - `this.user = res.data.user`
  - `localStorage.setItem('token', this.token)`
  - `localStorage.setItem('user', JSON.stringify(this.user))`

### Step 7: Protected page load

- Example: orders list
  - `client/src/views/Orders.vue`
    - `await api.get('/orders', { params })`
  - `client/src/services/api.js`
    - Adds `Authorization: Bearer <token>`
    - Vite forwards to `http://127.0.0.1:5000/api/orders`
  - `server/app/routes/orders.py`
    - `orders_bp = Blueprint('orders', __name__, url_prefix='/api/orders')`
    - `list_orders()` uses `auth_required`, reads `g.current_user`, and calls `order_service.visible_orders_for(user)`.
  - Result returned to Vue: `{ orders: [...], page, per_page, total, pages }`.

---

## 3. Visual summary of the exact communication points

```text
Browser
  -> client/src/views/Login.vue        (handleLogin)
  -> client/src/stores/auth.js         (login action)
  -> client/src/services/api.js        (api.post('/auth/login') + interceptor adds Authorization)
  -> Vite dev proxy                    (/api -> http://127.0.0.1:5000)
  -> server/app/routes/auth.py         (login_route)
  -> server/app/services/auth_service.py (login, create token)
  -> Flask backend                     returns JSON { access_token, user }
  -> client/src/services/api.js        (response)
  -> client/src/stores/auth.js         (save token/user)
  -> client/src/router/index.js        (guards allow access to /app routes)
```

Every later request follows the same path:

```text
/api/orders  -> client/src/views/Orders.vue -> client/src/services/api.js -> Vite proxy -> server/app/routes/orders.py
/api/reports -> client/src/views/Reports.vue -> client/src/services/api.js -> Vite proxy -> server/app/routes/reports.py
/api/products -> client/src/views/Products.vue -> client/src/services/api.js -> Vite proxy -> server/app/routes/products.py
```

---

## 4. Exact lines (mapped to files)

### `client/src/services/api.js`

- Axios instance base URL:
  - `const api = axios.create({ baseURL: '/api' })`
- Request interceptor that attaches the JWT:
  - `api.interceptors.request.use((config) => { ... })`
- Response interceptor:
  - `api.interceptors.response.use((res) => res, (err) => { ... })`

### `client/src/stores/auth.js`

- Login action:
  - `async login(email, password) { ... }`
- fetchMe action:
  - `async fetchMe() { ... }`
- Logout action:
  - `logout() { ... }`

### `client/src/router/index.js`

- Guard setup:
  - `router.beforeEach((to, from, next) => { ... })`
- Protected route metadata:
  - `meta: { requiresAuth: true }`
  - `meta: { requiresAdmin: true }`

### `client/vite.config.js`

- Dev proxy:
  - `server.proxy['/api'] = 'http://127.0.0.1:5000'`

### `server/app/__init__.py`

- Blueprint registration:
  - `app.register_blueprint(auth_bp)`
  - `app.register_blueprint(orders_bp)`
  - `app.register_blueprint(reports_bp)`
  - `app.register_blueprint(products_bp)`
  - `app.register_blueprint(customers_bp)`
  - `app.register_blueprint(users_bp)`

### `server/app/routes/auth.py`

- `auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')`
- `auth_bp.post('/login')` -> `login_route()`
- `auth_bp.post('/verify')` -> `verify_route()`
- `auth_bp.get('/me')` -> `me_route()`

### `server/app/routes/orders.py`

- `orders_bp = Blueprint('orders', __name__, url_prefix='/api/orders')`
- `list_orders()` is wrapped by `@auth_required` and calls `order_service.visible_orders_for(user)`.
- `create_order()` is wrapped by `@role_required(Role.ADMIN.value)` and calls `create_order_service()`.
- `update_status()` is wrapped by `@role_required(Role.ADMIN.value)` and calls `change_status()`.

### `server/app/services/auth_service.py`

- Login:
  - `login(email, password)`
  - Creates the JWT payload: `identity=str(user.id)`, `role`, `email`, `tv`.

### `server/app/services/order_service.py`

- Visibility:
  - `visible_orders_for(user)`
- Creation:
  - `create_order(payload)`
- Status:
  - `change_status(order, new_status)`

---

## 5. Quick lookup: what line to check for each communication step

| Communication step | Check this line | File |
|---|---|---|
| Frontend makes a request | `api.get('/orders')` / `api.post('/auth/login')` | `client/src/services/api.js` and the calling view/store |
| JWT is attached to the request | `config.headers.Authorization = Bearer <token>` | `client/src/services/api.js` |
| Vite forwards `/api` to Flask | `server.proxy['/api'] = 'http://127.0.0.1:5000'` | `client/vite.config.js` |
| Flask receives the route | `url_prefix='/api/...'` and `@routes.<name>` | `server/app/routes/*.py` |
| Auth/role enforced | `@auth_required`, `@role_required(...)`, `g.current_user` | `server/app/routes/*.py` |
| Business logic | `order_service.create_order()`, `order_service.visible_orders_for()`, `order_service.change_status()` | `server/app/services/order_service.py` |
| Database | SQLAlchemy models and queries in `server/app/models.py` | `server/app/models.py` |
| Return path to Vue | the JSON object returned by the route is stored in a Pinia store | `client/src/stores/summary.js` or the calling view |

---

## 6. Why this setup is used here

- Separation of concerns: Vue only knows the API, Flask never touches the browser.
- Vite proxy allows development on `localhost:5173` while the API runs on `localhost:5000`, with no CORS or absolute-host config needed in dev.
- JWTs are sent automatically, so components only call `api.get('/orders')` instead of managing headers manually.
- Service files contain the business rules; routes contain request/response handling only.
