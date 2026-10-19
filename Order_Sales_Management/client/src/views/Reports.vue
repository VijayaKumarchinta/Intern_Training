<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import VueApexCharts from 'vue3-apexcharts'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import { useSummaryStore } from '@/stores/summary'
import { formatDate, money, number, percent } from '@/utils/format'
import Icon from '@/components/Icon.vue'

const router = useRouter()
const auth = useAuthStore()
const summaryStore = useSummaryStore()

const loading = ref(true)
const errorMsg = ref('')
const group = ref('month')
const downloading = ref('')

const summary = computed(() => summaryStore.data || {})
const totalOrders = computed(() => summary.value.total_orders || 0)
const firstName = computed(
  () => auth.user?.full_name?.split(' ')[0] || 'Admin',
)

const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 12) return 'Good morning'
  if (hour < 17) return 'Good afternoon'
  return 'Good evening'
})

const dayRows = ref([])
const dayLoading = ref(false)

const chartRows = computed(() =>
  group.value === 'day' ? dayRows.value : summary.value.monthly_breakdown || [],
)

const chartSeries = computed(() => [
  {
    name: 'Revenue',
    data: chartRows.value.map((row) => Number(row.revenue.toFixed(2))),
  },
])

const chartPeriod = (period) =>
  group.value === 'day' ? period.slice(5, 10) : period.slice(0, 7)

const loadDays = async () => {
  if (dayRows.value.length || dayLoading.value) return
  dayLoading.value = true
  try {
    const res = await api.get('/reports/date-wise?group=day')
    dayRows.value = (res.data || []).slice(-30)
  } catch (err) {
    errorMsg.value = 'Failed to load daily revenue.'
  } finally {
    dayLoading.value = false
  }
}

const setGroup = (next) => {
  group.value = next
  if (next === 'day') loadDays()
}

const chartOptions = computed(() => ({
  chart: {
    type: 'bar',
    toolbar: { show: false },
    animations: { enabled: false },
    fontFamily: 'Inter, sans-serif',
  },
  colors: ['#c7f53c'],
  plotOptions: { bar: { borderRadius: 4, columnWidth: '46%' } },
  xaxis: {
    categories: chartRows.value.map((row) => chartPeriod(row.period)),
    labels: { style: { colors: '#8b95a8', fontSize: '11px' } },
    axisBorder: { show: false },
    axisTicks: { show: false },
  },
  yaxis: {
    labels: {
      style: { colors: '#8b95a8', fontSize: '11px' },
      formatter: (value) => (value >= 1000 ? `₹${(value / 1000).toFixed(0)}k` : `₹${value}`),
    },
  },
  grid: { show: false },
  dataLabels: { enabled: false },
  tooltip: {
    theme: 'dark',
    y: { formatter: (value) => money(value) },
  },
}))

const donutColors = ['#2f5bff', '#c7f53c', '#ff7a45', '#2bb6a3', '#8b8cf7', '#f4c542', '#94a3b8']

const donutSeries = computed(() =>
  (summary.value.product_breakdown || []).slice(0, 7).map((row) => Number(row.revenue.toFixed(2))),
)

const donutOptions = computed(() => ({
  chart: { type: 'donut', fontFamily: 'Inter, sans-serif' },
  labels: (summary.value.product_breakdown || []).slice(0, 7).map((row) => row.product),
  colors: donutColors,
  dataLabels: { enabled: false },
  legend: { show: false },
  stroke: { width: 0 },
  plotOptions: {
    pie: {
      donut: {
        size: '62%',
        labels: {
          show: true,
          name: { show: false },
          value: {
            show: true,
            fontSize: '26px',
            fontWeight: 700,
            color: '#0b1220',
            formatter: () => `${summary.value.product_breakdown?.length || 0} products`,
          },
          total: {
            show: true,
            label: '100%',
            fontSize: '11px',
            color: '#6b7280',
            formatter: () => '100%',
          },
        },
      },
    },
  },
  tooltip: { y: { formatter: (value) => money(value) } },
}))

const statusRows = computed(() => {
  const rows = summary.value.status_breakdown || []
  const byStatus = Object.fromEntries(rows.map((row) => [row.status, row.count]))
  return ['Pending', 'Received', 'Shipped', 'Delivered', 'Cancelled', 'Returned'].map(
    (status) => ({
      status,
      count: byStatus[status] || 0,
      share: percent(byStatus[status] || 0, totalOrders.value),
    }),
  )
})

const duplicateValue = computed(() =>
  (summary.value.duplicate_groups || []).reduce(
    (total, group) => total + Number(group.unit_price || 0),
    0,
  ),
)

