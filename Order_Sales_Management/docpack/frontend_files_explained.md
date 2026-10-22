# Frontend Files Explained (OrderSalesManagement)

This file explains every frontend source file in `Order_Sales_Management/client/src/`: each line, function, const, template, and scoped CSS role.

All paths are relative to `Order_Sales_Management/client/src/`.

---

## 1. `main.js` — app bootstrap / entry point

Single-file script loaded first by the browser. It wires the three global provider layers so every other Vue file can use them.

- `import { createApp } from 'vue'` — Vue 3 capability to create the application instance.
- `import { createPinia } from 'pinia'` — Pinia state-store factory.
- `import App from './App.vue'` — root component, contains `<router-view />`.
- `import router from './router'` — Vue Router instance with guards and all routes.
- `import './style.css'` — global CSS variables/reset imported at bootstrap, available to every scoped and global style block.
- `const app = createApp(App)` — creates the Vue app from the root component.
- `app.use(createPinia())` — registers Pinia so `useAuthStore()` and `useSummaryStore()` work anywhere.
- `app.use(router)` — registers Vue Router so `<router-view />` renders route-matched components.
- `app.mount('#app')` — attaches the app to `<div id="app">` in `index.html`.
- Role: nothing is rendered here itself; it is the dependency-injection layer for the whole frontend.

---

## 2. `router/index.js` — routing + auth guards

Route table and global navigation guard.

- `import { createRouter, createWebHistory } from 'vue-router'` — router factory and HTML5 history mode.
- `import { useAuthStore } from '@/stores/auth'` — auth store needed by guards.
- `const routes = [ ... ]` — route definitions:
  - `Landing` (`/`) — public homepage.
  - `Login`, `Register`, `ForgotPassword`, `ResetPassword` — public auth screens.
  - `/app` parent route renders `AppLayout.vue` once per dashboard session. `meta: { requiresAuth: true }` marks it protected.
  - Children of `/app`:
    - `''` redirects to `/app/orders` (default).
    - `Orders` — admin order list.
    - `MyOrders` — customer view of own orders.
    - `orders/:id` — detail page; `:id` is the Vue dynamic segment.
    - `products`, `customers`, `reports`, `duplicates`, `new-order`, `users`, `totals` — admin panels; each carries `meta: { requiresAdmin: true }`.
- `const router = createRouter({ history: createWebHistory(), routes })` — builds the router instance.
- `router.beforeEach((to, from, next) => { ... })` — global guard before any navigation:
  - If a protected route is visited and not logged in → `next('/login')`.
  - If an admin route is visited by a customer → `next('/app/orders')`.
  - If `Orders` is opened by a customer → redirect to `/app/my-orders`.
  - If `MyOrders` is opened by an admin → redirect to `/app/orders`.
  - Otherwise `next()` allows the navigation.
- Role: it enforces the UI-side access policy. Real enforcement still lives in the Flask backend.

---

## 3. `services/api.js` — Axios HTTP client

Only HTTP client used by the frontend.

- `import axios from 'axios'` — Axios HTTP library.
- `const api = axios.create({ baseURL: '/api' })` — base URL for all requests; Vite dev proxy forwards `/api` to Flask on `127.0.0.1:5000`.
- `api.interceptors.request.use((config) => { ... })` — runs before each request; reads `localStorage['token']`, attaches `Authorization: Bearer <token>`, and returns the config.
- `api.interceptors.response.use((res) => res, (err) => { ... })` — runs after every response:
  - Success path returns the response unchanged.
  - Error path: if status is `401` or `422`, removes stale `token` and `user` from `localStorage` and redirects to `/login` unless already on the login page.
  - Always `return Promise.reject(err)` so calling views can catch and show a message.
- Role: injects the JWT into every request and turns auth failures into a logout redirect.

---

## 4. `stores/auth.js` — authentication state

Pinia store for login state and reload-with-auth state.

- `import { defineStore } from 'pinia'` — Pinia store factory.
- `import api from '@/services/api'` — used to call `/auth/login` and `/auth/me`.
- `export const useAuthStore = defineStore('auth', { ... })` — named store.
- `state: () => ({ token: localStorage.getItem('token') || null, user: JSON.parse(localStorage.getItem('user')) || null })`:
  - `token` is the raw JWT.
  - `user` is the parsed user object from `localStorage`.
  - Values survive a page refresh by reading `localStorage` at startup.
- `getters: { isAuthenticated: (state) => !!state.token, isAdmin: (state) => state.user?.role === 'admin' }`:
  - `isAuthenticated` is used by the router guard and the layout.
  - `isAdmin` is used by the router guard and the layout menu.
- `actions: { async login(email, password) { ... } }`:
  - POSTs `/auth/login` with email/password.
  - Stores `res.data.access_token` in `token` and the full user object in `user`.
  - Persists both into `localStorage`.
- `async fetchMe() { ... }`:
  - If there is no token it returns early.
  - GETs `/auth/me` and replaces the local `user` with the fresh server profile.
  - The `try/catch` is empty on purpose: a fetch failure is not fatal; the app keeps its cached identity.
- `logout() { ... }`:
  - Resets `token` and `user` to null.
  - Removes both items from `localStorage`.
- Role: single place where login/logout/refresh user identity happen.

---

## 5. `stores/summary.js` — report dashboard state

Pinia store holding the admin dashboard payload.

- `import { defineStore } from 'pinia'` and `import api from '@/services/api'`.
- `export const useSummaryStore = defineStore('summary', { ... })`.
- `state: () => ({ data: null, loading: false, error: '' })`:
  - `data` stores the API response object from `/reports/summary`.
  - `loading` prevents duplicate fetch calls.
  - `error` holds a user-facing message.
- `actions: { async fetch(force = false) { ... } }`:
  - If `data` exists and `force !== true`, returns immediately (caching).
  - If a fetch is already running, returns immediately.
  - Sets `loading = true`, clears `error`.
  - GETs `/reports/summary`.
  - On success, assigns `this.data = res.data`.
  - On catch, sets `this.error = 'Failed to load totals.'`.
  - Finally resets `loading = false`.
- Role: caching + refresh for the dashboard summary by all report views.

---

## 6. `utils/format.js` — formatting helpers

Pure helper functions reused across views and in `Reports`, `Totals`, `MyOrders`, etc.

- `export const money(value, digits = 2)`:
  - `const amount = Number(value || 0)` — turns null/undefined/empty into `0`.
  - Returns `₹<amount.toLocaleString('en-IN')>` with fixed fractional digits, so `5000` becomes `₹5,000.00`.
- `export const number(value)`:
  - Returns `Number(value || 0).toLocaleString('en-IN')`.
- `export const percent(part, whole)`:
  - Returns `0` when `whole` is falsy, avoiding division by zero.
- `export const percentLabel(part, whole)`:
  - Returns `percent(...).toFixed(1) + '%'`.
- `export const formatDate(iso)`:
  - Returns `—` for missing/invalid dates.
  - Parses ISO into a date and renders in `en-GB` format (`16 Oct 2026`).
- `export const initials(name)`:
  - Splits on spaces, takes the first letter of up to two words, uppercases, and joins; returns `?` when empty.
- Role: shared formatting, no Vue, no HTTP.

---

## 7. `style.css` — global styles

- `@import url(...Inter...)` — loads `Inter Tight` and `Inter` fonts from Google Fonts.
- `:root { ... }`:
  - Color tokens: `--bg-app`, `--bg-card`, `--ink`, `--text-primary`, `--text-secondary`, `--line`, `--line-strong`, colors such as `--lime`, `--blue`, `--orange`, `--cream`, `--mint`, `--lavender`, `--pink`, `--red`, `--teal`, `--yellow`.
  - Spacing/radius/shadow tokens: `--radius-card`, `--radius-md`, `--radius-pill`, `--shadow-card`, `--shadow-float`.
- Universal reset (`*`, `html, body, #app`) and focus-visible outlines for accessibility.
- Base `.card`, `.btn` and modifier classes (`btn-primary`, `btn-dark`, `btn-lime`, `btn-ghost`, `btn-outline-red`, `btn-sm`), `.input`, `.status-pill` variants, `.table`, `.scroll-x`, `.error-banner`, `.success-banner`, `.empty-state`, `.spinner-state`, `.avatar`, and scrollbar styling.
- Role: design tokens + reusable base styles used by every component's scoped CSS.

---

## 8. `vite.config.js` — Vite build configuration

- `import { defineConfig } from 'vite'`, `import vue from '@vitejs/plugin-vue'`, `import path from 'node:path'`, `import { fileURLToPath } from 'node:url'`.
- `const __dirname = path.dirname(fileURLToPath(import.meta.url))` — gets the directory of this config.
- `export default defineConfig({ plugins: [vue()], resolve: { alias: { '@': path.resolve(__dirname, './src') } }, server: { proxy: { '/api': 'http://127.0.0.1:5000', '/db': 'http://127.0.0.1:5000' } } })`:
  - `plugins: [vue()]` compiles `.vue` Single-File Components.
  - `alias '@'` maps `@@/stores` imports to `client/src/...`.
  - `server.proxy` forwards `/api` and `/db` requests to the Flask backend, so the browser never needs a real backend host.
- Role: dev-server proxy + path alias.

---

---

# Views

## 1. `views/Landing.vue`

Public marketing/home page.

- `<script setup>` imports `computed`, `useRouter`, `useAuthStore`, `Icon`.
- `const startPath = computed(() => auth.isAuthenticated ? (auth.isAdmin ? '/app/reports' : '/app/my-orders') : '/login')` — redirects a logged-in user to their own dashboard.
- `const bars = [40, 52, 36, 72, 60, 66, 30, 84, 58, 44, 48, 70, 38, 62]` — static bar heights for the live-preview chart.
- `<template>` renders:
  - `topbar`: brand link + `Sign in` / `Get started` buttons.
  - `hero-grid`: hero message + `Go to app` / `Create an account` buttons; `startPath` is the hero CTA target.
  - `side-column`: two stat cards — a live-preview bar chart and an `Awaiting action` counter.
  - `feature-grid`: three feature cards — order workflow, server pricing (`total = quantity × locked price`), and duplicate alerts.
  - `landing-footer`: stack label `Vue.js · Flask · PostgreSQL`.
