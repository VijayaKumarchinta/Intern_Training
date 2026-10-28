# Full Architecture of the web app what is created

## Phase-0

- Before running anything make sure you got:
  - postgresql with 14+ version so the data can be stored in a database
  - Python with 3.11+ version helps us to run the backend
  - Node.js with 18+ version helps us to run/build the frontend

## Phase-1 - DB configuration(db/init.sql)

- Now first make sure you setup the db setup with proper db credentials,schema, tables
  - According to my setup design:
    - it will check whether the correct db is connected or not then it will create:
      - schema(order_sales) if missing
        - Tables:
          - user - where it will store the users with hashed passwords,verified users, and it's respective tokens
          - Customers - where it stores the customer details while taking reference from the user_id
          - Products - where it stores products separately and there unit prices
          - Orders - where it stores the order details while taking the reference from customer id
          - Order_items - where it stores the inline items while taking reference from order_id and product_id while on cascade w.r.t the order_id
        - Indexes:
          - to fetch the data easily w.r.t to the order tables with columns like customer_id, order_date, order_Status
        - Triggers:
          - To automatically update the users and orders registered and login time
        - Constraints w.r.t the order_status
  - After designing all this Run and setup the db using this this cmd

  ```psql -U postgres -f db/init.sql```

## Phase-2 - Backend Configuration(server/.env)

- the config class which is in app will read this file via dotenv module so we able to connect to the correct db
- File path:server/app/config

## Phase-3 - First admin bootstrap(server/manage.py)

- To set up the admin we can directly run

    ```flask --app manage create-admin```

This will insert a user with role admin while being is_verified as true and token_version=0

## Phase-4 - importing of the data(db/load_data.py)

```python "db/load_data.py" --csv data/Online_Store_Orders.csv --dry-run```

- The Pipeline is:
  - reads the csv file that contain columns
  - if any column is missing the operation will abort
  - parse into rows accordingly
  - can create customers and products later on if we need anything to add
  - can insert items and orders through frontend later on

## Phase-5 - Backend process starts(server/run.py)

``` python server/run.py → create_app() → Load credentials & validate environment → Configure logging (logs/app.log) → Initialize extensions (DB, JWT, Email, Password Hashing) → Register JWT error handlers (Invalid, Missing, Expired Token → 401) → Register Blueprints (Auth, Orders, Customers, Products, Users, Reports) → Register health-check routes (/ and /health) → Application Ready ```

- when we start it follows the order:
  - go to the "create_app()" which is in "server/app/__init.py__":
    - first will load the credentials and make sure the environment is ready
    - then it config the logs and stores in logs/"app.log"
    - Initialize the extensions and creating objects for db,jwt and email(for later check out) and checking and verifying of passwords are done in this file "server/app/extensions.py"
    - After that it will register the error callbacks related to jwt(invalidtoken,missing token,expiredtoken) while returning 401
    - then it will register their respective blueprints which contains their respective routes(auth,orders,customers,products,users,reports)
    - Finally will register the health checks ("/","/health")
    - Flask will listen on port number 5000 while enable the debug state as true which allows us to reload on file changes

## Phase-6 - Frontend process starts(client/)

- ``` cd client && npm run dev → Vite reads vite.config.js and configures the /api → http://127.0.0.1:5000 proxy → Starts frontend at http://localhost:5173 → client/index.html loads /src/main.js → Creates Vue app (App.vue) → Initializes Pinia stores (auth.js, summary.js) from localStorage (token, user) → Registers Vue Router (router/index.js) → Mounts app to #app → Frontend Ready ```

- when we start the frontend it will go like this:
  - vite reads it's config file(vite.config.js) and check the proxy(backend api)
  - usually frontend runs on port 5173 with localhost
  - then "client/index.html" loads the main.js("/src/main.js")
  - here we use pinia to initialize from the localstorage then initialize the respective routes

## Phase-7 - when visitor opens the link in browser

