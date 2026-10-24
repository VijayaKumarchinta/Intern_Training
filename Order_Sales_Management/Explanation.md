# Explanation.md — Order & Sales Management Application

This document explains the project file-by-file, with a focus on the frontend now.

The app is split into three layers:

```text
Vue 3 Frontend  ->  HTTP JSON requests  ->  Flask REST API  ->  PostgreSQL
```

The browser only talks to Flask. Flask never lets the browser touch PostgreSQL directly.
Flask enforces authentication, authorization, validation, business rules, and report queries.

---

# 1. Frontend (`client/`)

The frontend is a Vue 3 single-page application. It has no database code. It only sends requests and renders JSON.

---

## 1.1 Entry and bootstrap

### `client/index.html`

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>OrderSync - Sales Management</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.js"></script>
  </body>
</html>
```

Why each part exists:

- `<!doctype html>` starts an HTML5 document.
- `<meta charset="UTF-8">` allows the page to render non-ASCII text correctly.
- `<link rel="icon">` loads the app favicon.
- `<meta name="viewport">` makes the page responsive on mobile devices.
- `<div id="app">` is the mount point where Vue attaches the application.
- `<script type="module" src="/src/main.js">` tells the browser to load the Vue app as a JavaScript module.

The `favicon.svg` path is relative to `client/public/`, so Vite copies it to the output root.

---

### `client/src/main.js`

```js
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './style.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
```

Why each line exists:

- `createApp(App)` creates the Vue application root from `App.vue`.
- `createPinia()` creates the Pinia state store.
- `app.use(createPinia())` registers Pinia so every component can use `useAuthStore()` and `useSummaryStore()`.
- `app.use(router)` registers Vue Router so the app can switch pages.
- `app.mount('#app')` attaches the app to the `<div id="app">` element in `index.html`.

This is the single entry point. Without this file, Vue would not start.

---

### `client/src/App.vue`

```html
<script setup>
</script>

<template>
  <router-view />
</template>
```

Why this file exists:

- It is the root component.
- It is intentionally empty outside of `<router-view />`.
- `<router-view />` is a placeholder that React/Vue swaps out for the current route component.

This keeps routing outside the root component. Every route page is loaded by the router automatically.

---

## 1.2 Global styling and utilities

### `client/src/style.css`

This is the global stylesheet imported by `main.js`.

Key parts:

```css
@import url('https://fonts.googleapis.com/css2?family=Inter+Tight:wght@500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');
```

Why:

- The app uses two fonts.
- `Inter Tight` is used for headings and important UI text.
- `Inter` is used for body text.

```css
:root {
  --bg-app: #eef1f7;
  --bg-card: #ffffff;
  --ink: #0b1220;
  ...
}
```

Why:

- CSS variables centralize colors, spacing, shadows, and radius values.
- Components can reuse the same tokens, so the design stays consistent.
- Changing a theme later only requires editing one place.

```css
.card {
  background: var(--bg-card);
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-card);
}
```

Why:

- `.card` is a reusable container used in almost every admin view.
- It gives every card the same background, border radius, and shadow.

```css
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 44px;
  padding: 0 22px;
  border-radius: var(--radius-pill);
  font-size: 14px;
  font-weight: 600;
  white-space: nowrap;
}
```

Why:

- This is the base button style.
- Buttons across the app should look identical.
- The right padding, height, and color are reused through modifier classes like `.btn-primary`, `.btn-dark`, `.btn-lime`, `.btn-ghost`, and `.btn-outline-red`.

```css
.status-pill {
  display: inline-flex;
  align-items: center;
  padding: 5px 12px;
  border-radius: var(--radius-pill);
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}
.status-pill.pending {
  background: var(--cream);
  color: #8a5a00;
}
.status-pill.shipped {
  background: var(--blue-soft);
  color: #1f45c9;
}
```

Why:

- Order status pills need to look different for each status.
- Instead of writing inline styles for every pill, Vue binds classes like `status-pill pending`, so the CSS values above control the color and background.

```css
.input {
  width: 100%;
  height: 48px;
  padding: 0 18px;
  border: 1px solid var(--line-strong);
  border-radius: var(--radius-pill);
  background: #fff;
  color: var(--text-primary);
  font-size: 14px;
}
```

Why:

- This is the shared text input style.
- Every form in the app uses this same shape.

```css
.table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
  font-size: 14px;
}
```

Why:

- The app shows order, user, customer, product, and report tables in several views.
- `.table` gives all tables the same padding, borders, and alignment.

```css
::-webkit-scrollbar {
  width: 10px;
  height: 10px;
}
::-webkit-scrollbar-thumb {
  background: #d5d9e4;
  border-radius: 999px;
  border: 3px solid var(--bg-app);
}
```

Why:

- The app has horizontally scrollable tables on smaller screens.
- These rules style the scrollbar instead of leaving it default.

---

### `client/src/utils/format.js`

This file contains formatting helpers. Every component imports from here instead of writing formatting logic internally.

```js
export const money = (value, digits = 2) => {
  const amount = Number(value || 0)
  return `₹${amount.toLocaleString('en-IN', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })}`
}
```

Why:

- `number || 0` prevents `NaN` or `undefined` from appearing as a broken number.
- `toLocaleString('en-IN')` adds a thousands separator.
- The app uses Indian currency formatting.
- `minimumFractionDigits` and `maximumFractionDigits` ensure `.2f` style output for money.

```js
export const number = (value) => Number(value || 0).toLocaleString('en-IN')
```

Why:

- Used for counts like `123` -> `123`, `1000` -> `1,000`.

```js
export const percent = (part, whole) => {
  if (!whole) return 0
  return (Number(part || 0) / Number(whole)) * 100
}
```

Why:

- It prevents division by zero.
- It returns `0` when there are no orders yet.
- It always returns a percentage number like `42.5`, not a string.

```js
export const formatDate = (iso) => {
  if (!iso) return '—'
  const date = new Date(`${iso}T00:00:00`)
  if (Number.isNaN(date.getTime())) return iso
  return date.toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}