- Scoped CSS controls the hero, stat cards, bar chart, feature grid, breakpoints, and footer.
- Role: public marketing page; no API calls, no auth-dependent data.

---

## 2. `views/Login.vue`

Public login screen.

- Script setup:
  - Imports `ref`, `useAuthStore`, `useRoute`, `useRouter`, `AuthShell`.
  - `const email = ref('')`, `const password = ref('')` — form fields.
  - `const errorMsg = ref('')`, `const submitting = ref(false)` — UI state.
  - `const auth = useAuthStore()`, `const router = useRouter()`, `const route = useRoute()`.
- `const handleLogin = async () => { ... }` — form submit:
  - Clears `errorMsg`, sets `submitting`.
  - `await auth.login(email, password)`.
  - Success: `router.push(auth.isAdmin ? '/app/reports' : '/app/my-orders')`.
  - Fail: sets `errorMsg.value = err.response?.data?.error || 'Login failed'`.
  - Always resets `submitting`.
- Template:
  - `AuthShell` wrapper for the public layout.
  - `route.query.reset === 'success'` shows a success banner after password reset.
  - `errorMsg` rendered as an alert banner.
  - Form fields bound to `email` and `password` with `autocomplete`.
  - Submit button shows `Signing in…` while submitting.
  - Link to `Forgot password?` and `Create an account`.
  - Back link to `/`.
- Scoped CSS: title, auth form, buttons, links.
- Role: converts email + password into an authenticated session.

---

## 3. `views/Register.vue`

Registration split into two steps.

- `<script setup>`:
  - Imports `computed`, `ref`, `useRouter`, `api`, `AuthShell`, `Icon`.
  - `const step = ref(1)` — `1` = details, `2` = verify.
  - `const form = ref({ email: '', password: '', full_name: '', customer_id: '' })`.
  - `const code = ref('')`.
  - `const steps = ['Details', 'Verify email']`, `const activeStep = computed(() => step.value)`.
- `const handleRegister = async () => { ... }` — step 1:
  - POSTs `/auth/register` with `form.value`.
  - On success: `step.value = 2` and shows the OTP message.
  - On fail: shows backend `error.message`.
- `const handleVerify = async () => { ... }` — step 2:
  - POSTs to `/auth/verify` with `email`, `code`, `customer_id`.
  - On success: redirects to `/login`.
- `const handleResend = async () => { ... }`:
  - POSTs `/auth/resend-verification` with the email.
  - Shows `A new 6-digit code has been sent.`
- `const backToDetails = () => { ... }`: resets to step 1.
- Template:
  - `AuthShell` with dynamic heading, accent, subtitle, and steps.
  - Step 1: form for full name, email, password (with `minlength="8"`), customer ID.
  - Step 2: 6-digit OTP input with `maxlength`, `pattern`, and resend button.
  - Back/switch links.
- Scoped CSS styles the two-step layout, OTP input, and banners.
- Role: creates an unverified account and then verifies it with a 6-digit OTP.

---

## 4. `views/ForgotPassword.vue`

Password-reset request screen.

- Script setup: `ref`, `api`, `AuthShell`.
- `const email = ref('')`, `const message = ref('')`, `const errorMsg = ref('')`, `const submitting = ref(false)`.
- `const handleSubmit = async () => { ... }`:
  - POSTs `/auth/forgot-password` with `{ email }`.
  - On success, shows a message describing how to use the reset link.
  - On fail, shows backend error.
- Template:
  - `AuthShell` with heading, accent, subtitle.
  - A form with an email field.
  - After success, shows a `sent-note` with the next step.
  - Back link to `/login`.
- Scoped CSS: form, success note, banners.
- Role: performs a password-reset request without revealing whether the email exists.

---

## 5. `views/ResetPassword.vue`

Reset the password using a token.

- Script setup: `ref`, `useRoute`, `useRouter`, `api`, `AuthShell`.
- `const route = useRoute()`, `const token = route.query.token || ''` — token from URL, e.g. `/reset-password?token=...`.
- `const password = ref('')`, `const errorMsg = ref('')`, `const submitting = ref(false)`.
- `const handleSubmit = async () => { ... }`:
  - POSTs `/auth/reset-password` with `{ token, new_password }`.
  - On success, redirects to `/login?reset=success`.
- Template:
  - `AuthShell` with heading and subtitle.
  - If `token` is missing: shows an alert banner with a link to request a new link.
  - If `token` exists: form with a password field (`minlength="8"`).
  - Back links to `forgot-password` or `login`.
- Scoped CSS: form, banners.
- Role: performs a single-use, expiry-checked password reset.

---

## 6. `views/MyOrders.vue`

Customer-only orders view.

- Script setup:
  - Imports `computed`, `onMounted`, `ref`, `useRouter`, `api`, `useAuthStore`, and format helpers.
  - `const STATUSES = ['Pending', 'Received', 'Shipped', 'Delivered', 'Cancelled', 'Returned']`.
  - `const orders = ref([])`, `const loading`, `const errorMsg`, `const statusFilter`.
  - `const customerId = computed(() => auth.user?.customer_id || null)`.
  - `const firstName = computed(() => auth.user?.full_name?.split(' ')[0] || 'there')`.
- Computed:
  - `filteredOrders`: filtered by `statusFilter`.
  - `countByStatus(status)`: local count of each status.
  - `deliveredShare`, `inTransitShare`, `spent` — percentage/currency summaries.
  - `distribution`: array of `{ status, count, share, tone }` for the bar/legend.
- `const fetchOrders = async () => { ... }`:
  - Calls `auth.fetchMe()` first.
  - GETs `/orders` with `{ params: { per_page: 200 } }`.
  - Stores the returned orders (backend enforces customer-only visibility).
- `onMounted(fetchOrders)`.
- Template:
  - Page header with the user’s first name and a note about their customer ID.
  - Stats cards: delivered share, total orders, still-on-its-way share, and spent amount.
  - Bar chart and legend for distribution.
  - Orders table: order ID, date, status pill, items count, total.
  - Empty states for no orders and no matching status.
- Scoped CSS: stats grid, stat cards, distribution bars, table.
- Role: lets a customer browse and see only their own orders.

---

## 7. `views/Orders.vue`

Admin order list with tiles, filters, pagination, and status updates.

- Script setup:
  - Imports `computed`, `onMounted`, `ref`, `watch`, `useRoute`, `useRouter`, `api`, `useSummaryStore`, `useAuthStore`, `format` helpers, `Icon`.
  - `const STATUSES = ['Pending', 'Received', 'Shipped', 'Delivered', 'Cancelled', 'Returned']`.
  - `const ACTIONS = { ... }` — allowed next actions per current status (e.g. `Pending` can go to `Received`, `Shipped`, `Cancelled`).
  - `const orders = ref([])`, `const loading`, `const errorMsg`, `const total`, `const pages`, `const page`, `const statusFilter`, `const search`, `const updatingId`.
- Computed:
  - `summary`, `totalOrders`, `statusCounts` — from `summaryStore`.
  - `tiles` — array of tiles for the `All orders`, `Pending`, …, `Returned` summary.
- `const fetchOrders = async () => { ... }`:
  - Builds params: `page`, `per_page: 10`, optional `status`, optional `q` search.
  - GETs `/orders`.
  - Updates `orders`, `total`, `pages`.
  - Syncs the URL query with the current filter using `router.replace({ query: params2 })`.
- `const selectStatus(status)` — sets the filter and resets to page 1.
- `const onSearch()` — debounced search: clears the old timer, then fetches on page 1 after 300 ms.
- `const changeStatus(order, nextStatus)` — allowed transition handler:
  - Guards `updatingId`.
  - Confirms destructive actions (`Returned`/`Cancelled`) via `window.confirm`.
  - PATCHes `/orders/<order_id>/status` with `{ order_status }`.
  - Updates the local row and refreshes the summary.
- `watch(total, ...)` — if the filtered list empties while pagination is beyond page 1, resets to page 1 and refetches.
- `onMounted(async () => await Promise.all([summaryStore.fetch(), fetchOrders()]))`.
- Template:
  - Header with a `New order` button routing to `/app/new-order`.
  - Scrollable tiles for each status with the count and share.
  - Table with `Order ID`, `Customer`, `Date`, `Status`, `Items`, `Total`, and action buttons (`Receive`, `Ship`, `Cancel`, `Deliver`, `Return`).
  - Status pill classes match `status-pill.<status>`.
  - Pagination and empty/filter states.
  - Debounced search, client-side filter select, and server-side pagination.
- Scoped CSS: tiles, table, search, pagination, responsive grids.
- Role: full order management UI.

---

## 8. `views/CreateOrder.vue`

Admin order-creation form.

- Script setup:
  - Imports `computed`, `onMounted`, `ref`, `useRouter`, `api`, `money` helper.
  - `const products = ref([])`, `const customers = ref([])` — dropdowns.
  - `const form = ref({ order_id: '', customer_id: '', order_date: today, product_id: '', quantity: 1 })`.
  - `const customerSearch = ref('')` — search box.
  - `const selectedProduct = computed(() => products.find(p => p.product_id === form.value.product_id))`.
  - `const filteredCustomers` — filters customers by name, ID, or email (max 50).
  - `const lineTotal = computed(() => selectedProduct?.current_price * quantity)` — preview only.
- `onMounted(async () => { ... })`:
  - In parallel, GETs `/products` and `/customers`.
  - Prefills `product_id` and `customer_id` when available.