- `Landing(/ -> Landing.vue)`:

- ```Open / → Load Landing.vue → Check authStore.token → Token exists? → Yes: Show "Login" | No: Show "Register" → No API Call```

      - it shows about what this app is used for and shows the paths 
      - from the landing page the visitor either enter in login page(/login) or register page(/register)

- `Registration(/register -> Register.vue)`:
- ``Submit form``

  - ```Submit Registration Form → handleRegister() → POST /api/auth/register → routes/auth.py::register_route → Normalize & Validate Email/Password → auth_service.register() → Check Email Uniqueness → If customer_id Provided: Validate Customer Exists, Is Unlinked & Email Matches → Create Unverified User → Generate OTP → Hash OTP & Set 2-Minute TTL → send_verification_code() → Log OTP to server/logs/dev_emails.log (Development) → Return 201 → UI Switches to Enter-Code Step```

  - when we submit the form that is show it will send a backend request ```post /api/auth/register``` with "name,email,password,customer_id"
  - Backend will check the following(```routes/auth.py::register_route -> auth_service.register```):
    - uniqueness of email and then it will insert as unverified user
    - then it generates an otp while keeping it as hashed, expiry limit
    - then the code is gonna generate in server/logs/dev_emails.log since it is a business data
  - then it switches to UI where we can able to enter that code

- ``Entering the code``

  - ```Submit Email & OTP → handleVerify() → POST /api/auth/verify → routes/auth.py::verify_route → auth_service.verify_email() → Increment Verification Attempts → Attempts > 3? → Reject | Otherwise: Validate OTP & Expiry → Invalid/Expired? → Return 400 with Attempts Left | Valid? → Set is_verified=true & Clear OTP Hash → customer_id Provided? → Yes: Check Link Availability → Link Available: Set customers.user_id = user.id | Link Unavailable: Return linked=false with Warning → Return 200 → UI Shows Link Warning (if any) → Move to Login```

  - After that code is entered it will send a backend request ```POST /api/auth/verify``` with "email, code, customer_id?"
  - Backend will check the following(from frontend```routes/auth.py::verify_route sends to → auth_service.verify_email```)
    - check the attempts if > 3 -> rejects
    - if it's correct then the user will be verified and will link to the customer_id and then UI moves to login

- `Login(/login -> Login.vue)`:

- ```Open /login → Load Login.vue → Submit Email & Password → handleLogin() → POST /api/auth/login → auth_service.login() → Load User by Email → Verify Password (bcrypt) → Check is_verified → Invalid Credentials or Unverified User? → Return Error | Valid? → Generate JWT (sub, role, email, tv=token_version) → Return access_token & user → stores/auth.js::login() → Save Token & User to Pinia State + localStorage → Check User Role → Admin: Redirect to /app/reports | Customer: Redirect to /app/my-orders```

  - After successful register it redirects to the login page and send a backend req to ```POST /api/auth/login``` with "email, password"
    - loads the users by email
    - check the password then check is_verified then issue a token which is used for logout-everywhere
    - then it returns the "access_token, user"
    - then a frontend request is formed and save those details to state
    - redirects to :
      - role:
        - admin(/app/reports)
        - customer(/app/my-orders)

