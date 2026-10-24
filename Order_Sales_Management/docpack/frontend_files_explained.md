# Frontend Files Explained (OrderSalesManagement)

This file explains every frontend source file in `Order_Sales_Management/client/src/`: route/component role, state, and where it connects to the backend.

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
- Route definitions:
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
  - `alias '@'` maps `@@/` imports to `client/src/...`.
  - `server.proxy` forwards `/api` and `/db` requests to the Flask backend, so the browser never needs a real backend host.
- Role: dev-server proxy + path alias.

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

## Backend references for frontend developers

| Endpoint pattern | Frontend caller | Where it lands |
|---|---|---|
| `/api/auth/register`, `/api/auth/verify`, `/api/auth/login`, `/api/auth/forgot-password`, `/api/auth/reset-password`, `/api/auth/me` | `Login.vue`, `Register.vue`, `ForgotPassword.vue`, `ResetPassword.vue` | `server/app/routes/auth.py` → `server/app/services/auth_service.py` |
| `/api/orders`, `/api/orders/<id>`, `/api/orders/<id>/status`, `/api/orders/duplicates` | `Orders.vue`, `MyOrders.vue`, `OrderDetail.vue`, `Duplicates.vue` | `server/app/routes/orders.py` → `server/app/services/order_service.py` |
| `/api/reports/summary`, `/api/reports/product-wise`, `/api/reports/date-wise` | `Reports.vue`, `Totals.vue` | `server/app/routes/reports.py` → `server/app/services/order_service.py` |
| `/api/customers`, `/api/products`, `/api/products/<id>`, `/api/customers/<id>/link`, `/api/users/*` | admin views | `server/app/routes/customers.py`, `products.py`, `users.py` |