- `const handleSubmit = async () => { ... }`:
  - Builds payload with `order_id` (uppercased), `customer_id`, `order_date`, `items: [{ product_id, quantity }]`.
  - POSTs `/orders`.
  - On success, redirects to the new order detail page.
  - On fail, shows errors from `err.response.data.errors` or the generic `error`.
- Template:
  - Header: `Create order`.
  - Loading state while the products/customers dropdowns load.
  - Form: order ID (`ORD####`), customer search + select, order date, product select, quantity.
  - `pattern="ORD\d{4}"` enforces the format client-side.
  - Sidebar preview: `lineTotal` and validation note (server-side pricing).
- Scoped CSS: card layout, form fields, preview card, response.
- Role: creates a new order with server-side price locking.

---

## 9. `views/OrderDetail.vue`

Read-only order detail with status transition UI.

- Script setup:
  - Imports `computed`, `onMounted`, `ref`, `useRoute`, `useRouter`, `api`, `useAuthStore`, `useSummaryStore`, `format` helpers, `Icon`.
  - `const PROGRESS = ['Pending', 'Received', 'Shipped', 'Delivered']` — progress visualization.
  - `const allowedTransitions = { Pending: ['Received', 'Shipped', 'Cancelled'], Received: ['Shipped', 'Cancelled'], Shipped: ['Delivered', 'Returned'], Delivered: ['Returned'], Cancelled: [], Returned: [] }`.
  - `const order = ref(null)`, `const loading`, `const errorMsg`, `const updating`.
- Computed:
  - `nextStatuses`: derived from `allowedTransitions[order.order_status]`.
  - `progressIndex`: current step in `PROGRESS`.
  - `revenueShare`: order total divided by dashboard revenue.
  - `itemCount`: total quantity across items.
- `const fetchOrder = async () => { ... }`:
  - GETs `/orders/<route.params.id>`.
  - Maps a `404` to a friendly message.
- `const updateStatus = async (newStatus) => { ... }`:
  - PATCHes `/orders/<order_id>/status`.
  - Updates the local order status and refreshes the summary.
- `const backTarget = computed(() => auth.isAdmin ? '/app/orders' : '/app/my-orders')`.
- `onMounted(() => { if (auth.isAdmin) summaryStore.fetch(); fetchOrder(); })`.
- Template:
  - Back link, page header with avatar.
  - Loading, error, and order-not-found states.
  - Progress bar and labels when the order is in a transitionable state; a terminal note otherwise.
  - Status action buttons limited to `allowedTransitions` (no invalid buttons).
  - Line items table with product, quantity, unit price, line total.
  - Total row.
  - Sidebar: order total and revenue share (admin only), or item count for customer.
  - Customer card with name, linked-account status, and email.
- Scoped CSS: layout grid, progress, cards, table, responsive columns.
- Role: single-order view with a UI-level state machine.

---

## 10. `views/Reports.vue`

Admin sales-dashboard page.

- Script setup:
  - Imports `computed`, `onMounted`, `ref`, `useRouter`, `api`, `useAuthStore`, `useSummaryStore`, `format` helpers, `Icon`.
  - `const summary = computed(() => summaryStore.data || {})`, `const totalOrders`, `const firstName`, `const greeting`.
  - `const chartOptions = ref({ chart: { type: 'area', height: 300, toolbar: { show: false } }, colors: ['#2f5bff'], stroke: { curve: 'smooth', width: 3 }, fill: { type: 'gradient', ... }, xaxis: { categories: [], ... }, grid: {...}, dataLabels: { enabled: false } })`.
  - `const chartSeries = ref([{ name: 'Revenue', data: [] }])`.
  - `const duplicates = computed(() => summary.value.duplicate_groups || [])`.
- `onMounted(async () => { ... })`:
  - Fetches summary with `force = true`.
  - Takes the last 12 monthly rows and maps them to chart categories and series data.
- Template:
  - Header with greeting.
  - Loading state.
  - KPI cards: revenue, sales orders %, units sold, awaiting action %.
  - Full-width area chart for revenue over time.
  - Latest orders table and a duplicate-alert card.
  - `v-for` over `summary.latest_orders` and `duplicates.slice(0, 2)`.
  - A button to `/app/duplicates`.
- Scoped CSS: grid layout, KPI cards, chart card, table, duplicate card.
- Role: summary dashboard consumed from the Flask `/reports/summary` endpoint.

---

## 11. `views/Customers.vue`

Admin customer list with create/link actions.

- Script setup:
  - Imports `computed`, `onMounted`, `ref`, `api`, format helpers.
  - `const customers = ref([])`, `const loading`, `const errorMsg`, `const successMsg`.
  - `const showCreate`, `const saving`.
  - `const newCustomer = ref({ customer_id: '', cust_name: '', email: '' })`.
  - `const search = ref('')`, `const linkingCustomer`, `const targetUserId`.
- Computed:
  - `filtered`: searches customer_id, cust_name, email (case-insensitive).
  - `linked`: customers with `user_id`.
  - `linkedShare`, `unlinkedShare`: percentages.
- `const fetchCustomers = async () => { ... }`:
  - GETs `/customers`.
- `const createCustomer = async () => { ... }`:
  - POSTs `/customers` with `newCustomer.value`.
  - Clears the form and refreshes the list on success.
- `const startLink(customer)` — opens the link row.
- `const submitLink = async () => { ... }`:
  - PATCHes `/customers/<customer_id>/link` with `{ user_id }`.
  - Refreshes the list.
- `onMounted(() => { window.addEventListener('open-create-form', ...) })`.
- Template:
  - Header with `+ New customer` button.
  - Stats: total customers, linked %, unlinked %.
  - Inline create bar with customer ID, name, email.
  - Link bar (lavender) for the selected customer with a User ID input.
  - Search box and customer table: ID, name, email, linked user pill or Link button.
  - Max 100 rows shown; `filtered.slice(0, 100)`.
- Scoped CSS: stats, create bars, search, table.
- Role: admin-side customer catalog plus account linking.

---

## 12. `views/Products.vue`

Admin product catalog.

- Script setup:
  - Imports `computed`, `onMounted`, `ref`, `api`, `useSummaryStore`, `money`, `percent`.
  - `const summaryStore = useSummaryStore()`.
  - `const products = ref([])`, `const loading`, `const errorMsg`, `const successMsg`.
  - `const editId`, `const editPrice`, `const showCreate`, `const saving`.
  - `const newProduct = ref({ pro_name: '', current_price: null })`.
  - `const COLORS = ['#2f5bff', '#c7f53c', '#ff7a45', '#2bb6a3', '#8b8cf7', '#f4c542', '#94a3b8']`.
- Computed:
  - `salesIndex`: maps product name to its sales row from the summary.
  - `cards`: product list enriched with `units`, `share`, and `color`.
- `const fetchProducts = async () => { ... }`:
  - GETs `/products`.
- `const startEdit(product)` — opens the edit-price row.
- `const savePrice = async (id) => { ... }`:
  - PATCHes `/products/<id>` with `{ current_price }`.
  - Refreshes the list.
- `const createProduct = async () => { ... }`:
  - POSTs `/products`.
- `const deleteProduct = async (product) => { ... }`:
  - Deletes after a confirm dialog; backend blocks deletion while the product is used in orders.
- `onMounted(() => { window.addEventListener('open-create-form', ...); summaryStore.fetch(); fetchProducts(); })`.
- Template:
  - Header with `+ New product`.
  - Inline creation bar.
  - Product grid of cards: tag with product ID, share badge, name, price, bar chart of revenue share, units sold, and actions (Edit price / Delete).
  - Loading and empty states.
- Scoped CSS: responsive grid, badge, price, action buttons.
- Role: catalog management with server-side pricing updates.

---

## 13. `views/Duplicates.vue`

Admin duplicate-investigation page.

- Script setup:
  - Imports `computed`, `onMounted`, `ref`, `useRouter`, `api`, `useSummaryStore`, format helpers.
  - `const duplicates = ref([])`, `const loading`, `const errorMsg`, `const successMsg`.
  - `const cancelling = ref('')`.
  - `const totalOrders = computed(() => summaryStore.data?.total_orders || 0)`.
  - `const involvedOrders`, `duplicateShare`, `valueAtRisk`, `uniqueOrders`.
- `const orderStatus(orderId)` — finds the order status from the dashboard's latest orders.
- `const cancelCopy = async (group) => { ... }`:
  - Confirms the action.
  - PATCHes `/orders/<target>/status` with `order_status: 'Cancelled'`.
  - Refreshes the duplicates list.
- `const load = async () => { ... }`:
  - GETs `/orders/duplicates` and refetches the summary.
- `onMounted(load)`.
- Template:
  - Header and stats: groups flagged, share of all orders, value at risk.
  - Loading state.
  - Group cards with customer, product, quantity, price, date, and all order IDs as clickable chips.
  - Action row with note and Cancel button (disabled while cancelling).
- Scoped CSS: stats, group cards, chips, alerts.
- Role: surfaces and lets admins act on duplicate order groups.

---

## 14. `views/Users.vue`

Admin user list.

- Script setup:
  - Imports `computed`, `onMounted`, `ref`, `api`, format helpers.
  - `const users = ref([])`, `const loading`, `const errorMsg`, `const successMsg`.
  - `const showCreate`, `const saving`, `const newUser = ref({ email: '', password: '', full_name: '', role: 'customer' })`.
  - `const admins`, `const unverified`, `const customers` — derived counts.
- `const fetchUsers = async () => { ... }`:
  - GETs `/users`.
- `const createUser = async () => { ... }`:
  - POSTs `/users`.
- `onMounted(fetchUsers)`.
- Template:
  - Header with `+ New user`.
  - Create bar with email, password, full name, and role select.
  - Stats: registered users, admin percentage, unverified percentage.
  - Users table: ID, name + avatar, email, role pill, status text (verified/unverified).
  - Loading and empty states.