- `Password reset(/forget_password,/reset_password)`
  - ``ForgetPassword(/forget_password -> ForgetPassword.vue)``:

    -```Open Forgot Password Page → Submit Email → ForgotPassword.vue::handleSubmit() → POST /api/auth/forgot-password → auth_service.forgot_password() → Return Generic 200 (Prevent Email Enumeration) → User Exists? → Yes: Generate Reset Token → Hash with SHA-256 → Store Hash & 1-Hour TTL → send_password_reset() → Log Reset Link to Development Logs | No: No Reset Token Created → Display Generic Success Response```

    - from frontend click on forget_password button ```ForgotPassword.vue::handleSubmit sends to → POST /api/auth/forgot-password```
    - if the user exists `auth_service.forgot_password` with create a token and let the dev-logs give that link via `send_password_reset`
  
  - ``ResetPassword(/reset_password -> ResetPassword.Vue)``:

    - ```Open Reset Link → Extract Token from URL Query → Submit New Password → ResetPassword.vue::handleSubmit() → POST /api/auth/reset-password?token=... → auth_service.reset_password() → Verify Token Hash & Expiry → Invalid/Expired? → Return Error | Valid? → Hash New Password (bcrypt) → Update Password Hash → Clear Reset Token → Increment token_version → Return Success → Older JWTs Rejected by token_version Validation on Subsequent Requests → Redirect to Login```

      - from frontend when user click on reset button ```ResetPassword.vue::handleSubmit → POST /api/auth/reset-password?token=...```
      - `reset_password` verifies the hash and time limit then gives a new token to the user and the old jwt tokens are being rejected

## Phase-8 - the first page load(client/src/layouts/AppLayout.Vue)

- ```Open /app/* → Mount AppLayout.vue → onMounted() → auth.fetchMe(true) → Force Refresh GET /api/auth/me (Bypass 30-Second Cache) → Update Current User & Role → enforceRoleForCurrentRoute() → Check Role Against Current Route → Admin on /app/my-orders? → Redirect to /app/orders | Customer on /app/orders? → Redirect to /app/my-orders | Customer on Admin-Only Route (meta.requiresAdmin)? → Redirect to /app/orders | Otherwise: Stay on Current Route → visibleLinks() → Render Role-Appropriate Navigation Links → User Clicks Logout → handleLogout() → Clear Authentication State & localStorage → Redirect to /login```