const latestOrders = computed(() => summary.value.latest_orders || [])

const load = async () => {
  loading.value = true
  errorMsg.value = ''
  try {
    await summaryStore.fetch(true)
    if (summaryStore.error) errorMsg.value = summaryStore.error
  } finally {
    loading.value = false
  }
}

const downloadReport = async (type, grouping = 'month') => {
  if (downloading.value) return
  try {
    downloading.value = type
    let url = `/reports/${type}?format=csv`
    if (type === 'date-wise') url += `&group=${grouping}`
    const res = await api.get(url, { responseType: 'blob' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(res.data)
    link.download = `${type}_report_${new Date().toISOString().slice(0, 10)}.csv`
    link.click()
    URL.revokeObjectURL(link.href)
  } catch (err) {
    window.alert('Failed to download report.')
  } finally {
    downloading.value = ''
  }
}

onMounted(load)
</script>

<template>
  <div class="dashboard">
    <header class="dash-head">
      <div>
        <p class="eyebrow">OrderSync · Admin</p>
        <h1>{{ greeting }}, {{ firstName }}</h1>
      </div>
      <div class="dash-actions">
        <div class="segmented" role="group" aria-label="Chart grouping">
          <button :class="{ active: group === 'month' }" @click="setGroup('month')">Month</button>
          <button :class="{ active: group === 'day' }" @click="setGroup('day')">Day</button>
        </div>
        <button class="btn btn-ghost" :disabled="!!downloading" @click="downloadReport('product-wise')">
          Product CSV
        </button>
        <button class="btn btn-ghost" :disabled="!!downloading" @click="downloadReport('date-wise', group)">
          Date CSV
        </button>
        <button class="btn btn-primary" @click="router.push('/app/new-order')">
          <Icon name="plus" :size="15" /> New order
        </button>
        <div class="avatar">{{ firstName.charAt(0).toUpperCase() }}</div>
      </div>
    </header>

    <div v-if="loading" class="spinner-state">Loading dashboard…</div>
    <div v-else-if="errorMsg" class="error-banner">{{ errorMsg }}</div>

    <template v-else>
      <section class="bento">
        <div class="card revenue-card">
          <p class="card-label">Revenue · Shipped + Delivered</p>
          <p class="revenue-value mono">{{ money(summary.revenue || 0) }}</p>
          <span class="trend">
            {{ group === 'day' ? 'Last 30 days' : 'All time' }} ·
            {{ number(summary.units_sold) }} units sold
          </span>
          <div class="chart-wrap">
            <VueApexCharts
              v-if="chartRows.length"
              type="bar"
              height="150"
              :options="chartOptions"
              :series="chartSeries"
            />
            <p v-else-if="dayLoading" class="chart-empty">Loading daily revenue…</p>
            <p v-else class="chart-empty">No sales recorded yet.</p>
          </div>
        </div>

        <div class="stat blue-card">
          <p class="stat-label">Sales orders</p>
          <p class="stat-big">{{ percent(summary.sales_orders, totalOrders).toFixed(1) }}%</p>
          <p class="stat-foot">
            {{ number(summary.sales_orders) }} of {{ number(totalOrders) }} orders
          </p>
        </div>

        <div class="stat orange-card">
          <p class="stat-label dark">Awaiting action</p>
          <p class="stat-big dark">{{ percent(summary.awaiting_action, totalOrders).toFixed(1) }}%</p>
          <p class="stat-foot dark">
            {{ number(summary.awaiting_action) }} orders · <router-link to="/app/orders?status=Pending">open queue →</router-link>
          </p>
        </div>

        <div class="card units-card">
          <p class="card-label">Units sold</p>
          <p class="units-value mono">{{ number(summary.units_sold) }}</p>
          <p class="units-foot">on {{ number(summary.sales_orders) }} sales orders</p>
        </div>

        <router-link to="/app/duplicates" class="card dup-card">
          <p class="dup-title">
            <Icon name="alert" :size="16" /> {{ summary.duplicate_groups?.length || 0 }} duplicate
            {{ (summary.duplicate_groups?.length || 0) === 1 ? 'group' : 'groups' }}
          </p>
          <p class="dup-meta">
            {{ (summary.duplicate_groups || []).reduce((n, d) => n + (d.order_ids?.length || 0), 0) }}
            orders · {{ money(duplicateValue) }} one copy of each
          </p>
          <div class="dup-chips">
            <span
              v-for="group in (summary.duplicate_groups || []).slice(0, 2)"
              :key="group.order_ids.join('-')"
              class="code-chip"
            >
              {{ group.order_ids[0] }} · {{ group.order_ids[1] }}
            </span>
            <span v-if="!summary.duplicate_groups?.length" class="code-chip">No duplicates</span>
          </div>
        </router-link>

        <div class="card product-card">
          <h2>Revenue by product</h2>
          <div class="donut-layout">
            <VueApexCharts
              v-if="donutSeries.length"
              type="donut"
              height="210"
              width="210"
              :options="donutOptions"
              :series="donutSeries"
            />
            <p v-else class="chart-empty">No product revenue yet.</p>
            <ul class="donut-legend">
              <li v-for="(row, index) in (summary.product_breakdown || []).slice(0, 7)" :key="row.product">
                <span class="legend-name">
                  <i :style="{ background: donutColors[index % donutColors.length] }"></i>
                  {{ row.product }}
                </span>
                <span class="legend-share mono">
                  {{ percent(row.revenue, summary.revenue).toFixed(1) }}%
                </span>
              </li>
            </ul>
          </div>
        </div>

        <div class="card status-card">
          <div class="status-head">
            <h2>Order status</h2>
            <span class="muted">{{ number(totalOrders) }} orders</span>
          </div>
          <ul class="status-list">
            <li v-for="row in statusRows" :key="row.status">
              <span class="status-name">
                <i :class="`dot-${row.status.toLowerCase()}`"></i>{{ row.status }}
              </span>
              <span class="status-bar">
                <span
                  :class="`bar-${row.status.toLowerCase()}`"
                  :style="{ width: `${Math.max(row.share, 1.5)}%` }"
                ></span>
              </span>
              <span class="status-share mono">{{ row.share.toFixed(1) }}%</span>
            </li>
          </ul>
        </div>

        <div class="card latest-card">
          <div class="latest-head">
            <h2>Latest orders</h2>
            <router-link to="/app/orders" class="view-all">
              View all {{ number(totalOrders) }} →
            </router-link>
          </div>
          <div class="scroll-x">
            <table class="table">
              <thead>
                <tr>
                  <th>Order</th>
                  <th>Customer</th>
                  <th>Date</th>
                  <th>Status</th>
                  <th class="right">Total</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="order in latestOrders"
                  :key="order.order_id"
                  class="clickable"
                  @click="router.push(`/app/orders/${order.order_id}`)"
                >
                  <td><span class="order-id">{{ order.order_id }}</span></td>
                  <td class="muted">{{ order.customer_id }}</td>
                  <td class="muted">{{ formatDate(order.order_date) }}</td>
                  <td>
                    <span class="status-pill" :class="order.order_status.toLowerCase()">
                      {{ order.order_status }}
                    </span>
                  </td>
                  <td class="right mono">{{ money(order.total) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p v-if="!latestOrders.length" class="empty-state">No orders yet.</p>
        </div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.dashboard {
  max-width: 1400px;
}
.dash-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
  flex-wrap: wrap;
  margin-bottom: 22px;
}
.dash-head h1 {
  font-size: clamp(28px, 2.6vw, 42px);
  font-weight: 700;
  letter-spacing: -0.045em;
  margin-top: 6px;
}
.dash-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.segmented {
  display: inline-flex;
  background: #fff;
  border-radius: 999px;
  padding: 4px;
  gap: 2px;
}
.segmented button {
  border-radius: 999px;
  padding: 8px 18px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
}
.segmented button.active {
  background: var(--ink);
  color: #fff;
}
.bento {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}
.card {
  padding: 24px;
  border-radius: 26px;
}
h2 {
  font-size: 19px;
  font-weight: 700;
  letter-spacing: -0.03em;
}
.card-label {
  font-size: 13.5px;
  font-weight: 500;
  color: #9aa4b7;
}
.revenue-card {
  grid-column: span 2;
  background: var(--ink);
  color: #fff;
  display: flex;
  flex-direction: column;
  min-height: 262px;
}
.revenue-card .card-label {
  color: #9aa4b7;
}
.revenue-value {
  font-family: 'Inter Tight', sans-serif;
  font-size: clamp(32px, 3.2vw, 44px);
  font-weight: 700;
  letter-spacing: -0.045em;
  color: var(--lime);
  margin: 6px 0 12px;
  word-break: break-word;
}
.trend {
  align-self: flex-start;
  background: rgba(199, 245, 60, 0.12);
  color: var(--lime);
  border-radius: 999px;
  padding: 5px 12px;
  font-size: 11.5px;
  font-weight: 600;
}
.chart-wrap {
  margin-top: auto;
  padding-top: 14px;
  margin-bottom: -10px;
}
.chart-empty {
  color: #808b9f;
  font-size: 13px;
  padding: 26px 0;
}
.stat {
  border-radius: 26px;
  padding: 26px 24px;
  display: flex;
  flex-direction: column;
  min-height: 158px;
}
.blue-card {
  background: var(--blue);
  color: #fff;
}
.orange-card {
  background: var(--orange);
  color: var(--ink);
}
.stat-label {
  font-size: 14px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.88);
}
.stat-label.dark {
  color: var(--ink);
}
.stat-big {
  font-family: 'Inter Tight', sans-serif;
  font-size: clamp(34px, 3.4vw, 52px);
  font-weight: 800;
  letter-spacing: -0.05em;
  line-height: 1.05;
  margin: 10px 0 auto;
}
.stat-big.dark {
  color: var(--ink);
}
.stat-foot {
  font-size: 12.5px;
  color: rgba(255, 255, 255, 0.82);
}
.stat-foot a {
  color: #fff;
  font-weight: 600;
  text-decoration: none;
}
.stat-foot.dark {
  color: #4a2a17;
}
.stat-foot.dark a {
  color: var(--ink);
  font-weight: 700;
  text-decoration: none;
}
.units-card {
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.units-value {
  font-family: 'Inter Tight', sans-serif;
  font-size: 44px;
  font-weight: 700;
  letter-spacing: -0.045em;
  margin: 6px 0 4px;
}
.units-foot {
  font-size: 12.5px;
  color: var(--text-secondary);
}
.dup-card {
  background: var(--cream);
  text-decoration: none;
  color: var(--ink);
  display: flex;
  flex-direction: column;
  gap: 8px;
  transition: transform 0.18s ease;
}
.dup-card:hover {
  transform: translateY(-2px);
}
.dup-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 700;
}
.dup-meta {
  font-size: 12.5px;
  color: #6f5a25;
}
.dup-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: auto;
}
.code-chip {
  background: #fff;
  border-radius: 999px;
  padding: 5px 11px;
  font-size: 11px;
  font-weight: 700;
}
.product-card {
  grid-column: span 2;
}
.donut-layout {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  align-items: center;
  gap: 18px;
  margin-top: 12px;
}
.donut-legend {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 9px;
}
.donut-legend li {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 12.5px;
  color: #4b5563;
}
.legend-name {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.legend-name i {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex: none;
}
.legend-share {
  font-weight: 600;
  color: var(--text-primary);
}
.status-card {
  grid-column: span 2;
}
.status-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 18px;
}
.status-head .muted {
  font-size: 12.5px;
}
.status-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 13px;
}
.status-list li {
  display: grid;
  grid-template-columns: 96px minmax(0, 1fr) 52px;
  align-items: center;
  gap: 14px;
  font-size: 13px;
}
.status-name {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  font-weight: 500;
}
.status-name i {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  flex: none;
}
.status-bar {
  height: 8px;
  background: #eef0f5;
  border-radius: 999px;
  overflow: hidden;
}
.status-bar span {
  display: block;
  height: 100%;
  border-radius: 999px;
}
.status-share {
  text-align: right;
  font-weight: 600;
  font-size: 12.5px;
}
.dot-pending,
.bar-pending {
  background: #f4c542;
}
.dot-received,
.bar-received {
  background: #8b8cf7;
}
.dot-shipped,
.bar-shipped {
  background: var(--blue);
}
.dot-delivered,
.bar-delivered {
  background: var(--teal);
}
.dot-cancelled,
.bar-cancelled {
  background: #ef5350;
}
.dot-returned,
.bar-returned {
  background: #ec4899;
}
.latest-card {
  grid-column: span 4;
}
.latest-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}
.view-all {
  color: var(--blue);
  font-size: 13px;
  font-weight: 600;
  text-decoration: none;
}
.view-all:hover {
  text-decoration: underline;
}
.order-id {
  color: var(--blue);
  font-weight: 600;
}
.clickable {
  cursor: pointer;
}
.right {
  text-align: right;
}
@media (max-width: 1180px) {
  .bento {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .revenue-card,
  .product-card,
  .status-card,
  .latest-card {
    grid-column: span 2;
  }
}
@media (max-width: 640px) {
  .bento {
    grid-template-columns: 1fr;
  }
  .revenue-card,
  .product-card,
  .status-card,
  .latest-card {
    grid-column: span 1;
  }
  .donut-layout {
    grid-template-columns: 1fr;
    justify-items: center;
  }
  .donut-legend {
    width: 100%;
  }
  .status-list li {
    grid-template-columns: 84px minmax(0, 1fr) 48px;
    gap: 10px;
  }
  .dash-actions {
    width: 100%;
  }
}
</style>