- Scoped CSS: stats, create bar, table, role pills, status pills.
- Role: admin account management (with backend role/control checks).

---

## 15. `views/Totals.vue`

Full-lifetime totals report view.

- Script setup:
  - Imports `computed`, `onMounted`, `ref`, `vue`, `useSummaryStore`, format helpers, `Icon`.
  - `const summaryStore = useSummaryStore()`, `const loading = ref(true)`.
  - `const summary = computed(() => summaryStore.data || {})`.
  - `const totalOrders = computed(() => summary.value.total_orders || 0)`.
  - `const products`: product breakdown with `share`.
  - `const statusRows`: stable ordered status list with counts and shares.
- `onMounted(async () => { await summaryStore.fetch(true); loading.value = false })`.
- Template:
  - Hero revenue card: total lifetime revenue, total orders, units sold, average order value.
  - Two-column layout: top products table (with share bars) and order status breakdown bars.
  - Uses `percent()` to avoid division by zero.
  - All numbers are formatted with `money()` / `number()` / `percent()`.
- Scoped CSS: hero card, grid, table, status bars.
- Role: readable admin summary of totals.

---

## 16. `components/Icon.vue`

Inline SVG icon renderer.

- `<script setup>`:
  - `const props = defineProps({ name: { type: String, required: true }, size: { type: [Number, String], default: 20 }, strokeWidth: { type: [Number, String], default: 2 } })`.
  - `const paths = { ... }` — dictionary of SVG path `d` commands for `layers`, `dashboard`, `orders`, `products`, `customers`, `users`, `duplicates`, `logout`, `arrowLeft`, `arrowRight`, `lock`, `alert`, `check`, `plus`, `download`, `mail`.
  - `const path = computed(() => paths[props.name] || '')`.
- Template:
  - `<svg :width="size" :height="size" viewBox="0 0 24 24" fill="none" stroke="currentColor" :stroke-width="strokeWidth" ...>` with `<g v-html="path"></g>`.
- Role: reusable icon by name.

---

## 17. `components/AuthShell.vue`

Public auth layout wrapper.

- `<script setup>` imports `Icon`.
- Template:
  - `.auth-layout` with centered `.auth-card`.
  - Brand link (OrderSync mark + name) and a `<slot />` for each page.
- Scoped CSS: layout, card, brand mark, font scale.
- Role: identical public auth layout for Login, Register, ForgotPassword, ResetPassword.

---

## 18. `layouts/AppLayout.vue`

Dashboard shell.

- Script setup:
  - Imports `onMounted`, `useRouter`, `useRoute`, `useAuthStore`, `Icon`.
- `const links = [ ... ]` — nav items with `admin` and `customerOnly` flags; `MyOrders` is customer-only, everything else is admin.
- `const visibleLinks = () => links.filter((link) => auth.isAdmin ? link.admin : link.customerOnly)`.
- `const handleLogout = () => { auth.logout(); router.replace('/login') }`.
- `onMounted(() => { auth.fetchMe() })` — refreshes identity on load.
- Template:
  - Sticky top nav with brand, nav links for visible links, user profile with role badge and first-letter avatar, and logout button.
  - `<main class="app-main"> <router-view /> </main>`.
- Scoped CSS: sticky nav, active link states, responsive collapse below 1100 px.
- Role: shared dashboard chrome; hides admin links to non-admin users.

---

## 19. `utils/format.js`

Already described above under "global utilities".

---

## 20. `style.css`

Global styles; already described above.

---

## 21. `vite.config.js`

Already described above.

---

# Summary of the frontend

- **Entry:** `main.js` creates the Vue app, registers Pinia and Vue Router, and mounts `#app`.
- **Routing:** Vue Router with route-level `requiresAuth` / `requiresAdmin` flags plus a global `beforeEach` guard.
- **HTTP:** Axios `api.js` automatically attaches the JWT and redirects 401/422 to `/login`.
- **State:** Pinia stores `auth.js` (token, user) and `summary.js` (dashboard totals).
- **Pages:** public auth screens (`Login`, `Register`, `ForgotPassword`, `ResetPassword`), `Landing`, and dashboard screens (`MyOrders`, `Orders`, `CreateOrder`, `OrderDetail`, `Reports`, `Customers`, `Products`, `Duplicates`, `Users`, `Totals`).
- **Components:** reusable `Icon`, public `AuthShell`, and dashboard `AppLayout`.
- **Utilities:** `format.js` for money/percent/date; global `style.css`; `vite.config.js` proxy and alias.

---

# Endpoints Explained (OrderSalesManagement)

All paths are relative to the Flask app. `base_url = http://127.0.0.1:5000` (Vite proxies `/api` to the Flask server). Every JSON body is `application/json`. Auth uses `Authorization: Bearer <JWT>`.

---

## Auth endpoints (`/api/auth/*`)

### 1. `POST /api/auth/register`

- **Purpose:** Register a new customer account. Public.
- **Request:** JSON `{ email, password, full_name?, customer_id? }`.
- **Behavior:**
  - Normalizes email (trim + lowercase).
  - Validates email and password (8–72 bytes).
  - Requires a valid existing customer ID.
  - Rejects duplicate emails (case-insensitive).
  - Generates a 6-digit OTP, stores its SHA-256 hash with a 2-minute expiry, and emails it to the user (dev: writes to `server/logs/dev_emails.log`).
  - Creates `User` with `role='customer'`, `is_verified=FALSE`, `token_version=0`.
- **Success (201):**
  - `{ message: 'Verification code sent', user_id, email, is_verified: false }`
- **Client errors (400):**
  - `{ error: '...' }` for invalid email, short password, unknown customer ID, email/cust match failure, or duplicate email.

### 2. `POST /api/auth/verify`

- **Purpose:** Verify email OTP and optionally link a customer record. Public.
- **Request:** `{ email, code, customer_id? }`.
- **Behavior:**
  - Finds the user by lowercased email.
  - Rejects already-verified, expired, missing, or invalid codes; limits attempts and gives remaining-count feedback.
  - On success: marks verified, clears the OTP fields.
  - If `customer_id` is supplied, uses `link_customer()`; on failure, returns 409.
- **Success (200):** `{ message: 'Email verified', user_id, is_verified: true }`.
- **Client errors (400):** `{ error: 'Invalid code'/'Code expired'/'Too many attempts...'/... }` or 409 for link failure.

### 3. `POST /api/auth/resend-verification`

- **Purpose:** Resend a verification code. Public (unsafe-lookup protected: returns 200 for unknown emails).
- **Request:** `{ email }`.
- **Behavior:**
  - Finds the user; if unknown or already verified, returns 200.
  - Issues a new OTP with a fresh expiry and sends it.
- **Success (200):** `{ message: 'If the email needs verification, a new code was sent' }`.

### 4. `POST /api/auth/login`

- **Purpose:** Authenticate and receive a JWT. Public.
- **Request:** `{ email, password }`.
- **Behavior:**
  - Returns a generic `401` for missing/invalid credentials.
  - Rejects unverified accounts with a 401.
  - On success, creates a JWT with `identity=user.id` and claims `role`, `email`, `tv = token_version`.
- **Success (200):**
  - `{ access_token, user: { id, email, full_name, role, is_verified, customer_id } }`
- **Client errors (401):** `{ error: 'Email and password are required'/'Invalid credentials'/'Please verify your email first' }`.

### 5. `POST /api/auth/forgot-password`

- **Purpose:** Request a password-reset link. Public.
- **Request:** `{ email }`.
- **Behavior:**
  - If the user exists, generates a random reset token, stores its SHA-256 hash with a 1-hour expiry, and emails the link.
- **Success (200):** `{ message: 'If the email exists, a reset link was sent' }` — identical for unknown emails.
- **Client errors (400):** `{ error: 'Email is required' }`.

### 6. `POST /api/auth/reset-password`

- **Purpose:** Reset a password using a one-time token. Public.
- **Request:** `{ token, new_password }`.
- **Behavior:**
  - Finds the user by hashed token; rejects unknown/expired tokens.
  - Validates the new password.
  - On success, replaces the password hash, clears reset token state, resets verification state, and increments `token_version` (invalidates old JWTs).
- **Success (200):** `{ message: 'Password reset successful' }`.
- **Client errors (400):** `{ error: 'Token is required'/'Token expired'/'Password must be at least 8 characters'/... }`.

### 7. `GET /api/auth/me`

- **Purpose:** Current authenticated user. Requires `auth_required`.
- **Response (200):**
  - `{ id, email, full_name, role, is_verified, customer_id, customer? }` — with `customer` containing `customer_id`, `cust_name` when linked.
- **Client errors:** 401 unauthenticated/malformed/expired token.

---

## Customer/catalog endpoints (`/api/customers`, `/api/products`)

### 8. `GET /api/customers`

- **Purpose:** List customers. Admin only.
- **Response (200):**
  - `{ customers: [ { customer_id, user_id, cust_name, email }, ... ] }`
- **Client errors:** 403 for non-admin.

### 9. `POST /api/customers`

- **Purpose:** Create a customer record. Admin only.
- **Request:** `{ customer_id, cust_name, email? }`.
- **Behavior:**
  - `customer_id` uppercased; `email` lowercased or `null`.
- **Success (201):** `{ customer: { customer_id, user_id, cust_name, email } }`.
- **Client errors (400/409):** `customer_id` or `cust_name` missing; duplicate customer ID.

### 10. `PATCH /api/customers/<customer_id>/link`

- **Purpose:** Link a customer to a user. Admin only.
- **Request:** `{ user_id }`.
- **Behavior:**
  - Rejects missing/`user_id`, non-existent customer or user.
  - Rejects a customer already linked to another user.
  - On success, sets `cust.user_id`, copies email/full name from the user if empty.