```

Why:

- `order_date` is stored by PostgreSQL, often as `YYYY-MM-DD`.
- Vue receives it as an ISO string, so `new Date(...)` converts it into a display-friendly date.
- `en-GB` gives a UK-style date such as `16 Oct 2026`.
- If the date is empty or invalid, it returns `—` instead of crashing.

---

## 1.3 State management

### `client/src/stores/auth.js`

This Pinia store handles authentication.

```js
state: () => ({
  token: localStorage.getItem('token') || null,
  user: JSON.parse(localStorage.getItem('user')) || null,
})
```

Why:

- On app load, Vue reads `localStorage` directly.
- If the browser still has a token and user object, the page does not need to ask the user to log in again immediately.
- If nothing is stored, `token` and `user` start as `null`.

```js
getters: {
  isAuthenticated: (state) => !!state.token,
  isAdmin: (state) => state.user?.role === 'admin',
}
```

Why:

- `isAuthenticated` is used by the router to know whether a user can enter protected pages.
- `isAdmin` is used by the router to decide whether the user is allowed to see admin-only links and pages.

```js
actions: {
  async login(email, password) {
    const res = await api.post('/auth/login', { email, password })
    this.token = res.data.access_token
    this.user = res.data.user
    localStorage.setItem('token', this.token)
    localStorage.setItem('user', JSON.stringify(this.user))
  }
}
```

Why:

- It sends the login request to the backend.
- It saves the JWT in `localStorage`.
- It also saves the user object so the app can remember the user and role.
- The route guard in `router/index.js` can then decide where to send the user after login.

```js
actions: {
  async fetchMe() {
    if (!this.token) return
    try {
      const res = await api.get('/auth/me')
      this.user = res.data
      localStorage.setItem('user', JSON.stringify(this.user))
    } catch (err) {
    }
  }
}
```

Why:

- After the app loads, `AppLayout.vue` calls this.
- It refreshes the current user details from the backend.
- It is useful after login or when a token is refreshed.

```js
actions: {
  logout() {
    this.token = null
    this.user = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }
}
```

Why:

- This clears everything before redirecting to `/login`.
- The router and the API interceptors rely on `auth.isAuthenticated` being false after logout.

---

### `client/src/stores/summary.js`

This Pinia store stores the report dashboard data.

```js
state: () => ({
  data: null,
  loading: false,
  error: '',
}),
```

Why:

- `data`: holds the summary returned by `GET /reports/summary`.
- `loading`: prevents duplicate requests while the API call is in progress.
- `error`: stores a user-facing error message if the request fails.

```js
actions: {
  async fetch(force = false) {
    if (this.data && !force) return
    if (this.loading) return
    this.loading = true
    this.error = ''
    try {
      const res = await api.get('/reports/summary')
      this.data = res.data
    } catch (err) {
      this.error = 'Failed to load totals.'
    } finally {
      this.loading = false
    }
  }
}
```

Why:

- Reports should not be fetched on every render. The store keeps the data.
- `force = true` is used when the user takes an action that should refresh the dashboard, like changing an order status.
- The `try/catch` ensures the app stays stable even if the backend fails.

---

### `client/src/services/api.js`

This Axios instance is the only HTTP client used by the frontend.

```js
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})
```

Why:

- Every request that needs authentication adds the JWT header automatically.
- Components do not have to write `Authorization` inside every `api.get()` or `api.post()`.

```js
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response && (err.response.status === 401 || err.response.status === 422)) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      if (window.location.pathname !== '/login' && window.location.pathname !== '/') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(err)
  }
)
```

Why:

- A `401` means the token expired or was deleted.
- A `422` usually means validation or auth failure.
- When either happens, the app removes the stale credentials and redirects to `/login`.
- It still rejects the error so the view can also show a message.

---

## 1.4 Router and authentication guards

### `client/src/router/index.js`

```js
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
```

Why:

- `createRouter` builds the Vue Router instance.
- `useAuthStore` is imported so the router can read the user state.

```js
const routes = [
  { path: '/', name: 'Landing', component: () => import('@/views/Landing.vue') },
  { path: '/login', name: 'Login', component: () => import('@/views/Login.vue') },
  { path: '/register', name: 'Register', component: () => import('@/views/Register.vue') },
  { path: '/forgot-password', name: 'ForgotPassword', component: () => import('@/views/ForgotPassword.vue') },
  { path: '/reset-password', name: 'ResetPassword', component: () => import('@/views/ResetPassword.vue') },
  {
    path: '/app',
    component: () => import('@/layouts/AppLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: '', redirect: '/app/orders' },
      { path: 'orders', name: 'Orders', component: () => import('@/views/Orders.vue') },
      { path: 'my-orders', name: 'MyOrders', component: () => import('@/views/MyOrders.vue') },
      { path: 'orders/:id', name: 'OrderDetail', component: () => import('@/views/OrderDetail.vue') },
      { path: 'products', name: 'Products', component: () => import('@/views/Products.vue'), meta: { requiresAdmin: true } },
      { path: 'customers', name: 'Customers', component: () => import('@/views/Customers.vue'), meta: { requiresAdmin: true } },
      { path: 'reports', name: 'Reports', component: () => import('@/views/Reports.vue'), meta: { requiresAdmin: true } },
      { path: 'duplicates', name: 'Duplicates', component: () => import('@/views/Duplicates.vue'), meta: { requiresAdmin: true } },
      { path: 'new-order', name: 'CreateOrder', component: () => import('@/views/CreateOrder.vue'), meta: { requiresAdmin: true } },
      { path: 'users', name: 'Users', component: () => import('@/views/Users.vue'), meta: { requiresAdmin: true } },
      { path: 'totals', name: 'Totals', component: () => import('@/views/Totals.vue'), meta: { requiresAdmin: true } },
    ]
  }
]
```

Why each route exists:

- `Landing` is the public homepage.
- `Login`, `Register`, `ForgotPassword`, and `ResetPassword` are public auth screens.
- `/app` is the protected dashboard layout.
- `/app/orders` is the default order list for everyone.
- `/app/my-orders` is the customer-only order view.
- `/app/orders/:id` is the detail page.
- Admin-only routes are marked with `meta: { requiresAdmin: true }`.

The `component: () => import('@/views/Orders.vue')` pattern is code splitting. This means Vue downloads the route page only when the user visits it.

---

### Router guard logic

```js
router.beforeEach((to, from, next) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    next('/login')
  }
  else if (to.meta.requiresAdmin && !auth.isAdmin) {
    next('/app/orders')
  }
  else if (to.name === 'Orders' && auth.isAuthenticated && !auth.isAdmin) {
    next('/app/my-orders')
  }
  else if (to.name === 'MyOrders' && auth.isAdmin) {
    next('/app/orders')
  }
  else {
    next()
  }
})
```

Why each branch exists:

- If a protected route is visited without a token, redirect to `/login`.
- If an admin-only route is visited by a customer, send them back to the order list.
- If a normal user visits `/app/orders`, show their own orders instead.
- If an admin visits `/app/my-orders`, send them to the normal admin order list.
- Otherwise, let the route continue.

This is the UI-side guard. It reduces unnecessary backend calls, but it does not replace backend security.

---

## 1.5 Shared UI components

### `client/src/components/Icon.vue`

```js
const props = defineProps({
  name: { type: String, required: true },
  size: { type: [Number, String], default: 20 },
  strokeWidth: { type: [Number, String], default: 2 },
})
```

Why:

- This component renders inline SVG icons.
- Each icon is selected by a `name` prop.
- The `size` and `strokeWidth` props let the same icon be reused at different sizes.

```html
<svg :width="size" :height="size" viewBox="0 0 24 24" ...>
  <g v-html="path"></g>