- Here the shell will mounts around every /app/* view
- onMounted():
  - await auth.fetchMe(true):
    - a forced refresh of ```/api/auth/me``` so it will be refresh w.r.t the role
  - enforceRoleForCurrentRoute():
    - if admin role is on `/app/my-orders` redirects -> `/app/orders`
    - if customer role is on `/app/orders` redirects -> `/app/my-orders`
    - if and only if the role is admin directly redirects -> `/app/orders`
  - visible  Links():
    - it is based on the role use appropriate nav links
  - handle_logout():
    - Who ever login in the application using either admin/customer when that user press the button logout just redirects -> `/login`

## Phase-9 - Authorization on every request

- ```Every API Request → FRONTEND GATES → Request Interceptor (services/api.js) → Attach JWT as Bearer Token → Send Request to Backend → BACKEND GATES → _load_user (Read JWT sub & Load User) → _resolve_request_user (Compare JWT tv with users.token_version) → auth_required (Validate Authentication & Set g.current_user) → role_required (Check Admin Role if Required) → Endpoint Permission Checks (is_admin / owns_customer / can_view_order) → order_service.visible_orders_for(user) → Admin: Return All Orders | Customer: Return Only Own Orders → Return API Response → FRONTEND RESPONSE INTERCEPTOR → 401: forceLogout('session_expired') → Clear Storage & Redirect to /login | 403 on Role-Guarded Endpoint: forceLogout('role_changed') → Clear Storage & Redirect to /login | Other Errors: Propagate to Caller```

- Every API call passes through two gates in both frontend and backend each:
  - `Frontend gates`:
    - ``service/api.js``:
      - request interceptor:
        - where it caries a token which helps to verify the authorization
      - response interceptor:
        - Authentication - when a session is under status 401 it's a forced logout(-> `/login`)
        - Authorization -  when the status is 403 it will check w.r.t the role-guarded and forced logout when this status was out
    - `Backend gates`:
      - ``utils/decorators.py``:
        - this loads and check:
          - the users against the jwt
          - req_user w.r.t the tv
          - auth_required helps to get the current user
          - role is reuqired
      - ``utils/permission.py``
        - this will do:
          - role check w.r.t the user
          - who owns that particular ID
          - can_view_order w.r.t the users(admin,customer)
  - ``order_service.visible_orders_for(user)``:
    - role:
      - admin -> can view all the order
      - customer -> can view the orders related to that user

## Phase-10 user_flow w.r.t the roles

- Customer flow(`client/src/views/MyOrders.Vue`):

  - ```Open /app/my-orders → Mount MyOrders.vue → onMounted() → fetchOrders() → GET /api/orders?per_page=200 → Backend list_orders() → visible_orders_for(user) → Fetch Customer's Own Orders Only → Return Orders → countByStatus() → Group Orders by Status (Pending / Received / Shipped / Cancelled / Delivered / Returned) → Render Orders List → Customer Clicks an Order → GET /api/orders/:id → permissions.can_view_order() → Order Owned by Customer or User Is Admin? → Yes: Return Order Details | No: Return 404 Not Found (Hide Order Existence)```

  - onMouted():
    - Calls fetchOrders() to fetch orders using `GET /api/orders?per_page=200.`
    - Backend list_orders() calls visible_orders_for(user) to filter orders based on the authenticated user's role:
      - admin: Fetches all orders.
      - customer: Fetches only orders associated with their account.
    - Returns the filtered orders to the frontend.
    - Frontend assigns the response to the orders state and uses countByStatus() to group orders by status for display

- Admin Flow:
  - Orders(`client/src/views/Orders.vue`):
  
    - ```Open /app/orders → Load Orders.vue → fetchOrders() → GET /api/orders (status filter + debounced search q + pagination) → Backend list_orders() → Eager-Load Order Items & Customer (joined_load) → _order_response() (Serialize Order + Computed Total) → Return Orders → Render Orders List → Admin Changes Status → Cancelled/Returned? → Yes: Browser confirm() → Confirmed? → PATCH /api/orders/:id/status → order_service.change_status() → can_transition(ALLOWED_TRANSITIONS) → Valid Transition? → No: Return 400 Error | Yes: Update Status in Database → Return Success → Refresh Orders → summaryStore.fetch(true) (Bypass Cache) → Dashboard Summary Updated```

    - `fetch_Orders()` this function will fetch orders w.r.t the status filters
    - `list_orders` this helps to load the users w.r.t the order responses
    - changeStatus `PATCH /api/orders/:id/status` can change the status and it won't revert once we change the status
    - frontend always refreshes when there is changes in status throughout the application

  - Create_order(`client/src/views/CreateOrder.vue`):
  
    - ```Open /app/orders/new → Mount CreateOrder.vue → onMounted() → GET /api/products (Any Authenticated User) + GET /api/customers (Admin Only) → Load Products & Customers into Form → Admin Submits Order → handleSubmit() → POST /api/orders (One Item) → Backend create_order() → Check Admin Role → order_service.validate_order_payload() → Validate Order ID, Date, Customer, Items, Duplicate Products, Quantity (1–1000) & Product Existence → Fetch Current Product Price from Database (Ignore Client-Sent unit_price) → Validation Passed? → No: Return Validation Error → Yes: Begin Database Transaction → Insert Order Header (Pending) + Order Items → Duplicate order_id? → Yes: Rollback & Return 409 Conflict → Other Failure? → Rollback All Changes → Success? → Commit Transaction → Return 201 Created → Redirect to /app/orders/:id```

    - onMouted():
      - helps to load /products(any-auth) and /customers(admin-auth)
    - handleSubmit():
      - send `POST /api/orders` with one item
    - Backed `orderservice.py::create_order`:
      - to create an order we need admin role
      - it will check in `validate_order_payload()` then the unit price can be changed w.r.t current_price in products
      - then by default it will be inserted as pending then it will redirects to `/app/orders/:id` with 201 status

  - Products(`client/src/views/Products.Vue`):

    - ```Open /app/products → Load Products.vue → fetchProducts() → GET /api/products → Backend Checks Authentication (Any Authenticated User) → Fetch Products & Current Prices → Return Products → Render Product List→ Admin Updates Price → savePrice() → PATCH /api/products/:id → Check Admin Authorization → Update Product Price → Return Success → Refresh Product List→ Admin Creates Product → createProduct() → POST /api/products → Check Admin Authorization → Validate & Insert Product → Return Success → Refresh Product List→ Admin Deletes Product → deleteProduct() → DELETE /api/products/:id → Check Admin Authorization → Product Used in order_items? → Yes: Return 409 Conflict | No: Delete Product → Return Success → Refresh Product List```
  
    - fetchProducts():
      - `GET /api/products` - here any authenticated user can view products.
    - savePrice():
      - `PATCH /api/products/:id` - can update the price only who authorized to that particular patch
    - createProduct():
      - `POST /api/products` - same with the save price but here it is for creating products
    - deleteProduct():
      - `DELETE /api/products/:id` - same with the create product but for deleting the products with 409 status if the deleted product is used

  - Users(`client/src/views/users.vue`):

    - ```Open /app/users → Load Users.vue → fetchUsers() → GET /api/users → Backend Checks Admin Authorization → Fetch & Return Users → Render Users Table→ Admin Creates User → createUser() → POST /api/users → Validate User Details → Create User → Return Success → Refresh User List→ Admin Updates Role → updateUserRole() → PATCH /api/users/role → Check Admin Authorization & Validate Role → Protect Last Admin → Update User Role → Return Success → Refresh User List→ Admin Deletes User → deleteUser() → DELETE /api/users → Check Admin Authorization → Prevent Self-Deletion & Last-Admin Deletion → Delete User → Return Success → Refresh User List```
  
    - fetchUsers():
      - `GET /api/users` - here the authorized user can fetch the users
    - createUser()
      - `POST /api/users` - here we can create users
      - UserRol_update()
        - `PATCH /api/users/role` - can update the role
      - Delete_user()
        - `DELETE /api/users` - can delete the user
  
- Duplicates(/duplicates -> Duplicates.vue):
  
  - ```Open /duplicates → Load Duplicates.vue → load() → GET /api/orders/duplicates → Backend Runs find_duplicates() → Identify & Group DuplicateOrders → Return        Duplicate Groups → Render Duplicates for Review→ Admin Reviews Duplicate Group → Select Copy to Cancel → cancelCopy() → PATCH /api/orders/:id/status → Backend Validates Request & Updates Order Status → Return Success → Refresh Duplicate List```
  
  - load():
    - `GET /api/orders/duplicates` this will helps to load the duplicate orders while finding them using find_duplicates and then will group by
  - cancelCopy():
    - `PATCH /api/orders/:id/status` this will allow us to change the status of the order
- it will always delete after reviewing only

- Reports(/reports,/totals -> Reports.Vue, Totals.Vue):
  - `GET /api/reports/summary` those both are shared under summaryStore.fetch(force)
  - order_service.get_dashboard_summary():
    - it helps to join all the orders,items,products and filters w.r.t the status and returns the respective values
  - and will format via `utils/format.js::money,number,percentage,date`
  - and can view the product-wise and date-wise reports in the dashboard




app = Flask(__name__):
  - this line creates the centralized application object and holds
    - the url mapping
    - app config
    - handle errors
    - loads the templates
    - register the extensions themselves
  - and name will be imports


- in simple words that line creates a flask app and hands it the modules from the which the flask derives

  Practice more and try to remember
  Aggregation function use_cases
  window functions 
  check the proper use_cases like when we use particular keyword

  live dashboard streaming check it!
  like how it done and what will be used
  make sure to identify and get to know proper terminologies and proper naming
  practice more
  f - is used for dynamic data
  - make sure to know why we using particular keywords,functions when you write instead of blind implementation and always keep it simple

- Traceback know why,what and how we do it
  - python
- Git - documentation
- make sure to document everything what you have built
- MQTT use_cases throughout the internet
- D
- eployment 