- **Success (200):** `{ message: 'Customer linked successfully', customer: { customer_id, user_id, cust_name, email } }`.
- **Client errors (400/404/409)** as above.

### 11. `GET /api/products`

- **Purpose:** Product catalog for dropdowns. Authenticated (any role).
- **Response (200):** `{ products: [ { product_id, pro_name, current_price }, ... ] }`.

### 12. `POST /api/products`

- **Purpose:** Create a product. Admin only.
- **Request:** `{ pro_name, current_price }`.
- **Success (201):** `{ product: { product_id, pro_name, current_price } }`.
- **Client errors (400/409):** missing name, negative price, duplicate product name.

### 13. `PATCH /api/products/<id>`

- **Purpose:** Update a product’s price. Admin only.
- **Request:** `{ current_price }`.
- **Success (200):** `{ message: 'Price updated', product }`.
- **Client errors (400/404):** invalid price or missing product.

### 14. `DELETE /api/products/<id>`

- **Purpose:** Delete a product. Admin only.
- **Success (200):** `{ message: 'Product deleted' }`.
- **Client errors (404/409):** missing product, or product already used in orders (cannot delete while referenced).

---

## Orders endpoints (`/api/orders/*`)

All order creation, retrieval, and status transitions. The creation endpoint requires admin; most read endpoints accept any authenticated user, with backend-enforced visibility.

### 15. `POST /api/orders`

- **Purpose:** Create an order with line items. Admin only.
- **Request:**
  ```json
  {
    "order_id": "ORD1234",
    "customer_id": "C5678",
    "order_date": "2026-10-21",
    "items": [
      { "product_id": 7, "quantity": 2 }
    ]
  }
  ```
  (Client can also send `order_status` or per-item `unit_price`, but the server ignores them.)
- **Behavior:**
  - Server-side validation: `order_id` matches `ORD####`, `customer_id` matches `C####`, customer exists, at least one item, valid quantity (integer 1..1000), product exists and has a price set, no duplicate product per order, status allowable.
  - Creates the order header as `Pending` and inserts order items using the product’s server-side `current_price` as `unit_price`.
  - Returns 409 if the order ID already exists.
  - Rollback on DB failure; generic 400 on unexpected errors.
- **Success (201):**
  - `{ order_id, customer_id, order_date, order_status, items: [ { order_item_id, product_id, product_name, quantity, unit_price, line_total } ], total, item_count, customer? }`
- **Client errors (400/409):** validation errors array or 409 for duplicate order ID.

### 16. `GET /api/orders`

- **Purpose:** List orders. Any authenticated user; customers only see their own (via `visible_orders_for`).
- **Query params:**
  - `page` (default 1), `per_page` (default 50, cap 200).
  - `status` (one of `Pending`, `Received`, `Shipped`, `Delivered`, `Cancelled`, `Returned`; else 400).
  - `customer_id` (customer-initiated; rejected with 403 if not the caller’s own customer for non-admins).
  - `q` (search by order_id, customer_id, customer name, or email).
- **Response (200):**
  ```json
  {
    "orders": [
      {
        "order_id": "ORD1234",
        "customer_id": "C5678",
        "order_date": "2026-10-21",
        "order_status": "Pending",
        "total": 123.45,
        "item_count": 2,
        "customer": { "customer_id": "C5678", "cust_name": "...", "email": "...", "user_id": 3 }
      }
    ],
    "page": 1,
    "per_page": 10,
    "total": 42,
    "pages": 5
  }
  ```
- **Client errors:** 400 invalid status/filter; 403 customer filtering another customer’s orders; 401 missing token.

### 17. `GET /api/orders/<order_id>`

- **Purpose:** Order detail with line items and total. Owner or admin.
- **Response (200):**
  ```json
  {
    "order_id": "ORD1234",
    "customer_id": "C5678",
    "order_date": "2026-10-21",
    "order_status": "Delivered",
    "total": 999.0,
    "item_count": 3,
    "items": [ ... ],
    "customer": { ... }
  }
  ```
- **Client errors:**
  - 401 missing token.
  - 404 order not found, or not owned by the caller (customer attempted to view another customer’s order; 404 is used instead of 403 to avoid leaking order IDs).

### 18. `PATCH /api/orders/<order_id>/status`

- **Purpose:** Update an order’s status (admin only).
- **Request:** `{ order_status: "Shipped" }`.
- **Behavior:**
  - Rejects missing status (400).
  - Enforces the state machine:
    - `Pending` → `Received`, `Shipped`, `Cancelled`
    - `Received` → `Shipped`, `Cancelled`
    - `Shipped` → `Delivered`, `Returned`
    - `Delivered` → `Returned`
    - `Cancelled` / `Returned` → none
- **Success (200):** order JSON with updated status.
- **Client errors (400/404):** invalid transition or missing order.

### 19. `GET /api/orders/duplicates`

- **Purpose:** Find duplicate order groups. Admin only.
- **Response (200):**
  ```json
  {
    "duplicates": [
      {
        "customer_id": "C5678",
        "product_id": 7,
        "product_name": "Phone",
        "quantity": 2,
        "unit_price": 199.0,
        "order_date": "2026-10-20",
        "occurrences": 2,
        "order_ids": ["ORD1234", "ORD5678"]
      }
    ]
  }
  ```
- **Behavior:** groups by customer, product, qty, price, date; returns groups with `occurrences > 1`, ordered by group size.
- **Client errors:** 403 for non-admin.

---

## Report endpoints (`/api/reports/*`)

Admin only.

### 20. `GET /api/reports/summary`

- **Purpose:** Dashboard KPIs + breakdowns + latest orders + duplicate groups.
- **Response (200):**
  ```json
  {
    "revenue": 1234.56,
    "sales_orders": 10,
    "units_sold": 34,
    "awaiting_action": 5,
    "total_orders": 42,
    "status_breakdown": [ { "status": "Delivered", "count": 10 }, ... ],
    "latest_orders": [ { "order_id", "customer_id", "order_date", "order_status", "total" }, ... ],
    "duplicate_groups": [ ... ],
    "product_breakdown": [ { "product", "items", "units", "revenue" }, ... ],
    "monthly_breakdown": [ { "period", "orders", "units", "revenue" }, ... ]
  }
  ```
- **Behavior:** revenue, sales orders, units sold are counted only for `Shipped` + `Delivered`; cancellations/returned/pending/received are not included. The report is computed from `order_items` (historical unit price), not from the current product price.

### 21. `GET /api/reports/product-wise`

- **Purpose:** Product-wise sales. Admin only.
- **Query:** `?format=csv` to download.
- **JSON (200):** `[ { "product": "Phone", "items": 20, "units": 60, "revenue": 12000.0 }, ... ]`.
- **CSV:** `Product, Items Sold, Units Sold, Revenue (INR)` header; numeric amounts formatted with 2 decimals.

### 22. `GET /api/reports/date-wise`

- **Purpose:** Daily or monthly sales by date. Admin only.
- **Query:** `?group=day|month` (default `day`), `?format=csv`.
- **JSON (200):** `[ { "period": "2026-10-21", "orders": 3, "units": 9, "revenue": 144.0 }, ... ]` (month mode uses `2026-10` buckets).
- **CSV:** `Period (day), Orders, Units Sold, Revenue (INR)` with 2-decimal amounts.

---

## Users endpoints (`/api/users/*`)

Admin only.

### 23. `GET /api/users`

- **Purpose:** List users. Admin only.
- **Response (200):** `{ users: [ { id, email, full_name, role, is_verified, customer_id }, ... ] }`.

### 24. `POST /api/users`

- **Purpose:** Create a user. Admin only.
- **Request:** `{ email, password, full_name?, role?: 'customer' }`.
- **Behavior:** email is lowercased; `role` defaults to `customer`; password hashed with bcrypt; new user is verified on creation.
- **Success (201):** `{ user: { ... } }`.
- **Client errors (400/409):** missing email/password, duplicate email.

### 25. `PATCH /api/users/<id>/role`

- **Purpose:** Change a user’s role. Admin only.
- **Request:** `{ role: "admin"|"customer" }`.
- **Success (200):** `{ message: 'Role updated', user }`.
- **Client errors (400/404):** invalid role value; missing user; cannot demote the last remaining admin (400).

### 26. `DELETE /api/users/<id>`

- **Purpose:** Delete a user. Admin only.
- **Behavior:**
  - Blocks self-deletion (400).
  - Blocks deleting the last remaining admin (400).
  - Sets `cust.user_id = NULL` and commits the customer row before delete.
- **Success (200):** `{ message: 'User deleted' }`.
- **Client errors (400/404):** as above.

---

## Health and root

### 27. `GET /health`

- **Purpose:** Liveness probe. Public.
- **Response (200):** `{ status: "ok" }`.

### 28. `GET /`

- **Purpose:** Root endpoint. Public.
- **Response (200):** `{ status: "ok" }`.

---

## Full endpoint map