</svg>
```

Why:

- `:width` and `:height` use the `size` prop.
- `v-html="path"` injects the SVG path shape.
- Icons can be used anywhere without copying SVG code.

Available icons include `layers`, `dashboard`, `orders`, `products`, `customers`, `users`, `duplicates`, `logout`, `arrowLeft`, `arrowRight`, `lock`, `alert`, `check`, `plus`, `download`, and `mail`.

---

### `client/src/components/AuthShell.vue`

```html
<template>
  <div class="auth-layout">
    <div class="auth-card">
      <router-link to="/" class="brand">
        <span class="brand-mark"><Icon name="layers" :size="20" :stroke-width="2.5" /></span>
        <span class="brand-name">OrderSync</span>
      </router-link>
      <slot />
    </div>
  </div>
</template>
```

Why:

- `AuthShell` wraps public auth pages.
- It provides the same brand header and layout for login, register, forgot password, and reset password.
- The `<slot />` is where each page's form is injected.

Why it is a component instead of raw HTML on every page:

- Avoids duplication.
- Keeps the brand and layout in one place.
- Makes the public screens look consistent.

---

## 1.6 Layout

### `client/src/layouts/AppLayout.vue`

```js
const links = [
  { name: 'Reports', label: 'Dashboard', admin: true },
  { name: 'Orders', label: 'Orders', admin: true },
  { name: 'Products', label: 'Products', admin: true },
  { name: 'Customers', label: 'Customers', admin: true },
  { name: 'Users', label: 'Users', admin: true },
  { name: 'Duplicates', label: 'Duplicates', admin: true },
  { name: 'Totals', label: 'Totals', admin: true },
  { name: 'MyOrders', label: 'My Orders', admin: false, customerOnly: true },
]

