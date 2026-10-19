# apply_changes.ps1 - run from the PROJECT ROOT (the folder that contains "client" and "server")
#   powershell -ExecutionPolicy Bypass -File .\apply_changes.ps1
$ErrorActionPreference = 'Stop'
if (-not (Test-Path (Join-Path $PWD 'client\src')) -or -not (Test-Path (Join-Path $PWD 'server\app'))) {
  throw 'Run this from the project root (the folder containing client and server).'
}
$utf8 = New-Object System.Text.UTF8Encoding($false)

function Write-Utf8($rel, $text) {
  [System.IO.File]::WriteAllText((Join-Path $PWD $rel), $text.TrimEnd() + "`n", $utf8)
  Write-Host "  wrote $rel"
}
function Edit-Literal($rel, $old, $new) {
  $p = Join-Path $PWD $rel
  $t = [System.IO.File]::ReadAllText($p)
  if ($t.Contains($new)) { Write-Host "  already patched: $rel"; return }
  if (-not $t.Contains($old)) { throw "Anchor not found in $rel :: $old" }
  [System.IO.File]::WriteAllText($p, $t.Replace($old, $new), $utf8)
  Write-Host "  patched $rel"
}

# 0. Backups
$bk = Join-Path $PWD ('_backup_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
New-Item -ItemType Directory -Path $bk | Out-Null
foreach ($f in 'client\src\views\Reports.vue','client\src\layouts\AppLayout.vue','client\src\views\Orders.vue','server\app\routes\customers.py','server\app\services\order_service.py') {
  Copy-Item (Join-Path $PWD $f) (Join-Path $bk (Split-Path $f -Leaf))
}
Write-Host "Backups in $bk"

# 1. Backend: customers list is admin-only
Write-Host '[1/5] customers.py'
$p = Join-Path $PWD 'server\app\routes\customers.py'
$t = [System.IO.File]::ReadAllText($p)
$re = [regex]'@auth_required(\r?\n)def list_customers'
if ($re.IsMatch($t)) {
  [System.IO.File]::WriteAllText($p, $re.Replace($t, '@role_required(Role.ADMIN.value)$1def list_customers', 1), $utf8)
  Write-Host '  patched server\app\routes\customers.py'
} else { Write-Host '  already patched or not found: customers.py' }

# 2. Backend: status_counts in dashboard summary
Write-Host '[2/5] order_service.py'
Edit-Literal 'server\app\services\order_service.py' 'duplicates = find_duplicates()[:3]' @'
duplicates = find_duplicates()[:3]

    status_counts = {s: 0 for s in VALID_STATUSES}
    for status, cnt in (
        db.session.query(Order.order_status, func.count(Order.order_id))
        .group_by(Order.order_status)
        .all()
    ):
        status_counts[status] = int(cnt)
'@
Edit-Literal 'server\app\services\order_service.py' '"awaiting_action": int(awaiting_action),' @'
"awaiting_action": int(awaiting_action),
        "status_counts": status_counts,
'@

# 3. Frontend: Dashboard (Bento + percentages)
Write-Host '[3/5] Reports.vue'
Write-Utf8 'client\src\views\Reports.vue' @'
<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

const summary = ref(null)
const loading = ref(true)
const errorMsg = ref('')
const dateGroup = ref('month')

const RUPEE = '\u20B9'
const money = (n) =>
  RUPEE + Number(n || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
const pct = (n, d) => (d ? ((n / d) * 100).toFixed(1) : '0.0') + '%'

const STATUS_ORDER = ['Pending', 'Received', 'Shipped', 'Delivered', 'Cancelled', 'Returned']
const STATUS_COLORS = {
  Pending: '#F59E0B', Received: '#3B82F6', Shipped: '#6366F1',
  Delivered: '#10B981', Cancelled: '#EF4444', Returned: '#EC4899',
}
const PILLS = {
  Pending: ['#FEF3C7', '#92400E'], Received: ['#DBEAFE', '#1E40AF'], Shipped: ['#E0E7FF', '#3730A3'],
  Delivered: ['#D1FAE5', '#065F46'], Cancelled: ['#FEE2E2', '#991B1B'], Returned: ['#FCE7F3', '#9D174D'],
}
const PRODUCT_COLORS = ['#2F5BFF', '#C6F432', '#FF8A4C', '#0B1020', '#9AA7FF', '#C9CED9']

const statusRows = computed(() => {
  const counts = summary.value?.status_counts || {}
  const total = STATUS_ORDER.reduce((s, k) => s + (counts[k] || 0), 0)
  return STATUS_ORDER.map((k) => ({
    label: k,
    n: counts[k] || 0,
    pct: pct(counts[k] || 0, total),
    w: total ? ((counts[k] || 0) / total) * 100 : 0,
    color: STATUS_COLORS[k],
  }))
})
const totalOrders = computed(() => statusRows.value.reduce((s, r) => s + r.n, 0))

const monthly = computed(() => {
  const m = summary.value?.monthly_breakdown || []
  const max = Math.max(...m.map((x) => x.revenue), 1)
  return m.map((x) => ({
    key: x.period.slice(0, 7),
    h: (x.revenue / max) * 100,
    hi: x.revenue >= max * 0.55,
    tip: x.period.slice(0, 7) + ' - ' + money(x.revenue),
  }))
})

const productRows = computed(() => {
  const rev = summary.value?.revenue || 0
  const list = summary.value?.product_breakdown || []
  const rows = list.slice(0, 5).map((p, i) => ({
    name: p.product, revenue: p.revenue, pct: pct(p.revenue, rev), color: PRODUCT_COLORS[i],
  }))
  const rest = list.slice(5)
  if (rest.length) {
    const r = rest.reduce((s, p) => s + p.revenue, 0)
    rows.push({ name: 'Others', revenue: r, pct: pct(r, rev), color: PRODUCT_COLORS[5] })
  }
  return rows
})

const donutStyle = computed(() => {
  const rev = summary.value?.revenue || 0
  if (!rev) return { background: '#E5E7EB' }
  let acc = 0
  const stops = productRows.value.map((p) => {
    const a = (acc / rev) * 100
    acc += p.revenue
    return `${p.color} ${a.toFixed(2)}% ${((acc / rev) * 100).toFixed(2)}%`
  })
  return { background: `conic-gradient(${stops.join(', ')})` }
})

const latest = computed(() =>
  (summary.value?.latest_orders || []).map((o) => ({
    ...o,
    bg: (PILLS[o.order_status] || ['#EEE', '#333'])[0],
    fg: (PILLS[o.order_status] || ['#EEE', '#333'])[1],
  }))
)
const dupGroups = computed(() => summary.value?.duplicate_groups || [])

onMounted(async () => {
  try {
    const res = await api.get('/reports/summary')
    summary.value = res.data
  } catch (err) {
    errorMsg.value = 'Failed to load dashboard data.'
  } finally {
    loading.value = false
  }
})

const downloadReport = (type) => {
  let url = `/api/reports/${type}?format=csv`
  if (type === 'date-wise') url += `&group=${dateGroup.value}`
  const tag = type === 'date-wise' ? `date_wise_${dateGroup.value}` : 'product_wise'

  fetch(url, { headers: { Authorization: `Bearer ${auth.token}` } })
    .then((res) => {
      if (!res.ok) throw new Error('Download failed')
      return res.blob()
    })
    .then((blob) => {
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = `${tag}_report_${new Date().toISOString().slice(0, 10)}.csv`
      link.click()
      URL.revokeObjectURL(link.href)
    })
    .catch((err) => {
      console.error(err)
      alert('Failed to download report')
    })
}
</script>

<template>
  <div v-if="loading" class="bn-state">Loading dashboard...</div>
  <div v-else-if="errorMsg" class="bn-state bn-error">{{ errorMsg }}</div>

  <div v-else class="bn">
    <div class="bn-head">
      <h2>Sales reports</h2>
      <div class="bn-actions">
        <div class="bn-seg" role="group" aria-label="Date-wise grouping">
          <button :class="{ on: dateGroup === 'day' }" @click="dateGroup = 'day'">Day</button>
          <button :class="{ on: dateGroup === 'month' }" @click="dateGroup = 'month'">Month</button>
        </div>
        <button class="bn-pill" @click="downloadReport('date-wise')">Date-wise CSV</button>
        <button class="bn-pill" @click="downloadReport('product-wise')">Product-wise CSV</button>
      </div>
    </div>

    <section class="bn-row">
      <div class="bn-tile bn-dark bn-grow2">
        <div class="bn-split">
          <div>
            <div class="bn-sub">Revenue &middot; Shipped + Delivered</div>
            <div class="bn-hero">{{ money(summary.revenue) }}</div>
          </div>
        </div>
        <div>
          <div class="bn-bars">
            <div v-for="b in monthly" :key="b.key" :title="b.tip" class="bn-bar"
                 :style="{ height: b.h + '%', background: b.hi ? '#C6F432' : '#4A5580' }"></div>
          </div>
          <div class="bn-axis" v-if="monthly.length">
            <span>{{ monthly[0].key }}</span>
            <span>{{ monthly[Math.floor(monthly.length / 2)].key }}</span>
            <span>{{ monthly[monthly.length - 1].key }}</span>
          </div>
        </div>
      </div>

      <div class="bn-col">
        <div class="bn-tile bn-blue">
          <div class="bn-sub">Sales orders</div>
          <div class="bn-big">{{ pct(summary.sales_orders, totalOrders) }}</div>
          <div class="bn-mono">{{ summary.sales_orders.toLocaleString() }} of {{ totalOrders.toLocaleString() }} orders</div>
        </div>
        <div class="bn-tile bn-white">
          <div class="bn-sub bn-muted">Units sold</div>
          <div class="bn-big">{{ summary.units_sold.toLocaleString() }}</div>
          <div class="bn-mono bn-muted">across {{ summary.product_breakdown.length }} products</div>
        </div>
      </div>

      <div class="bn-col">
        <div class="bn-tile bn-orange">
          <div class="bn-sub">Awaiting action</div>
          <div class="bn-big">{{ pct(summary.awaiting_action, totalOrders) }}</div>
          <router-link class="bn-link" to="/app/orders?status=Pending">
            {{ summary.awaiting_action.toLocaleString() }} of {{ totalOrders.toLocaleString() }} orders &rarr;
          </router-link>
        </div>
        <div class="bn-tile bn-yellow">
          <div class="bn-sub"><strong>{{ dupGroups.length ? dupGroups.length + (dupGroups.length >= 3 ? '+' : '') + ' duplicate group' + (dupGroups.length > 1 ? 's' : '') : 'No duplicates' }}</strong></div>
          <template v-if="dupGroups.length">
            <div class="bn-small">{{ dupGroups[0].customer_id }} &middot; Product {{ dupGroups[0].product_id }} &middot; {{ money(dupGroups[0].unit_price) }} &middot; {{ dupGroups[0].order_date }}</div>
            <div class="bn-chips"><span v-for="id in dupGroups[0].order_ids" :key="id">{{ id }}</span></div>
            <router-link class="bn-link" to="/app/duplicates">Review &rarr;</router-link>
          </template>
          <div v-else class="bn-small">All orders are unique.</div>
        </div>
      </div>
    </section>

    <section class="bn-row">
      <div class="bn-tile bn-white bn-grow1">
        <h3>Revenue by product</h3>
        <div class="bn-donutrow">
          <div class="bn-donut" :style="donutStyle">
            <div class="bn-donut-hole">
              <span class="bn-muted">{{ summary.product_breakdown.length }} products</span>
              <strong>{{ money(summary.revenue) }}</strong>
            </div>
          </div>
          <div class="bn-legend">
            <div v-for="p in productRows" :key="p.name" class="bn-legrow">
              <span class="bn-dot" :style="{ background: p.color }"></span>
              <span class="bn-legname">{{ p.name }}</span>
              <span class="bn-mono bn-muted">{{ p.pct }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="bn-tile bn-white bn-grow1">
        <h3>Order status</h3>
        <div class="bn-stack">
          <div v-for="s in statusRows" :key="s.label" :style="{ width: s.w + '%', background: s.color }"></div>
        </div>
        <div class="bn-legend">
          <div v-for="s in statusRows" :key="s.label" class="bn-legrow">
            <span class="bn-dot" :style="{ background: s.color }"></span>
            <span class="bn-legname">{{ s.label }}</span>
            <span class="bn-mono">{{ s.pct }}</span>
            <span class="bn-mono bn-muted bn-count">{{ s.n.toLocaleString() }}</span>
          </div>
        </div>
      </div>
    </section>

    <section class="bn-tile bn-white">
      <div class="bn-split">
        <h3>Latest orders</h3>
        <router-link class="bn-link bn-blue-text" to="/app/orders">View all &rarr;</router-link>
      </div>
      <div class="bn-list">
        <div v-for="o in latest" :key="o.order_id" class="bn-item">
          <router-link :to="`/app/orders/${o.order_id}`" class="bn-mono bn-id">{{ o.order_id }}</router-link>
          <span class="bn-muted bn-cust">{{ o.customer_id }}</span>
          <span class="bn-muted bn-date">{{ o.order_date }}</span>
          <span class="bn-status" :style="{ background: o.bg, color: o.fg }">{{ o.order_status }}</span>
          <span class="bn-mono bn-total">{{ money(o.total) }}</span>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.bn { display: flex; flex-direction: column; gap: 20px; color: #0B1020; }
.bn-state { padding: 40px; text-align: center; color: #5B6478; }
.bn-error { color: #991B1B; }
.bn-head { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 12px; }
.bn-head h2 { margin: 0; font-size: 20px; font-weight: 700; }
.bn-actions { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; }
.bn-seg { display: flex; background: #FFFFFF; border-radius: 99px; padding: 4px; }
.bn-seg button { border: 0; background: transparent; padding: 7px 14px; border-radius: 99px; font-size: 12px; font-weight: 700; color: #5B6478; cursor: pointer; }
.bn-seg button.on { background: #0B1020; color: #FFFFFF; }
.bn-pill { border: 1px solid #D5DAE6; background: #FFFFFF; border-radius: 99px; padding: 9px 16px; font-size: 12px; font-weight: 700; color: #0B1020; cursor: pointer; }
.bn-row { display: flex; flex-wrap: wrap; gap: 20px; }
.bn-col { flex: 1 1 280px; min-width: 0; display: flex; flex-direction: column; gap: 20px; }
.bn-grow2 { flex: 2 1 520px; }
.bn-grow1 { flex: 1 1 380px; }
.bn-tile { box-sizing: border-box; min-width: 0; border-radius: 28px; padding: 26px 30px; display: flex; flex-direction: column; justify-content: space-between; gap: 14px; }
.bn-col .bn-tile { flex: 1; }
.bn-tile h3 { margin: 0; font-size: 17px; font-weight: 700; }
.bn-dark { background: #0B1020; color: #FFFFFF; gap: 28px; }
.bn-blue { background: #2F5BFF; color: #FFFFFF; }
.bn-white { background: #FFFFFF; }
.bn-orange { background: #FF8A4C; color: #2B1200; }
.bn-yellow { background: #FFE9A8; color: #4A3500; }
.bn-sub { font-size: 14px; font-weight: 500; opacity: 0.85; }
.bn-muted { color: #5B6478; opacity: 1; }
.bn-dark .bn-sub { color: #A5ADC2; opacity: 1; }
.bn-hero { font-size: 56px; font-weight: 800; letter-spacing: -2.5px; line-height: 1.05; margin-top: 8px; color: #C6F432; }
.bn-big { font-size: 48px; font-weight: 800; letter-spacing: -2px; }
.bn-mono { font-family: ui-monospace, 'IBM Plex Mono', Consolas, monospace; font-size: 12px; }
.bn-small { font-size: 13px; line-height: 1.5; }
.bn-split { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.bn-bars { display: flex; align-items: flex-end; gap: 4px; height: 120px; }
.bn-bar { flex: 1; border-radius: 3px; min-height: 2px; }
.bn-axis { display: flex; justify-content: space-between; font-family: ui-monospace, Consolas, monospace; font-size: 11px; color: #A5ADC2; margin-top: 10px; }
.bn-link { font-size: 13px; font-weight: 700; color: inherit; text-decoration: none; }
.bn-blue-text { color: #2F5BFF; }
.bn-chips { display: flex; flex-wrap: wrap; gap: 8px; }
.bn-chips span { font-family: ui-monospace, Consolas, monospace; font-size: 12px; font-weight: 600; background: #FFFFFF; padding: 4px 10px; border-radius: 99px; }
.bn-donutrow { display: flex; flex-wrap: wrap; align-items: center; gap: 28px; }
.bn-donut { position: relative; width: 176px; height: 176px; flex: 0 0 176px; border-radius: 50%; }
.bn-donut-hole { position: absolute; inset: 32px; border-radius: 50%; background: #FFFFFF; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; font-size: 11px; }
.bn-donut-hole strong { font-size: 14px; font-weight: 800; }
.bn-legend { flex: 1 1 180px; display: flex; flex-direction: column; gap: 10px; }
.bn-legrow { display: flex; align-items: center; gap: 10px; font-size: 13px; }
.bn-legname { flex: 1; font-weight: 600; }
.bn-count { width: 44px; text-align: right; }
.bn-dot { width: 10px; height: 10px; border-radius: 3px; flex: 0 0 10px; }
.bn-stack { display: flex; height: 16px; border-radius: 99px; overflow: hidden; gap: 2px; }
.bn-list { display: flex; flex-direction: column; }
.bn-item { display: flex; flex-wrap: wrap; align-items: center; gap: 14px; padding: 13px 0; border-top: 1px solid #EEF0F5; font-size: 13px; }
.bn-id { width: 92px; font-weight: 600; color: #0B1020; text-decoration: none; }
.bn-cust { width: 60px; }
.bn-date { flex: 1 1 90px; }
.bn-status { padding: 4px 12px; border-radius: 99px; font-size: 12px; font-weight: 700; }
.bn-total { width: 110px; text-align: right; font-weight: 600; }
</style>
'@

# 4. Frontend: layout with Totals column
Write-Host '[4/5] AppLayout.vue'
Write-Utf8 'client\src\layouts\AppLayout.vue' @'
<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter, useRoute } from 'vue-router'
import api from '@/services/api'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const handleLogout = () => {
  auth.logout()
  router.replace('/login')
}

const TITLES = { CreateOrder: 'Create Order', OrderDetail: 'Order Detail' }
const pageTitle = computed(() => TITLES[route.name] || route.name)
const greeting = computed(() => {
  const h = new Date().getHours()
  return h < 12 ? 'Good morning' : h < 17 ? 'Good afternoon' : 'Good evening'
})

const RUPEE = '\u20B9'
const money = (n) =>
  RUPEE + Number(n || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
const pct = (n, d) => (d ? ((n / d) * 100).toFixed(1) : '0.0') + '%'

const totals = ref(null)
const loadTotals = async () => {
  if (!auth.isAdmin) return
  try {
    const res = await api.get('/reports/summary')
    totals.value = res.data
  } catch (e) {
    totals.value = null
  }
}
onMounted(loadTotals)
watch(() => route.fullPath, loadTotals)

const allOrders = computed(() =>
  Object.values(totals.value?.status_counts || {}).reduce((a, b) => a + b, 0)
)
const productTotals = computed(() =>
  (totals.value?.product_breakdown || []).map((p) => ({
    name: p.product,
    units: p.units,
    revenue: p.revenue,
    share: pct(p.revenue, totals.value.revenue),
    w: totals.value.revenue ? (p.revenue / totals.value.revenue) * 100 : 0,
  }))
)
</script>

<template>
  <div class="app-layout">
    <aside class="sidebar">
      <div class="logo">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
      </div>
      <nav>
        <router-link v-if="auth.isAdmin" to="/app/reports" title="Dashboard" class="nav-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>
        </router-link>
        <router-link to="/app/orders" title="Orders" class="nav-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line></svg>
        </router-link>
        <router-link v-if="auth.isAdmin" to="/app/products" title="Products" class="nav-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 7h-9m3 10H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2z"></path><circle cx="12" cy="12" r="3"></circle></svg>
        </router-link>
        <router-link v-if="auth.isAdmin" to="/app/customers" title="Customers" class="nav-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle></svg>
        </router-link>
        <router-link v-if="auth.isAdmin" to="/app/duplicates" title="Duplicates" class="nav-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
        </router-link>
      </nav>
      <button class="logout-btn" @click="handleLogout" title="Logout">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>
      </button>
    </aside>

    <aside v-if="auth.isAdmin && totals" class="totals" aria-label="Totals">
      <h2>Totals</h2>

      <div class="t-revenue">
        <span class="t-label">Revenue</span>
        <strong>{{ money(totals.revenue) }}</strong>
        <span class="t-note">100% of sales (Shipped + Delivered)</span>
      </div>

      <div class="t-pair">
        <div>
          <span class="t-label">Sales orders</span>
          <strong>{{ pct(totals.sales_orders, allOrders) }}</strong>
          <span class="t-note">{{ totals.sales_orders.toLocaleString() }} of {{ allOrders.toLocaleString() }}</span>
        </div>
        <div>
          <span class="t-label">Awaiting</span>
          <strong>{{ pct(totals.awaiting_action, allOrders) }}</strong>
          <span class="t-note">{{ totals.awaiting_action.toLocaleString() }} of {{ allOrders.toLocaleString() }}</span>
        </div>
      </div>

      <div class="t-table">
        <div class="t-row t-headrow"><span>Product</span><span>Units</span><span>Revenue</span><span>%</span></div>
        <div v-for="p in productTotals" :key="p.name" class="t-item">
          <div class="t-row">
            <span class="t-name">{{ p.name }}</span>
            <span>{{ p.units.toLocaleString() }}</span>
            <span>{{ money(p.revenue) }}</span>
            <span class="t-pct">{{ p.share }}</span>
          </div>
          <div class="t-bar"><div :style="{ width: p.w + '%' }"></div></div>
        </div>
        <div class="t-row t-foot">
          <span class="t-name">Total</span>
          <span>{{ totals.units_sold.toLocaleString() }}</span>
          <span>{{ money(totals.revenue) }}</span>
          <span class="t-pct">100%</span>
        </div>
      </div>
    </aside>

    <main class="main-content">
      <header class="topbar">
        <div class="header-left">
          <h1 v-if="route.name === 'Reports'">{{ greeting }}, {{ auth.user?.full_name?.split(' ')[0] || 'Admin' }}</h1>
          <h1 v-else>{{ pageTitle }}</h1>
          <p class="subtitle" v-if="route.name === 'Reports'">Here is how orders and sales look today.</p>
        </div>

        <div class="header-right">
          <button v-if="auth.isAdmin" class="btn-primary" @click="router.push('/app/new-order')">New order</button>
          <div class="avatar">{{ auth.user?.full_name?.charAt(0) || 'A' }}</div>
        </div>
      </header>

      <div class="page-container">
        <router-view />
      </div>
    </main>
  </div>
</template>

<style scoped>
.app-layout { display: flex; min-height: 100vh; background: #EBEEF5; }
.sidebar { width: 88px; flex: 0 0 88px; background: white; display: flex; flex-direction: column; align-items: center; padding: 32px 0; border-right: 1px solid var(--border-color); }
.logo { width: 44px; height: 44px; background: #0B1020; color: #C6F432; border-radius: 12px; display: flex; align-items: center; justify-content: center; margin-bottom: 48px; }
nav { display: flex; flex-direction: column; gap: 12px; flex: 1; }
.nav-icon { width: 48px; height: 48px; display: flex; align-items: center; justify-content: center; border-radius: 12px; color: var(--text-secondary); transition: 0.2s; }
.nav-icon:hover { background: var(--bg-app); color: var(--text-primary); }
.nav-icon.router-link-active { background: #0B1020; color: #C6F432; }
.logout-btn { background: transparent; padding: 12px; color: var(--text-secondary); border-radius: 12px; transition: 0.2s; }
.logout-btn:hover { background: #FEE2E2; color: #991B1B; }

.totals { width: 300px; flex: 0 0 300px; box-sizing: border-box; background: #0B1020; color: #FFFFFF; padding: 32px 22px; display: flex; flex-direction: column; gap: 22px; overflow-y: auto; max-height: 100vh; position: sticky; top: 0; }
.totals h2 { margin: 0; font-size: 13px; letter-spacing: 1.2px; text-transform: uppercase; color: #A5ADC2; font-weight: 700; }
.t-revenue { display: flex; flex-direction: column; gap: 4px; }
.t-revenue strong { font-size: 30px; font-weight: 800; letter-spacing: -1px; color: #C6F432; }
.t-label { font-size: 12px; color: #A5ADC2; font-weight: 600; }
.t-note { font-size: 11px; color: #7F89A3; }
.t-pair { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.t-pair > div { background: #161C32; border-radius: 14px; padding: 12px 14px; display: flex; flex-direction: column; gap: 3px; }
.t-pair strong { font-size: 22px; font-weight: 800; letter-spacing: -0.5px; }
.t-table { display: flex; flex-direction: column; gap: 10px; }
.t-row { display: grid; grid-template-columns: 1.3fr 0.7fr 1.3fr 0.8fr; gap: 6px; font-size: 12px; align-items: baseline; }
.t-row span:nth-child(n+2) { text-align: right; font-family: ui-monospace, Consolas, monospace; }
.t-headrow { color: #7F89A3; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.6px; }
.t-name { font-weight: 600; }
.t-pct { color: #C6F432; font-weight: 700; }
.t-bar { height: 4px; border-radius: 99px; background: #1E2540; margin-top: 5px; }
.t-bar div { height: 4px; border-radius: 99px; background: #C6F432; }
.t-foot { border-top: 1px solid #2B3350; padding-top: 12px; font-weight: 800; }

.main-content { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.topbar { display: flex; justify-content: space-between; align-items: flex-start; padding: 40px 48px 24px 48px; }
.header-left h1 { font-size: 28px; font-weight: 700; margin-bottom: 6px; letter-spacing: -0.5px; }
.subtitle { color: var(--text-secondary); font-size: 15px; }
.header-right { display: flex; align-items: center; gap: 16px; }
.avatar { width: 44px; height: 44px; border-radius: 50%; background: #1A1D21; color: white; display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: 16px; }
.page-container { padding: 0 48px 48px 48px; max-width: 1600px; width: 100%; margin: 0 auto; box-sizing: border-box; }

@media (max-width: 1280px) { .totals { display: none; } }
</style>
'@

# 5. Frontend: Orders with status buttons
Write-Host '[5/5] Orders.vue'
Write-Utf8 'client\src\views\Orders.vue' @'
<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const orders = ref([])
const loading = ref(true)
const errorMsg = ref('')
const notice = ref('')
const busyId = ref('')
const statusFilter = ref(typeof route.query.status === 'string' ? route.query.status : '')
const page = ref(1)
const total = ref(0)
const pages = ref(1)

// Mirrors ALLOWED_TRANSITIONS in server/app/services/order_service.py
const NEXT = {
  Pending: [
    { to: 'Received', label: 'Receive' },
    { to: 'Shipped', label: 'Ship' },
    { to: 'Cancelled', label: 'Cancel', danger: true },
  ],
  Received: [
    { to: 'Shipped', label: 'Ship' },
    { to: 'Cancelled', label: 'Cancel', danger: true },
  ],
  Shipped: [
    { to: 'Delivered', label: 'Deliver' },
    { to: 'Returned', label: 'Return', danger: true },
  ],
  Delivered: [{ to: 'Returned', label: 'Return', danger: true }],
}
const actionsFor = (status) => NEXT[status] || []

const fetchOrders = async () => {
  loading.value = true
  errorMsg.value = ''
  try {
    let url = `/orders?page=${page.value}&per_page=15`
    if (statusFilter.value) url += `&status=${statusFilter.value}`
    const res = await api.get(url)
    orders.value = res.data.orders
    total.value = res.data.total
    pages.value = res.data.pages
  } catch (err) {
    errorMsg.value = 'Failed to load orders.'
  } finally {
    loading.value = false
  }
}

const changeStatus = async (order, action) => {
  if (action.danger && !confirm(`${action.label} order ${order.order_id}? This cannot be undone.`)) return
  busyId.value = order.order_id
  notice.value = ''
  errorMsg.value = ''
  try {
    await api.patch(`/orders/${order.order_id}/status`, { order_status: action.to })
    await fetchOrders()
    notice.value = `${order.order_id} is now ${action.to}`
  } catch (err) {
    errorMsg.value = err.response?.data?.error || 'Failed to update status'
  } finally {
    busyId.value = ''
  }
}

const nextPage = () => { if (page.value < pages.value) { page.value++; fetchOrders() } }
const prevPage = () => { if (page.value > 1) { page.value--; fetchOrders() } }

onMounted(fetchOrders)
</script>

<template>
  <div class="card" style="padding: 0; overflow: hidden;">
    <div class="table-header">
      <h2>All Orders <span class="count">{{ total }}</span></h2>
      <select v-model="statusFilter" @change="page = 1; fetchOrders()" class="filter-select">
        <option value="">All Statuses</option>
        <option value="Pending">Pending</option>
        <option value="Received">Received</option>
        <option value="Shipped">Shipped</option>
        <option value="Delivered">Delivered</option>
        <option value="Cancelled">Cancelled</option>
        <option value="Returned">Returned</option>
      </select>
    </div>

    <div v-if="errorMsg" class="error-banner" style="margin: 24px;">{{ errorMsg }}</div>
    <div v-if="notice" class="notice-banner">{{ notice }}</div>
    <div v-if="loading" style="padding: 40px; text-align: center; color: var(--text-secondary);">Loading orders...</div>

    <table v-else-if="orders.length > 0" class="data-table">
      <thead>
        <tr>
          <th>Order ID</th>
          <th>Customer</th>
          <th>Date</th>
          <th>Status</th>
          <th>Items</th>
          <th style="text-align: right;">Total</th>
          <th v-if="auth.isAdmin" style="text-align: right;">Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="order in orders" :key="order.order_id" @click="router.push(`/app/orders/${order.order_id}`)" class="clickable-row">
          <td class="mono" style="color: var(--brand-purple);">{{ order.order_id }}</td>
          <td>{{ order.customer_id }}</td>
          <td style="color: var(--text-secondary);">{{ order.order_date }}</td>
          <td>
            <span class="status-pill" :class="order.order_status.toLowerCase()">{{ order.order_status }}</span>
          </td>
          <td>{{ order.item_count }}</td>
          <td class="mono" style="text-align: right;">&#8377;{{ order.total.toFixed(2) }}</td>
          <td v-if="auth.isAdmin" class="actions-cell" @click.stop>
            <button
              v-for="a in actionsFor(order.order_status)"
              :key="a.to"
              class="act"
              :class="{ danger: a.danger }"
              :disabled="busyId === order.order_id"
              @click.stop="changeStatus(order, a)"
            >{{ a.label }}</button>
            <span v-if="!actionsFor(order.order_status).length" class="closed">Closed</span>
          </td>
        </tr>
      </tbody>
    </table>

    <div v-else class="empty-state">No orders found matching your criteria.</div>

    <div class="pagination" v-if="pages > 1">
      <button @click="prevPage" :disabled="page === 1" class="btn-secondary">Previous</button>
      <span class="page-info">Page {{ page }} of {{ pages }}</span>
      <button @click="nextPage" :disabled="page === pages" class="btn-secondary">Next</button>
    </div>
  </div>
</template>

<style scoped>
.table-header { display: flex; justify-content: space-between; align-items: center; padding: 24px 32px; border-bottom: 1px solid var(--border-color); }
.table-header h2 { font-size: 18px; font-weight: 600; display: flex; align-items: center; gap: 12px; }
.count { background: var(--bg-app); padding: 4px 10px; border-radius: var(--radius-pill); font-size: 12px; color: var(--text-secondary); }
.filter-select { width: 160px; margin-bottom: 0; padding: 8px 16px; }
.clickable-row { cursor: pointer; transition: background 0.1s; }
.empty-state { text-align: center; padding: 60px; color: var(--text-secondary); font-size: 15px; }
.pagination { display: flex; justify-content: center; align-items: center; gap: 24px; padding: 24px; border-top: 1px solid var(--border-color); }
.page-info { font-size: 14px; font-weight: 500; }
.notice-banner { background: #D1FAE5; color: #065F46; padding: 12px; border-radius: 8px; margin: 16px 24px; font-size: 14px; }
.actions-cell { text-align: right; white-space: nowrap; }
.act { border: 1px solid #D5DAE6; background: #FFFFFF; color: #0B1020; padding: 6px 12px; border-radius: 99px; font-size: 12px; font-weight: 700; cursor: pointer; margin-left: 6px; }
.act:hover { background: #0B1020; color: #FFFFFF; }
.act.danger { color: #991B1B; border-color: #F3C6C6; }
.act.danger:hover { background: #991B1B; color: #FFFFFF; }
.act:disabled { opacity: 0.5; cursor: wait; }
.closed { font-size: 12px; color: var(--text-secondary); }
</style>
'@

Write-Host ''
Write-Host 'Done. Restart Flask (the Vite page hot-reloads). If anything looks wrong, restore the files from the _backup_ folder.'