| # | Method | Path | Auth | Description |
|---|--------|------|------|-------------|
| 1 | POST | `/api/auth/register` | public | register customer, send OTP |
| 2 | POST | `/api/auth/verify` | public | verify email OTP + link customer |
| 3 | POST | `/api/auth/resend-verification` | public | resend OTP |
| 4 | POST | `/api/auth/login` | public | get JWT |
| 5 | POST | `/api/auth/forgot-password` | public | request reset link |
| 6 | POST | `/api/auth/reset-password` | public | reset password with token |
| 7 | GET | `/api/auth/me` | auth | current user |
| 8 | GET | `/api/customers` | admin | list customers |
| 9 | POST | `/api/customers` | admin | create customer |
| 10 | PATCH | `/api/customers/<id>/link` | admin | link customer to user |
| 11 | GET | `/api/products` | auth | list products |
| 12 | POST | `/api/products` | admin | create product |
| 13 | PATCH | `/api/products/<id>` | admin | update price |
| 14 | DELETE | `/api/products/<id>` | admin | delete product |
| 15 | POST | `/api/orders` | admin | create order |
| 16 | GET | `/api/orders` | auth | list orders (owner/admin) |
| 17 | GET | `/api/orders/<id>` | auth | order detail |
| 18 | PATCH | `/api/orders/<id>/status` | admin | change status |
| 19 | GET | `/api/orders/duplicates` | admin | find duplicates |
| 20 | GET | `/api/reports/summary` | admin | dashboard summary |
| 21 | GET | `/api/reports/product-wise` | admin | product sales |
| 22 | GET | `/api/reports/date-wise` | admin | date/month sales |
| 23 | GET | `/api/users` | admin | list users |
| 24 | POST | `/api/users` | admin | create user |
| 25 | PATCH | `/api/users/<id>/role` | admin | change role |
| 26 | DELETE | `/api/users/<id>` | admin | delete user |
| 27 | GET | `/health` | public | liveness |
| 28 | GET | `/` | public | root |

---

## Important API behaviors

- **Auth:** JWT is sent as `Authorization: Bearer <token>`. `auth_required` resolves the user from the DB, not from the token claims; `token_version` mismatches return 401.
- **Role checks:** `role_required(Role.ADMIN.value)` enforces exact role on `customers`, `products`, `orders` admin actions, `reports`, `users`, `duplicates`.
- **Visibility:** customers see own orders only; customers requesting another customer’s order ID get `404`, not `403`. Admins see all orders and any order detail.
- **Pricing:** clients cannot set order prices; server uses `products.current_price`.
- **Idempotency/duplicates:** repeated API submissions are a different concern; duplicate-record detection lives in `GET /api/orders/duplicates`.
- **Status machine:** enforced by the backend and mirrored in the frontend for UI safety.
- **Error format:** JSON `error` or `errors` array, with no stack traces or credentials leaked.

---

# Backend Files Explained (OrderSalesManagement)

All Python paths are relative to `Order_Sales_Management/server/app/`. Flask app factory: `server/run.py` → `from app import create_app`; tests use `server/app/tests/conftest.py`.

---

## 1. `app/__init__.py` — app factory

- `from flask import Flask, jsonify` — Flask application and JSON helper.
- `from .config import Config, configure_logging` — settings and logger setup.
- `from .extensions import db, jwt, mail` — shared extensions.
- `def create_app():`
  - Creates the Flask app.
  - Loads `app.config.from_object(Config)`.
  - Calls `configure_logging(app)` to wire console + rotating file logging.
  - Initializes `db`, `jwt`, and `mail` singletons.
  - Registers JWT error handlers: `invalid_token` → 401, `unauthorized_loader` → 401, `expired_token` → 401.
  - Lazy-imports route blueprints and registers:
    - `auth_bp` (base `/api/auth`)
    - `orders_bp` (base `/api/orders`)
    - `reports_bp` (base `/api/reports`)
    - `products_bp` (base `/api/products`)
    - `customers_bp` (base `/api/customers`)
    - `users_bp` (base `/api/users`)
  - Adds root `/` and `/health` (both `/health` returns `{ status: 'ok' }`).
  - Returns the configured Flask app.
- Role: central factory, extension wiring, blueprint registration, and error hooks.

---

## 2. `app/config.py` — settings

- `BASE_DIR` — project root (`server/` parent).
- `configure_logging(app)` — sets up:
  - Console + `RotatingFileHandler` (`logs/app.log`, 5 MB, 3 backups).
  - Logging format `%(asctime)s | %(levelname)-7s | %(name)s | %(message)s`.
  - Suppresses noisy SQLAlchemy/Werkzeug logs while keeping Flask-level output.
  - Logs `Server ready` when started under the reloader.
- `class Config:`
  - `DATABASE_URL` — required; raises `RuntimeError` if missing.
  - `SECRET_KEY` / `JWT_SECRET_KEY` — required.
  - `SQLALCHEMY_DATABASE_URI`, `SQLALCHEMY_TRACK_MODIFICATIONS = False`.
  - `SQLALCHEMY_ENGINE_OPTIONS`: pool settings and `search_path` from `DB_SCHEMA` (default `order_sales`).
  - `JWT_ACCESS_TOKEN_EXPIRES` = hours from env (`JWT_ACCESS_TOKEN_EXPIRES_HOURS`) * 3600.
  - Mail config: `MAIL_SERVER/PORT/USERNAME/PASSWORD/USE_TLS`.
  - `VERIFY_TTL_MINUTES`, `VERIFY_MAX_ATTEMPTS`, `RESET_TTL_HOURS`.
- Role: single source for Flask configuration and logging; `.env`/`.env.test` are loaded before app creation.

---

## 3. `app/constants.py` — role constants

- `class Role(str, Enum): ADMIN = 'admin'`, `CUSTOMER = 'customer'`.
- `Role.values()` returns the allowed role strings as a set.
- `Role.is_valid(value)` checks membership.
- Role: single source for role strings used in decorators, guards, and validation.

---

## 4. `app/extensions.py` — shared singletons

- `db = SQLAlchemy()` — SQLAlchemy ORM engine/session.
- `jwt = JWTManager()` — JWT support (login, token revocation via `token_version`).
- `mail = Mail()` — Flask-Mail for email, used in development by `email.py`.
- `hash_password(plain)` — bcrypt hashing; type-checks and raises `TypeError` on non-str.
- `verify_password(plain, hashed)` — bcrypt verification; returns False safely on bad input.
- Role: reusable, dependency-free helpers available to routes and services.

---

## 5. `app/models.py` — SQLAlchemy models

### `User`
- Table `users`.
- Columns:
  - `id` PK (identity).
  - `email` (String, not null).
  - `password_hash` (String, not null).
  - `full_name` (String).
  - `role` (String, default `'customer'`), constrained to `'admin'`/`'customer'`.
  - `is_verified` (Boolean, default False).
  - `verification_token_hash`, `verification_expires_at`, `verification_attempts`.
  - `reset_token_hash`, `reset_token_expires_at`.
  - `token_version` (default 0) — used for JWT invalidation.
  - `created_at`, `updated_at` via `_now()`.
- `to_dict()` returns clean serializable fields.
- Relationship: `customer` → `Customer`, `uselist=False`.

### `Customer`
- Table `customers`; PK `customer_id` (String 20).
- `user_id` (Integer FK → users.id, `ON DELETE SET NULL`, unique) — one-to-one link to an account.
- `cust_name`, `email`, `created_at`.
- `to_dict()` serializes with `user_id`, `cust_name`, `email`.
- Relationship: `orders` → Order (lazy select).

### `Product`
- Table `products`; PK `product_id` (identity).
- `pro_name` unique not null; `current_price` Decimal(12,2).
- `to_dict()` converts `current_price` to float or null.
- Relationship: `order_items`.

### `Order`
- Table `orders`; PK `order_id` (String 20).
- `customer_id` FK → customers.customer_id (not null).
- `order_date` (Date), `order_status` (default `'Pending'`, validated set).
- `created_at`, `updated_at` with triggers (DB side).
- `items` relationship (OrderItem, order_by ID).
- `to_dict(include_items=False)` serializes order data; with items includes line items.

### `OrderItem`
- Table `order_items`; PK `order_item_id` (identity).
- `order_id` FK → orders.order_id (`ON DELETE CASCADE`).
- `product_id` FK → products.product_id.
- `quantity` (Integer, > 0 enforced), `unit_price` (Decimal(12,2), ≥ 0 enforced).
- Unique `(order_id, product_id)` constraint.
- `to_dict()` returns item, product name, and `line_total`.

- Role: defines all database entities and serialization. No business rules.

---

## 6. `app/utils/decorators.py` — auth/authorization decorators

- `_load_user(uid)` — loads a `User` by integer ID; returns None on bad input.
- `_resolve_request_user()` — runs after `jwt_required()`:
  - Reads `get_jwt_identity()`, loads the user.
  - Checks `get_jwt()['tv']` against `user.token_version`; mismatch → 401.
  - Returns `(user, None)` or `(None, (jsonify(...), 401))`.
- `auth_required(fn)` — decorator:
  - Wraps `@jwt_required()` + `_resolve_request_user()`.
  - On success sets `g.current_user`.
- `role_required(required_role)` — decorator factory:
  - Checks `user.role == required_role`; else returns 403.
  - On success, sets `g.current_user`.
- Role: DRY auth and RBAC for every route.

---

## 7. `app/utils/permissions.py` — ownership predicates

- `is_admin(user)` / `is_customer(user)`.
- `owns_customer(user, customer_id)` — True when the logged-in user is linked to that customer.
- `can_view_order(user, order)` — admins can always view; customers can view only orders owned by their linked customer.
- Role: used in `orders.py` to enforce 404-on-other-customer while avoiding ID enumeration.

---

## 8. `app/utils/email.py` — dev email simulation

- `DEV_EMAIL_LOG` — path to `server/logs/dev_emails.log`.
- `_write_dev_email_log(kind, email, payload)` — appends timestamped lines.
- `send_verification_code(email, code)` — logs `VERIFY-OTP` with TTL.
- `send_password_reset(email, token)` — builds `FRONTEND_URL/reset-password?token=...` and logs `RESET-LINK`.
- Role: development-only delivery. Production should replace with a real email provider.

---

## 9. `app/utils/validators.py` — input validators

- `normalize_email(email)` — strip + lowercase.
- `validate_password(password)` — returns a message when empty, < 8 chars, or > 72 bytes (bcrypt limit).
- `validate_email(email)` — requires non-empty and contains `@`.
- Role: uses as the single source for auth input validation in `auth_service.py`.

---

## 10. `app/services/__init__.py`

Empty package marker.

---

## 11. `app/services/auth_service.py` — auth business logic