const visibleLinks = () =>
  links.filter((link) => (auth.isAdmin ? link.admin : link.customerOnly))
```

Why:

- The nav links are data-driven.
- If the user is admin, they see admin links.
- If the user is a customer, they only see `MyOrders`.
- This avoids showing admin links to customers, even though the router guard is doing the real security.

```js
const handleLogout = () => {
  auth.logout()
  router.replace('/login')
}
```

Why:

- It clears the auth store and redirects the user to login.

```js
onMounted(() => {
  auth.fetchMe()
})
```

Why:

- When the app loads, it checks the current user.
- This refreshes the user object after the page loads.

```html
<header class="top-nav">
  <div class="nav-left">
    <router-link to="/" class="brand">
      <span class="brand-mark"><Icon name="layers" ... /></span>
      <span class="brand-name">OrderSync</span>
    </router-link>
    <nav class="nav-links" aria-label="Main navigation">
      <router-link v-for="link in visibleLinks()" :key="link.name" :to="...">
        {{ link.label }}
      </router-link>
    </nav>
  </div>
  <div class="nav-right">
    <div class="user-profile">
      <span class="role-badge">{{ auth.user?.role || 'Admin' }}</span>
      <div class="avatar">{{ (auth.user?.full_name || 'A').charAt(0).toUpperCase() }}</div>
    </div>
    <button class="logout-btn" title="Log out" @click="handleLogout">
      <Icon name="logout" :size="18" />
    </button>
  </div>
</header>
<main class="app-main">
  <router-view />