- `_now()` — UTC timestamp.
- `_hash(value)` — SHA-256 hex digest (used for OTP and reset tokens, never the raw value).
- `_new_otp()` — 6-digit zero-padded OTP.
- `_new_reset_token()` — `secrets.token_urlsafe(32)` reset token.
- `_verify_ttl_minutes()`, `_verify_max_attempts()`, `_reset_ttl_hours()` — config-backed TTL/limit values.

### `register(email, password, full_name, customer_id)`
- Validates email/password and a real customer ID.
- Rejects duplicate email (case-insensitive) and unknown customer ID.
- Rejects a customer record whose email doesn’t match the given email.
- Stores a hashed OTP, creates the user with `role='customer'`, `is_verified=False`, `token_version=0`, and 2-minute OTP TTL.
- Returns `(user, None)` or `(None, error)`.

### `verify_email(email, code)`
- Validates input; finds the user.
- Rejects already verified, missing/hash-less tokens, expired tokens.
- Limits attempts; on wrong code, increments `verification_attempts` and returns remaining count.
- On success: marks verified, clears OTP fields.

### `resend_verification_code(email)`
- Returns `(True, None)` for unknown or already-verified users (no enumeration).
- Issues a fresh OTP and sends it.

### `link_customer(user, customer_id)`
- Requires verified user.
- Rejects unknown/missing customer or email mismatch.
- Sets `cust.user_id = user.id`, updates email/name if empty.
- Returns `(True, None)` or `(False, error)`.

### `login(email, password)`
- Finds user by lowercased email; rejects missing/invalid credentials and unverified accounts.
- Returns a token with `role`, `email`, `tv`, and the user object.

### `forgot_password(email)`
- If the user exists, hashes a new reset token and sets a 1-hour expiry.
- Always returns `(True, None)` for both known and unknown emails.

### `reset_password(token, new_password)`
- Finds user by hashed token; rejects unknown/inactive/expired tokens.
- Validates password; then replaces `password_hash`, clears reset state, resets verification state, and increments `token_version` (invalidates old JWTs).

- Role: all identity and password logic lives here, with no HTTP or Flask route imports.

---

## 12. `app/services/order_service.py` — order business logic

- `VALID_STATUSES = {Pending, Received, Shipped, Delivered, Cancelled, Returned}`.
- `ALLOWED_TRANSITIONS` — exact state machine.
- `SALE_STATUSES = frozenset({Shipped, Delivered})` — recognized as revenue-generating.

### `validate_order_payload(payload)`
- Returns a list of errors.
- Enforces `order_id` `ORD####`, `order_date` parseable as `YYYY-MM-DD`, `customer_id` `C####` and must exist, at least one item, unique product per order, quantity integer 1..1000, and product existence + non-null price.
- Accepts an optional `order_status` (default `Pending`), validated against `VALID_STATUSES`.

### `create_order(payload)`
- Runs validation first; returns `(None, errors, 400)` if invalid.
- Rejects duplicate order IDs (409).
- Creates the order header as `Pending`, then inserts each item with `unit_price = product.current_price`.
- Commits in a transaction; rolls back and re-raises unexpected exceptions.
- Returns `(order, None, 201)`.

### `visible_orders_for(user)`
- Admin: `Order.query`.
- Customer: scoped join `orders`→`customers` filtered by `customer.user_id == user.id`.
- None/unknown user: empty query.
- Role: ownership scope used by the `/orders` GET.

### `can_transition(old_status, new_status)`
- Validates statuses and checks the transition set.

### `change_status(order, new_status)`
- Uses `can_transition`; returns `(False, message)` on failure.
- On success, updates `order_status` and commits, returns `(True, None)`.

### `product_wise_report()`
- Groups by product; counts items, sums units, and sums `quantity * unit_price`.
- Filters only Shipped+Delivered orders; ordered by revenue descending.

### `date_wise_report(group='day')`
- Bucket is month-truncated (`date_trunc`) for `group='month'`, else raw `order_date`.
- Counts distinct orders, sums units and revenue, for Shipped+Delivered orders only.

### `find_duplicates()`
- Joins orders, order_items, products.
- Groups by customer, product, qty, price, date, and returns all groups with `occurrences > 1`.
- Each result includes customer/product IDs, names, qty, price, date, occurrences, and sorted `order_ids`.

### `get_dashboard_summary()`
- Computes `revenue`, `sales_orders`, `units_sold`, `awaiting_action` (Pending+Received), `total_orders` from the `orders` table.
- Fetches `latest_orders` (top 6), `find_duplicates()[:3]`, full `product_breakdown`, `monthly_breakdown`, and `status_breakdown`.
- Returns a flat dict used directly by the API route.

- Role: all order/catalog/report logic lives here, with no HTTP or Flask-route imports.

---

## 13. `app/routes/__init__.py`

Empty package marker.

---

## 14. `app/routes/auth.py` — auth HTTP layer

- `auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')`.
- `_json()` — safe request JSON parser.
- `register_route()` → `register()`; returns 201 with a verification message, 400 with errors.
- `verify_route()` → `verify_email()`; on success, links customer if supplied; 409 on link failure.
- `resend_route()` → `resend_verification_code()`; generic 200 message.
- `login_route()` → `login()`; 200 with `access_token` + user, 401 on error.
- `forgot_route()` → `forgot_password()`; generic 200.
- `reset_route()` → `reset_password()`; 200 on success, 400 on failure.
- `me_route()` → `auth_required`; returns full user + customer info when linked.
- Role: thin HTTP controller; all logic is in `auth_service`.

---

## 15. `app/routes/customers.py` — customer HTTP layer

- `customers_bp` at `/api/customers`.
- `list_customers()` → Admin only; returns `{ customers: [...] }`.
- `create_customer()` → Admin only; validates and creates a customer; 409 on duplicate ID.
- `link_customer_route(<customer_id>)` → Admin only; validates user and linking rules; copies email/name from the user if empty.
- Role: thin HTTP layer over `Customer` and DB session.

---

## 16. `app/routes/orders.py` — order HTTP layer

- `orders_bp` at `/api/orders`. Logged-in user is available as `g.current_user`.
- `_json()` — safe request body parser.
- `_order_response(order, include_items)` — builds JSON including items, computed total, and customer info.
- `list_duplicates()` → Admin only → `{ duplicates: find_duplicates() }`.
- `list_orders()`:
  - `auth_required`; `visible_orders_for(user)` controls admin/customer scope.
  - Parses and validates `status`, `customer_id`, and `q` search.
  - Paginates with Flask-SQLAlchemy with defaults `page=1`, `per_page=50` (capped at 200).
  - Returns paginated JSON with `orders`, `page`, `per_page`, `total`, `pages`.
- `get_order(order_id)`:
  - `auth_required`; 404 if order not found or `!can_view_order(user, order)` (customer isolation).
- `create_order()`:
  - Admin only; calls `create_order_service()`; wraps `IntegrityError` as 409, generic DB failures as 400.
  - Returns validation errors array or success JSON.
- `update_status(order_id)`:
  - Admin only; 400 if no status, 404 if missing, 400 on invalid transition.
- Role: thin HTTP layer; business rules from `order_service`.

---

## 17. `app/routes/products.py` — product HTTP layer

- `products_bp` at `/api/products`.
- `list_products()` → auth-required; returns product list.
- `create_product()` → admin; enforces unique name and non-negative price.
- `update_product_price(<id>)` → admin; returns 400 on invalid/negative price.
- `delete_product(<id>)` → admin; 409 if the product is used in any order.

---

## 18. `app/routes/reports.py` — report HTTP layer

- `reports_bp` at `/api/reports`.
- `dashboard_summary()` → admin only → `{ summary }`.
- `product_wise()` → admin only; JSON list or CSV download with `format=csv`.
- `date_wise()` → admin only; `group=day|month`, JSON or CSV.
- `_generate_product_csv(data)` and `_generate_date_csv(data, group)` produce streamed CSV responses with `Content-Disposition` filenames.
- Role: JSON + CSV report delivery; all aggregation is in `order_service`.

---

## 19. `app/routes/users.py` — users HTTP layer

- `users_bp` at `/api/users`.
- `list_users()` → admin only.
- `create_user()` → admin; enforces lowercase email, validation, hashed password, and a default role of `customer`.
- `update_user_role(<id>)` → admin only; rejects invalid roles; prevents demoting the last admin.
- `delete_user(<id>)` → admin only; blocks self-delete and last-admin deletion; unsets the linked customer record before deleting.
- Role: thin HTTP layer; all business rules in the function body (this file directly touches `User`, `db`, and `get_jwt_identity`).

---

## 20. `app/__init__.py` — app factory

Already described above.

---

## 21. `app/config.py`

Already described above.

---

## 22. `app/constants.py`

Already described above.

---

## 23. `app/extensions.py`

Already described above.

---

## 24. `app/models.py`

Already described above.

---

## 25. `app/utils/decorators.py`, `permissions.py`, `email.py`, `validators.py`

Already described above.

---

## 26. `app/services/auth_service.py`, `order_service.py`

Already described above.

---

# Final Full Project Explained — OrderSalesManagement (Intern_Training)

## 1. What this project is

A small inventory/order-management web app built as an internship training project:

- A **Vue 3 frontend** (Vite + Pinia + Vue Router + Axios).
- A **Flask REST API** (Python + Flask-SQLAlchemy).
- A **PostgreSQL database** (pre-created schema `order_sales`).
- The app provides: accounts + email verification + password reset, role-based access (`admin`, `customer`), per-customer order ownership, validated order creation, server-side pricing, strict status transitions, duplicate-order detection, and sales dashboards.

The public website is `http://localhost:5173` (Vite) and the API is `http://localhost:5000` (Flask).

---

## 2. Architecture