</main>
```

Why:

- `<router-view />` is the only thing that changes between `/app/orders`, `/app/reports`, `/app/users`, etc.
- The top nav stays fixed across pages.
- The user profile and logout button always stay visible.

---

## 1.7 Views

### `client/src/views/Landing.vue`

This is the public home page.

```js
const startPath = computed(() =>
  auth.isAuthenticated ? (auth.isAdmin ? '/app/reports' : '/app/my-orders') : '/login',
)
```

Why:

- If a user is logged in, `Go to app` sends them to their dashboard.
- If a customer logs in, they land at `/app/my-orders`.
- If they are admin, they land at `/app/reports`.
- If not logged in, they go to `/login`.

()` => import('@/views/Landing.vue')` means the page is loaded only when the user visits `/`.

---

### `client/src/views/Login.vue`

```js
const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const handleLogin = async () => {
  try {
    errorMsg.value = ''
    submitting.value = true
    await auth.login(email.value, password.value)
    router.push(auth.isAdmin ? '/app/reports' : '/app/my-orders')
  } catch (err) {
    errorMsg.value = err.response?.data?.error || 'Login failed'
  } finally {
    submitting.value = false
  }
}
```

Why:

- It reads the email and password from the form.
- It calls the auth store to send the request.
- If successful, it redirects to the right admin or customer dashboard.
- If it fails, it shows the backend error message.

```html
<form class="auth-form" @submit.prevent="handleLogin">
```

Why:

- `@submit.prevent` prevents the browser from doing a normal form submit, which would reload the page.
- Vue handles the submit with the JavaScript function instead.

---

### `client/src/views/Register.vue`

This view splits registration into two steps:

1. Details: email, password, full name, customer ID.
2. Verify email: enter the 6-digit OTP.

```js
const steps = ['Details', 'Verify email']
const activeStep = computed(() => step.value)
```

Why:

- It keeps the UI clean by showing one step at a time.
- It makes the registration flow easier to follow.

```js
const handleRegister = async () => {
  try {
    errorMsg.value = ''
    submitting.value = true
    await api.post('/auth/register', form.value)
    step.value = 2
    successMsg.value = 'Code sent. In development, read it from server/logs/dev_emails.log.'
  } catch (err) {
    errorMsg.value = err.response?.data?.error || 'Registration failed'
  } finally {
    submitting.value = false
  }
}
```

Why:

- It sends registration to the backend and then moves to the verification step.
- Registration does not create a verified account yet; the backend requires email verification.

```js
const handleVerify = async () => {
  try {
    errorMsg.value = ''
    submitting.value = true
    await api.post('/auth/verify', {
      email: form.value.email,
      code: code.value.trim(),
      customer_id: form.value.customer_id,
    })
    router.push('/login')
  } catch (err) {
    errorMsg.value = err.response?.data?.error || 'Verification failed'
  } finally {
    submitting.value = false
  }
}
```

Why:

- This sends the OTP code to the backend.
- If it succeeds, the user is directed to the login screen.

---

### `client/src/views/ForgotPassword.vue`

```js
const handleSubmit = async () => {
  try {
    message.value = ''
    errorMsg.value = ''
    submitting.value = true
    await api.post('/auth/forgot-password', { email: email.value })
    message.value =
      'If the email exists, a reset link was sent. Check server/logs/dev_emails.log in development.'
  } catch (err) {
    errorMsg.value = err.response?.data?.error || 'Something went wrong.'
  } finally {
    submitting.value = false
  }
}
```

Why:

- It sends the email to the backend.
- The backend returns a generic success response for both known and unknown emails.
- The frontend does not invent information about whether the email is registered.

---

### `client/src/views/ResetPassword.vue`

```js
const route = useRoute()
const token = route.query.token || ''
```

Why:

- The reset link from the backend contains a token like `/reset-password?token=...`.
- Vue Router makes this token available in `route.query.token`.

```js
const handleSubmit = async () => {
  try {
    errorMsg.value = ''
    submitting.value = true
    await api.post('/auth/reset-password', { token, new_password: password.value })
    router.push({ path: '/login', query: { reset: 'success' } })
  } catch (err) {
    errorMsg.value = err.response?.data?.error || 'Failed to reset password'
  } finally {
    submitting.value = false
  }
}
```

Why:

- It sends the token and new password to the backend.
- After success, it returns to `/login` with a query flag so the user knows they can sign in.

---

### `client/src/views/MyOrders.vue`

This is the customer-only order page.

```js
const customerId = computed(() => auth.user?.customer_id || null)
```

Why:

- Backend enforces that a customer only sees orders for their own linked customer.
- The UI also tells the user only their customer ID is visible.

```js
const deliveredShare = computed(() =>
  percent(countByStatus('Delivered'), orders.value.length),
)
```

Why:

- It calculates the percentage of delivered orders.
- If there are no orders, `percent()` already returns `0`, so it does not divide by zero.

```js
const fetchedOrders = async () => {
  loading.value = true
  errorMsg.value = ''
  try {
    await auth.fetchMe()
    const res = await api.get('/orders', { params: { per_page: 200 } })
    orders.value = res.data.orders
  } catch (err) {
    errorMsg.value = 'Failed to load your orders.'
  } finally {
    loading.value = false
  }
}
```

Why:

- It refreshes the authenticated user profile.
- It fetches the customer's own orders.
- The backend enforces visibility, so the REST call does not need extra client-side filtering.

---

### `client/src/views/Orders.vue`

This is the admin order list page.

```js
const orders = ref([])
const loading = ref(true)
const errorMsg = ref('')
const total = ref(0)
const pages = ref(1)
const page = ref(1)
const statusFilter = ref(route.query.status || '')
const search = ref('')
const updatingId = ref('')
```

Why:

- These are the reactive state variables that hold the current list of orders.
- Pagination is tracked separately from the backend pagination result.
- `updatingId` prevents the same order from being updated twice at once.

```js
const fetchOrders = async () => {
  loading.value = true
  errorMsg.value = ''
  try {
    const params = { page: page.value, per_page: 10 }
    if (statusFilter.value) params.status = statusFilter.value
    if (search.value.trim()) params.q = search.value.trim()
    const res = await api.get('/orders', { params })
    orders.value = res.data.orders
    total.value = res.data.total
    pages.value = res.data.pages || 1
    ...
  } catch (err) {
    errorMsg.value = err.response?.data?.error || 'Failed to load orders.'
  } finally {
    loading.value = false
  }
}
```

Why:

- It builds query parameters from the UI.
- It sends `page`, `per_page`, `status`, and `q`.
- It stores the server-side pagination result.
- Using `res.data.orders` keeps the Vue view in sync with the backend.

```js
const changeStatus = async (order, nextStatus) => {
  if (updatingId.value) return

  if (nextStatus === 'Returned' || nextStatus === 'Cancelled') {
    const ok = window.confirm(`Are you sure you want to mark ${order.order_id} as ${nextStatus}? This cannot be undone.`)
    if (!ok) return
  }

  try {
    updatingId.value = order.order_id
    await api.patch(`/orders/${order.order_id}/status`, { order_status: nextStatus })
    order.order_status = nextStatus
    summaryStore.fetch(true)
  } catch (err) {
    errorMsg.value = err.response?.data?.error || 'Failed to update status.'
  } finally {
    updatingId.value = ''
  }
}
```

Why:

- It prevents two simultaneous status clicks.
- It confirms destructive actions such as `Cancelled` and `Returned`.
- It patches the status on the server.
- It updates the local order row immediately.
- It forces the summary store to refresh so the dashboard reflects the changed order.

---

### `client/src/views/CreateOrder.vue`

```js
const form = ref({
  order_id: '',
  customer_id: '',
  order_date: new Date().toISOString().split('T')[0],
  product_id: '',
  quantity: 1,
})
```

Why:

- This is the data model for the order creation form.
- If no date is chosen, it defaults to today.
- `product_id` and `quantity` start as placeholders.

```js
onMounted(async () => {
  try {
    const [prodRes, custRes] = await Promise.all([
      api.get('/products'),
      api.get('/customers'),
    ])
    products.value = prodRes.data.products
    customers.value = custRes.data.customers
    ...
  } catch (err) {
    errorMsg.value = 'Failed to load products and customers.'
  } finally {
    loading.value = false
  }
})
```

Why:

- It loads both products and customers at the same time to avoid a slow two-step page load.
- `Promise.all` lets both requests run in parallel.

```js
const handleSubmit = async () => {
  try {
    errorMsg.value = ''
    submitting.value = true
    const payload = {
      order_id: form.value.order_id.trim().toUpperCase(),
      customer_id: form.value.customer_id,
      order_date: form.value.order_date,
      items: [
        {
          product_id: form.value.product_id,
          quantity: Number(form.value.quantity),
        },
      ],
    }
    const res = await api.post('/orders', payload)
    router.push(`/app/orders/${res.data.order_id}`)
  } catch (err) {
    const body = err.response?.data
    errorMsg.value =
      (body?.errors && body.errors.join(', ')) || body?.error || 'Failed to create order.'
  } finally {
    submitting.value = false
  }
}
```

Why:

- It builds the request payload.
- It does not send a client-side price. The backend uses the product price.
- If the backend returns validation errors, it shows them joined together.
- After success, it redirects to the new order detail page.

---

### `client/src/views/OrderDetail.vue`

This page shows one order and allows status changes.

```js
const allowedTransitions = {
  Pending: ['Received', 'Shipped', 'Cancelled'],
  Received: ['Shipped', 'Cancelled'],
  Shipped: ['Delivered', 'Returned'],
  Delivered: ['Returned'],
  Cancelled: [],
  Returned: [],
}
```

Why:

- This is the same state machine as the backend.
- It decides which buttons to show in the UI.
- It prevents users from seeing invalid status options.

```js
const fetchOrder = async () => {
  loading.value = true
  errorMsg.value = ''
  try {
    const res = await api.get(`/orders/${route.params.id}`)
    order.value = res.data
  } catch (err) {
    errorMsg.value =
      err.response?.status === 404
        ? 'Order not found, or you do not have access to it.'
        : 'Failed to load this order.'
  } finally {
    loading.value = false
  }
}
```

Why:

- The order is fetched from the backend.
- A `404` is shown if the order does not exist or the user cannot view it.
- This is how the app hides other customers' order IDs.

```js
const updateStatus = async (newStatus) => {
  if (updating.value) return
  try {
    updating.value = newStatus
    const res = await api.patch(`/orders/${order.value.order_id}/status`, {
      order_status: newStatus,
    })
    order.value.order_status = res.data.order_status
    summaryStore.fetch(true)
  } catch (err) {
    errorMsg.value = err.response?.data?.error || 'Failed to update status.'
  } finally {
    updating.value = ''
  }
}
```

Why:

- It patches the status on the backend.
- It updates the local order so the UI changes immediately.
- It refreshes the summary dashboard because revenue and status counts may change.

---

### `client/src/views/Reports.vue`

This is the admin-only dashboard report page.

```js
const summary = computed(() => summaryStore.data || {})
```

Why:

- If `summaryStore.data` is `null`, this returns an empty object so the template can still render without crashing.

```js
onMounted(async () => {
  try {
    await summaryStore.fetch(true)
    const monthly = (summary.value.monthly_breakdown || []).slice(-12)
    chartOptions.value.xaxis.categories = monthly.map((m) => m.period.slice(0, 7))
    chartSeries.value[0].data = monthly.map((m) => m.revenue)
  } catch (e) {
    errorMsg.value = 'Failed to load dashboard.'
  } finally {
    loading.value = false
  }
})
```

Why:

- It fetches the full summary.
- It takes the last 12 months for the revenue chart.
- It maps the monthly period labels and revenue values into ApexCharts format.

The page renders:

- KPI cards for revenue, sales orders, units sold, and awaiting action.
- An area chart for revenue over time.
- Latest orders.
- Duplicate groups.

---

### `client/src/views/Customers.vue`

This admin-only page manages customer records.

```js
const createCustomer = async () => {
  if (saving.value) return
  try {
    errorMsg.value = ''
    successMsg.value = ''
    saving.value = true
    await api.post('/customers', newCustomer.value)
    successMsg.value = 'Customer created.'
    showCreate.value = false
    newCustomer.value = { customer_id: '', cust_name: '', email: '' }
    await fetchCustomers()
  } catch (err) {
    errorMsg.value = err.response?.data?.error || 'Failed to create customer.'
  } finally {
    saving.value = false
  }
}
```

Why:

- It creates a customer record through the backend.
- It clears the form after success.
- It refreshes the customer list.

```js
const submitLink = async () => {
  if (!targetUserId.value) return
  try {
    errorMsg.value = ''
    successMsg.value = ''
    saving.value = true
    await api.patch(`/customers/${linkingCustomer.value.customer_id}/link`, {
      user_id: parseInt(targetUserId.value, 10),
    })
    successMsg.value = `Linked ${linkingCustomer.value.customer_id} to user ${targetUserId.value}.`
    linkingCustomer.value = null
    await fetchCustomers()
  } catch (err) {
    errorMsg.value = err.response?.data?.error || 'Failed to link customer.'
  } finally {
    saving.value = false
  }
}
```

Why:

- It links a user account to a customer record.
- The backend checks role, verification, and email matching.
- The client shows a simple link UI.

---

### `client/src/views/Products.vue`

This admin-only page manages the product catalog.

```js
const products = ref([])
const loading = ref(true)
```

Why:

- `products` holds the returned product list.
- `loading` shows the spinner.

```js
const fetchProducts = async () => {
  try {
    const res = await api.get('/products')
    products.value = res.data.products
  } catch (err) {
    errorMsg.value = 'Failed to load products.'
  } finally {
    loading.value = false
  }
}
```

Why:

- Backend lists products for dropdown and catalog pages.

```js
const savePrice = async (id) => {
  if (saving.value) return
  try {
    errorMsg.value = ''
    saving.value = true
    await api.patch(`/products/${id}`, { current_price: editPrice.value })
    successMsg.value = 'Price updated. New orders will use it; existing orders keep their price.'
    editId.value = null
    await fetchProducts()
  } catch (err) {
    errorMsg.value = err.response?.data?.error || 'Failed to update price.'
  } finally {
    saving.value = false
  }
}
```

Why:

- This is how an admin changes a product's current price.
- The backend ignores client-side price changes during order creation, but this endpoint lets admins change prices directly.

```js
const deleteProduct = async (product) => {
  if (!window.confirm(`Delete ${product.pro_name}? This cannot be undone.`)) return
  try {
    errorMsg.value = ''
    await api.delete(`/products/${product.product_id}`)
    successMsg.value = 'Product deleted.'
    await fetchProducts()
  } catch (err) {
    errorMsg.value = err.response?.data?.error || 'Failed to delete product.'
  }
}
```

Why:

- It asks the user to confirm before deleting.
- It deletes the product through the admin-only endpoint.

---

### `client/src/views/Duplicates.vue`

This admin-only page shows duplicate order groups.

```js
const duplicates = ref([])
const loading = ref(true)
```

Why:

- `duplicates` stores duplicate groups returned by `/orders/duplicates`.
- `loading` shows the spinner.

```js
const cancelCopy = async (group) => {
  const target = group.order_ids[0]
  if (!window.confirm(`Cancel ${target}? This keeps both records but moves the copy to Cancelled.`)) {
    return
  }
  try {
    errorMsg.value = ''
    cancelling.value = target
    await api.patch(`/orders/${target}/status`, { order_status: 'Cancelled' })
    successMsg.value = `${target} cancelled. The other copy is untouched.`
    await load()
  } catch (err) {
    errorMsg.value =
      err.response?.data?.error || 'Only Pending orders can be cancelled directly.'
  } finally {
    cancelling.value = ''
  }
}
```

Why:

- This lets an admin mark the first copy of a duplicate group as `Cancelled`.
- It does not delete the other copy.
- It fetches the latest duplicates after the change.

---

### `client/src/views/Users.vue`

This admin-only page manages users.

```js
const createUser = async () => {
  if (saving.value) return
  try {
    errorMsg.value = ''
    successMsg.value = ''
    saving.value = true
    await api.post('/users', newUser.value)
    successMsg.value = 'User created successfully.'
    showCreate.value = false
    newUser.value = { email: '', password: '', full_name: '', role: 'customer' }
    await fetchUsers()
  } catch (err) {
    errorMsg.value = err.response?.data?.error || 'Failed to create user.'
  } finally {
    saving.value = false
  }
}
```

Why:

- It creates a new user account.
- It resets the form after success so the user can create another account.
- It refreshes the user list.

---

### `client/src/views/Totals.vue`

This admin-only page shows the full lifetime totals report.

```js
const summary = computed(() => summaryStore.data || {})
```

Why:

- It safely returns an empty object when no data has been loaded yet.

```js
const products = computed(() =>
  (summary.value.product_breakdown || []).map((item) => ({
    ...item,
    share: percent(item.revenue, summary.value.revenue),
  }))
)
```

Why:

- It calculates the revenue share for each product from the backend summary data.
- It prevents a `null` crash when `product_breakdown` is empty.

```js
const statusRows = computed(() => {
  const rows = summary.value.status_breakdown || []
  const byStatus = Object.fromEntries(rows.map((row) => [row.status, row.count]))
  return ['Pending', 'Received', 'Shipped', 'Delivered', 'Cancelled', 'Returned'].map((status) => ({
    status,
    count: byStatus[status] || 0,
    share: percent(byStatus[status] || 0, totalOrders.value)
  }))
})
```

Why:

- It builds a stable sorted list of all statuses.
- It shows missing statuses even when they have zero count.
- It uses `percent()` so there is no division by zero.

```js
onMounted(async () => {
  await summaryStore.fetch(true)
  loading.value = false
})
```

Why:

- It fetches the report when the page opens.
- The `force = true` ensures new data is loaded, even if the store has a cached value.

---

## 1.8 Public pages and auth shell

### Login, Register, ForgotPassword, ResetPassword

All of these pages follow the same pattern:

```html
<AuthShell>
  ...
</AuthShell>
```

Why:

- `AuthShell` gives them the same brand header, centering, and layout.
- The slot contains only the page-specific form.

Common rules in these pages:

- Use `v-model` for form fields.
- Use `@submit.prevent` to stop the browser from reloading the page.
- Show `errorMsg.value` when `err.response?.data?.error` exists.
- Show `successMsg.value` when the backend confirms the action.
- Use `error.response?.data?.error` to get a useful message from Flask.

---

## 1.9 How the frontend components call the backend

```text
Vue component
  -> Pinia store action
    -> api.js Axios instance
      -> axios.request()
        -> Vite proxy
          -> Flask route
            -> service / model / database
              -> JSON response
                -> store
                  -> component
```

Example for login:

```text
Login.vue
  -> auth.login(email, password)
    -> api.post('/auth/login', {...})
      -> Flask: POST /api/auth/login
        -> auth.py route
          -> auth_service.login()
            -> PostgreSQL user table
              -> returns access_token
```

Example for orders:

```text
Orders.vue
  -> api.get('/orders', { params })
    -> Flask: GET /api/orders
      -> orders.py route
        -> order_service.visible_orders_for(user)
          -> PostgreSQL orders table
              -> returns JSON
```

---

## 1.10 How the frontend keeps security

1. **Route guards** check `auth.isAuthenticated` and `auth.isAdmin`.
2. **Vue Router redirects** the user before rendering the protected page.
3. **API interceptors** check `401` and `422`.
4. **Auth store** stores the token and user.
5. **Admin-only pages** redirect non-admins to `/app/orders`.
6. **Customer-only pages** redirect admins to `/app/orders`.

Important:

- The frontend guards improve UX, but they do not replace backend security.
- The backend still enforces these rules with decorators and database queries.
- A user cannot bypass protection by typing a URL directly.

---

# 2. Backend (`server/`)

The backend explanation is unchanged from the earlier review.

---

## `server/app/__init__.py`

- `create_app()` builds the Flask app.
- It loads configuration.
- It initializes `db`, `jwt`, and `mail`.
- It registers blueprints for `/api/auth`, `/api/orders`, `/api/reports`, `/api/products`, `/api/customers`, and `/api/users`.

---

## `server/app/config.py`

- Loads `.env` or `.env.test`.
- Reads `DATABASE_URL`, `JWT_SECRET_KEY`, `JWT_ACCESS_TOKEN_EXPIRES_HOURS`, and token TTLs.
- Configures SQLAlchemy, JWT, and mail.

---

## `server/app/constants.py`

- Defines `Role.ADMIN` and `Role.CUSTOMER`.
- Provides helper methods for role values.

---

## `server/app/extensions.py`

- Creates `db`, `jwt`, and `mail` singletons.
- Also exports `hash_password` and `verify_password` helpers.

---

## `server/app/models.py`

- Defines SQLAlchemy models for `User`, `Customer`, `Product`, `Order`, and `OrderItem`.
- Contains relationships and `to_dict()` helpers.

---

## `server/app/utils/decorators.py`

- `auth_required` checks a valid JWT.
- `role_required` checks the required role.
- Both load the current user and store it in `g.current_user`.
- They support token revocation through `token_version`.

---

## `server/app/utils/permissions.py`

- Contains helpers like `can_view_order()` and `owns_customer()`.
- Used by the routes to enforce visibility rules.

---

## `server/app/services/auth_service.py`

Business logic for accounts:

- registration, email verification, login, password reset, user linking.

---

## `server/app/services/order_service.py`

Business logic for orders:

- validation
- creation
- visibility scope
- status transitions
- duplicate detection
- sales reports

---

## `server/app/routes`

Thin HTTP controllers:

- `auth.py`
- `orders.py`
- `products.py`
- `customers.py`
- `reports.py`
- `users.py`

They read requests, call services, and return JSON.

---

## `server/app/tests`

Pytest suite:

- `test_auth.py`
- `test_orders.py`
- `test_permissions.py`
- `test_pricing.py`
- `test_reports.py`
- `test_smoke.py`

---

# 3. Data flow summary

```text
Browser
  -> Vue SPA
    -> Pinia store
      -> api.js
        -> Flask route
          -> Service
            -> SQLAlchemy / PostgreSQL
              -> JSON
                -> store
                  -> Vue component