```
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

Key architectural rules:

- The browser only talks to Flask over HTTP JSON; Flask never lets the browser touch PostgreSQL directly.
- Flask enforces auth, authorization, validation, business rules, and report queries.
- Frontend route guards are for UX; backend decorators are the real security.
- Routes are thin HTTP controllers; services contain the business rules.

---

## 3. Tech stack

| Layer | Technology | Responsibility |
|-------|------------|------------------|
| Frontend | Vue 3 + Vite + Pinia + Vue Router + Axios | Auth screens, order list/detail, status updates, reports |
| Backend | Python + Flask + Flask-SQLAlchemy | API endpoints, validation, business rules, transactions |
| Auth | Flask-JWT-Extended + bcrypt | Login tokens, password hashing, role checks, token revoking via `token_version` |
| DB | PostgreSQL (`order_sales` schema) | Relational data, constraints, indexes |
| Email (dev) | Flask-Mail + dev log | OTP and reset links written to `server/logs/dev_emails.log` |
| Testing | pytest + Flask test client | Regression suite |

---

## 4. Database design

Schema: `order_sales`. Flask connects to this schema at startup; it is not created/dropped by the app.

### Tables

| Table | Purpose |
|-------|---------|
| `users` | Login credentials, verification state, password reset, role, token version |
| `customers` | Customer profiles and account linking (`user_id` links to `users`) |
| `products` | Product catalog and current price |
| `orders` | Order header: customer, date, status |
| `order_items` | Products, quantities, historical unit price per order |
| `staging_orders` | Raw CSV rows before import/validation |

### Relationships

- `users` 1 ↔ 0..1 `customers`
- `customers` 1 ↔ many `orders`
- `orders` 1 ↔ many `order_items`
- `products` 1 ↔ many `order_items`
- `customers.user_id` unique → one user per customer; `ON DELETE SET NULL`
- `order_items.order_id` cascades delete, so an order and its items are deleted together.

### Key design decisions

- `users.email` unique case-insensitively (`LOWER(email)`).
- Passwords, verification tokens, and reset tokens are stored only as hashes. Tokens also carry an expiry.
- `order_items.unit_price` preserves the price charged at purchase; `products.current_price` is optional catalog data and is never used to rewrite history.
- Each order item stores the exact `unit_price` used for the order total.
- New-order prices come from the server (`products.current_price`), never from the browser.
- `orders.order_status` uses a strict set; the app enforces legal transitions.
- Sales reports count only `Shipped` + `Delivered` orders for revenue.

---

## 5. Authentication and authorization

### 5.1 Account lifecycle

1. **Register** (public):
   - Email + password + full name + customer ID.
   - Server normalizes and validates the email/password.
   - Creates a customer account with `role='customer'`, `is_verified=FALSE`, and a 6-digit OTP.
   - OTP is sent via dev email log.
   - Subsequent OTP/verification is required before login or customer linking.

2. **Verify email** (public):
   - Submit the 6-digit OTP.
   - Server checks expiry and attempt limits; on success marks the user verified.

3. **Login** (public):
   - Server loads the user by lowercased email, verifies password with bcrypt, and requires `is_verified`.
   - On success returns a JWT whose `identity` is the user ID and whose claims include `role`, `email`, and `token_version`.

4. **Reset password** (public):
   - Request a reset link via email.
   - Submit token + new password.
   - Server replaces the password hash and increments `token_version`, invalidating old tokens.

### 5.2 Role and ownership

- `role_required(Role.ADMIN.value)` protects admin endpoints.
- `auth_required` verifies the JWT and resolves the user from the DB; a `token_version` mismatch returns 401.
- `can_view_order()` returns:
  - Admin → always true.
  - Customer → true only for orders whose customer record is linked to that user.
- Customers trying another customer’s order ID get 404, not 403, to avoid leaking order IDs.
- `customers.user_id` is unique → a customer record can be linked to at most one user.

### 5.3 Frontend guards

- Router `beforeEach` enforces:
  - Protected routes require auth.
  - Admin routes redirect non-admins to `/app/orders`.
  - Customer opening `/app/orders` sees `/app/my-orders`.
  - Admin opening `/app/my-orders` sees `/app/orders`.

---

## 6. Order workflow

### 6.1 Create

- Payload: `order_id` (`ORD####`), `customer_id` (`C####`), `order_date`, `items`.
- Validation: formats, dates, positive integer quantity, product existence + price, no duplicate product per order.
- Server creates the order as `Pending` and inserts line items with the product’s server-side price.
- If any insert fails, the transaction rolls back.

### 6.2 Status machine

| From | Allowed next status |
|------|---------------------|
| `Pending` | `Received`, `Shipped`, `Cancelled` |
| `Received` | `Shipped`, `Cancelled` |
| `Shipped` | `Delivered`, `Returned` |
| `Delivered` | `Returned` |
| `Cancelled` | none |
| `Returned` | none |

- Client UI only offers legal next steps from `allowedTransitions`.
- Backend rejects illegal transitions with 400 and a message.
- `Cancelled` and `Returned` are terminal states.

### 6.3 Duplicate detection

- A duplicate group is defined by the same `customer_id`, `product_id`, `quantity`, `unit_price`, and `order_date`.
- Returns `order_ids` (the full group), `occurrences`, `customer_id`, `product_id`, `product_name`, `quantity`, `unit_price`, `order_date`.
- Admin-only endpoint.
- The UI lets the admin cancel one copy (moves it to `Cancelled`) while keeping the other record.

---

## 7. Sales reporting

- Revenue counts orders with `order_status` `Shipped` or `Delivered` only.
- `products.current_price` is **not** used for report totals; `order_items.unit_price` is preserved.
- `GET /api/reports/summary` returns:
  - KPIs: `revenue`, `sales_orders`, `units_sold`, `awaiting_action`, `total_orders`
  - `status_breakdown`, `latest_orders`, `duplicate_groups`, `product_breakdown`, `monthly_breakdown`
- `GET /api/reports/product-wise` (`?format=csv`) and `GET /api/reports/date-wise` (`?group=day|month`, `?format=csv`) return CSV or JSON.

---

## 8. Frontend architecture

### Root and routing

- `main.js`: app bootstrap, Pinia + Vue Router registration, mount.
- `router/index.js`: routes and global auth/role guards.

### State

- `stores/auth.js`: token, user, `isAuthenticated`, `isAdmin`, login/logout.
- `stores/summary.js`: summary payload with cache/force behavior.

### HTTP

- `services/api.js`: base URL `/api`, automatic `Authorization` header, 401/422 logout redirect.

### Pages

- Public: `Landing`, `Login`, `Register`, `ForgotPassword`, `ResetPassword`.
- Admin: `Orders`, `CreateOrder`, `OrderDetail`, `Products`, `Customers`, `Users`, `Reports`, `Duplicates`, `Totals`.
- Customer: `MyOrders`.
- Layouts/components: `AppLayout`, `AuthShell`, `Icon`.

### Utilities

- `format.js`: `money`, `number`, `percent`, `formatDate`, `initials`.
- `style.css`: design tokens and reusable base styles.
- `vite.config.js`: dev proxy to Flask and alias `@` → `src`.

---

## 9. Backend architecture

### App factory and extensions

- `app/__init__.py`: `create_app()`; config, logging, DB/JWT/Mail init, blueprint registration.
- `extensions.py`: singleton `db`, `jwt`, `mail`, `hash_password`, `verify_password`.
- `config.py`: env-driven settings (`.env` or `.env.test`), logging, mail config, JWT TTL.

### Business logic

- `constants.py`: `Role` enum.
- `decorators.py`: `auth_required`, `role_required`.
- `permissions.py`: `is_admin`, `is_customer`, `owns_customer`, `can_view_order`.
- `email.py`: dev email log.
- `validators.py`: email/password normalization and validation.
- `services/auth_service.py`: all account-related logic.
- `services/order_service.py`: order creation/validation/status/report logic.

### Routes

- `routes/auth.py`, `orders.py`, `customers.py`, `products.py`, `reports.py`, `users.py` — thin HTTP controllers calling services.
- `models.py` — database entities.
- `tests/` — pytest suite covering auth, permissions, pricing, reports, order workflow, and smoke.

---

## 10. How the pieces fit together

1. A user opens the site → Vue Router decides between public auth and protected `/app`.
2. If they need credentials, Register or Login creates a verified account and login returns a JWT.
3. Every API request sends the JWT; Flask resolves the user from the DB, checks the `token_version` claim, and enforces `role_required` and `can_view_order`.
4. The customer sees only their own orders; admins see everything.
5. Orders are created with server-side pricing, validated inputs, and atomic writes.
6. Status can only move through the defined transitions.
7. Admins can inspect duplicate groups, generate product/date sales reports, create users/products, and list customers/orders.
8. The dashboard reads the summary endpoints and refreshes when statuses/totals change.

---

## 11. Where to start for different tasks

| Task | Start here |
|------|------------|
| Add a public page | `client/src/views/NewView.vue` + `client/src/router/index.js` |
| Add a new API endpoint | `app/services/...` for logic, then `app/routes/...` + tests |
| Change auth rules | `services/auth_service.py`, `decorators.py`, `models.py` |
| Change orders/limits | `services/order_service.py`, `models.py` |
| Change pricing rule | `order_service.py` create; `products.py` price update |
| Change report definitions | `services/order_service.py` report functions |
| Change layouts | `layouts/AppLayout.vue`, `components/AuthShell.vue`, `components/Icon.vue` |

---

## 12. Verification performed

- Backend dependency resolution: passed.
- Backend test suite: `python -m pytest tests/ -v` → **82 passed** (auth, permissions, pricing, reports, order workflow, smoke) through the project virtualenv.
- Sources for this documentation were read from all `server/app/**/*.py`, `client/src/**/*` Vue/JS/CSS files, and `client/vite.config.js`.

---
Order & Sales Management (OrderSalesManagement) — Intern_Training