```

Every endpoint in the app follows this same pattern:

```text
HTTP request -> route -> service -> models/database -> JSON response
```

---

# 4. Important file locations

```text
client/src/main.js
  -> entry point

client/src/router/index.js
  -> routes and guards

client/src/services/api.js
  -> HTTP client

client/src/stores/auth.js
  -> authentication state and actions

client/src/stores/summary.js
  -> report dashboard state

client/src/views/*.vue
  -> screens such as Login, Orders, Reports, Totals

client/src/layouts/AppLayout.vue
  -> dashboard layout and navigation

client/src/components/
  -> Icon.vue, AuthShell.vue

client/src/utils/format.js
  -> formatting helpers

client/src/style.css
  -> global CSS variables and base styles
```

---

# 5. What changed in this explanation

The previous version focused heavily on backend files. This version adds:

1. `client/main.js`
2. `client/index.html`
3. `client/src/App.vue`
4. `client/src/router/index.js`
5. `client/src/services/api.js`
6. `client/src/stores/auth.js`
7. `client/src/stores/summary.js`
8. `client/src/utils/format.js`
9. `client/src/style.css`
10. `client/src/components/Icon.vue`
11. `client/src/components/AuthShell.vue`
12. `client/src/layouts/AppLayout.vue`
13. `client/src/views/Login.vue`, `Register.vue`, `ForgotPassword.vue`, `ResetPassword.vue`, `MyOrders.vue`, `Orders.vue`, `CreateOrder.vue`, `OrderDetail.vue`, `Reports.vue`, `Customers.vue`, `Products.vue`, `Duplicates.vue`, `Users.vue`, `Totals.vue`

Each frontend file now includes:

- what the code does
- why it was written that way
- where it fits in the request flow


A complete architecture and flow of whole web application
