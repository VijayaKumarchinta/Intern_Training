<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import VueApexCharts from 'vue3-apexcharts'
import { useAuthStore } from '@/stores/auth'
import { useSummaryStore } from '@/stores/summary'
import api from '@/services/api'
import { money, number, percent } from '@/utils/format'

const router = useRouter()
const auth = useAuthStore()
const summaryStore = useSummaryStore()

const loading = ref(true)
const errorMsg = ref('')

const summary = computed(() => summaryStore.data || {})
const totalOrders = computed(() => summary.value.total_orders || 0)

const firstName = computed(
  () => auth.user?.full_name?.split(' ')[0] || 'Admin'
)

const greeting = computed(() => {
  const hour = new Date().getHours()

  return hour < 12
    ? 'Good morning'
    : hour < 17
      ? 'Good afternoon'
      : 'Good evening'
})

const duplicates = computed(() => summary.value.duplicate_groups || [])

const chartOptions = ref({
  chart: {
    type: 'area',
    height: 300,
    toolbar: { show: false }
  },
  colors: ['#2f5bff'],
  stroke: {
    curve: 'smooth',
    width: 3
  },
  fill: {
    type: 'gradient',
    gradient: {
      opacityFrom: 0.3,
      opacityTo: 0.05
    }
  },
  xaxis: {
    categories: [],
    axisBorder: { show: false },
    axisTicks: { show: false }
  },
  grid: {
    borderColor: '#eef0f5',
    strokeDashArray: 4
  },
  dataLabels: { enabled: false },
  tooltip: {
    y: {
      formatter: (value) => money(value)
    }
  }
})

const chartSeries = ref([
  { name: 'Revenue', data: [] }
])

const productLoading = ref(true)
const productError = ref('')
const productRows = ref([])

const productChartOptions = ref({
  chart: {
    type: 'bar',
    height: 320,
    toolbar: { show: false }
  },
  colors: ['#2f5bff'],
  plotOptions: {
    bar: {
      horizontal: true,
      borderRadius: 5,
      barHeight: '65%'
    }
  },
  dataLabels: { enabled: false },
  xaxis: {
    categories: [],
    labels: {
      formatter: (value) => number(value)
    }
  },
  grid: {
    borderColor: '#eef0f5',
    strokeDashArray: 4
  },
  tooltip: {
    y: {
      formatter: (value) => money(value)
    }
  }
})

const productChartSeries = ref([
  { name: 'Revenue', data: [] }
])

const dateLoading = ref(true)
const dateError = ref('')
const dateRows = ref([])

const dateChartOptions = ref({
  chart: {
    type: 'area',
    height: 320,
    toolbar: { show: false }
  },
  colors: ['#10a37f'],
  stroke: {
    curve: 'smooth',
    width: 3
  },
  fill: {
    type: 'gradient',
    gradient: {
      opacityFrom: 0.3,
      opacityTo: 0.05
    }
  },
  dataLabels: { enabled: false },
  xaxis: {
    categories: [],
    axisBorder: { show: false },
    axisTicks: { show: false }
  },
  grid: {
    borderColor: '#eef0f5',
    strokeDashArray: 4
  },
  tooltip: {
    y: {
      formatter: (value) => money(value)
    }
  }
})

const dateChartSeries = ref([
  { name: 'Revenue', data: [] }
])

function getReportRows(data, possibleKeys) {
  if (Array.isArray(data)) {
    return data
  }

  for (const key of possibleKeys) {
    if (Array.isArray(data?.[key])) {
      return data[key]
    }
  }

  return []
}

async function loadProductReport() {
  productLoading.value = true
  productError.value = ''

  try {
    const response = await api.get('/reports/product-wise')

    productRows.value = getReportRows(response.data, [
      'products',
      'product_wise',
      'results',
      'data'
    ])

    productChartOptions.value = {
      ...productChartOptions.value,
      xaxis: {
        ...productChartOptions.value.xaxis,
        categories: productRows.value.map(
          (item) =>
            item.product_name ??
            item.product ??
            item.product_name_display ??
            'Unknown product'
        )
      }
    }

    productChartSeries.value = [
      {
        name: 'Revenue',
        data: productRows.value.map(
          (item) =>
            Number(
              item.revenue ??
              item.total_revenue ??
              item.total_sales ??
              0
            )
        )
      }
    ]
  } catch (error) {
    console.error('Failed to load product-wise report:', error)
    productError.value = 'Failed to load product-wise sales.'
  } finally {
    productLoading.value = false
  }
}

async function loadDateReport() {
  dateLoading.value = true
  dateError.value = ''

  try {
    const response = await api.get('/reports/date-wise')

    dateRows.value = getReportRows(response.data, [
      'dates',
      'date_wise',
      'results',
      'data'
    ])

    dateChartOptions.value = {
      ...dateChartOptions.value,
      xaxis: {
        ...dateChartOptions.value.xaxis,
        categories: dateRows.value.map(
          (item) =>
            item.date ??
            item.period ??
            item.order_date ??
            ''
        )
      }
    }

    dateChartSeries.value = [
      {
        name: 'Revenue',
        data: dateRows.value.map(
          (item) =>
            Number(
              item.revenue ??
              item.total_revenue ??
              item.total_sales ??
              0
            )
        )
      }
    ]
  } catch (error) {
    console.error('Failed to load date-wise report:', error)
    dateError.value = 'Failed to load date-wise sales.'
  } finally {
    dateLoading.value = false
  }
}

onMounted(async () => {
  try {
    await summaryStore.fetch(true)

    const monthly = (summary.value.monthly_breakdown || []).slice(-12)

    chartOptions.value = {
      ...chartOptions.value,
      xaxis: {
        ...chartOptions.value.xaxis,
        categories: monthly.map((item) =>
          item.period ? item.period.slice(0, 7) : ''
        )
      }
    }

    chartSeries.value = [
      {
        name: 'Revenue',
        data: monthly.map((item) => Number(item.revenue || 0))
      }
    ]
  } catch (error) {
    console.error('Failed to load dashboard:', error)
    errorMsg.value = 'Failed to load dashboard.'
  } finally {
    loading.value = false
  }

  await Promise.allSettled([
    loadProductReport(),
    loadDateReport()
  ])
})
</script>

<template>
  <div class="dashboard">
    <header class="page-header">
      <div>
        <h1>{{ greeting }}, {{ firstName }}</h1>
        <p class="subtitle">
          Here's what's happening with your orders and sales today.
        </p>
      </div>
    </header>

    <div v-if="loading" class="loading">
      Loading dashboard...
    </div>

    <div v-else-if="errorMsg" class="error-message">
      {{ errorMsg }}
    </div>

    <div v-else class="grid">
      <div class="kpi-card dark">
        <span class="kpi-label">Revenue</span>
        <span class="kpi-value">{{ money(summary.revenue) }}</span>
      </div>

      <div class="kpi-card blue">
        <span class="kpi-label">Sales Orders</span>
        <span class="kpi-value">
          {{ percent(summary.sales_orders, totalOrders).toFixed(1) }}%
        </span>
        <span class="kpi-sub">
          {{ number(summary.sales_orders) }} of {{ number(totalOrders) }}
        </span>
      </div>

      <div class="kpi-card white">
        <span class="kpi-label">Units Sold</span>
        <span class="kpi-value">{{ number(summary.units_sold) }}</span>
      </div>

      <div class="kpi-card orange">
        <span class="kpi-label">Awaiting Action</span>
        <span class="kpi-value">
          {{ percent(summary.awaiting_action, totalOrders).toFixed(1) }}%
        </span>
        <span class="kpi-sub">
          {{ number(summary.awaiting_action) }} open queue
        </span>
      </div>

      <div class="card span-3">
        <h2>Revenue Over Time (Last 12 Months)</h2>

        <VueApexCharts
          type="area"
          height="300"
          :options="chartOptions"
          :series="chartSeries"
        />
      </div>

      <div class="card span-2">
        <h2>Product-wise Sales</h2>
        <p class="muted">Revenue generated by each product.</p>

        <div v-if="productLoading" class="loading">
          Loading product report...
        </div>

        <div v-else-if="productError" class="error-message">
          {{ productError }}
          <button
            type="button"
            class="btn btn-ghost"
            @click="loadProductReport"
          >
            Retry
          </button>
        </div>

        <p v-else-if="!productRows.length" class="muted">
          No product sales data available.
        </p>

        <VueApexCharts
          v-else
          type="bar"
          height="320"
          :options="productChartOptions"
          :series="productChartSeries"
        />
      </div>

      <div class="card span-3">
        <h2>Date-wise Sales</h2>
        <p class="muted">Revenue generated over time.</p>

        <div v-if="dateLoading" class="loading">
          Loading date-wise report...
        </div>

        <div v-else-if="dateError" class="error-message">
          {{ dateError }}
          <button
            type="button"
            class="btn btn-ghost"
            @click="loadDateReport"
          >
            Retry
          </button>
        </div>

        <p v-else-if="!dateRows.length" class="muted">
          No date-wise sales data available.
        </p>

        <VueApexCharts
          v-else
          type="area"
          height="320"
          :options="dateChartOptions"
          :series="dateChartSeries"
        />
      </div>

      <div class="card span-2">
        <h2>Latest Orders</h2>

        <table class="data-table">
          <thead>
            <tr>
              <th>Order ID</th>
              <th>Customer</th>
              <th>Status</th>
              <th class="right">Total</th>
            </tr>
          </thead>

          <tbody>
            <tr
              v-for="order in (summary.latest_orders || [])"
              :key="order.order_id"
            >
              <td class="mono">{{ order.order_id }}</td>
              <td>{{ order.customer_id }}</td>
              <td>
                <span
                  class="status-pill"
                  :class="String(order.order_status || '').toLowerCase()"
                >
                  {{ order.order_status }}
                </span>
              </td>
              <td class="right mono">{{ money(order.total) }}</td>
            </tr>

            <tr v-if="!(summary.latest_orders || []).length">
              <td colspan="4" class="muted">
                No recent orders available.
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="duplicates.length" class="card duplicate-card">
        <h2>Duplicate Alert</h2>

        <p class="dup-text">
          {{ duplicates.length }} group(s) of duplicate orders found.
        </p>

        <div
          v-for="(group, index) in duplicates.slice(0, 2)"
          :key="index"
          class="dup-group"
        >
          <p class="mono">
            {{ (group.order_ids || []).join(' • ') }}
          </p>
          <p class="muted">
            {{ group.customer_id }} · Qty {{ group.quantity }}
          </p>
        </div>

        <router-link
          to="/app/duplicates"
          class="btn btn-ghost mt-auto"
        >
          Review Duplicates
        </router-link>
      </div>

      <div v-else class="card span-1">
        <h2>Duplicates</h2>
        <p class="muted">
          No duplicates found. All orders are unique.
        </p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard {
  max-width: 1600px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
}

h1 {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 8px;
}

h2 {
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 8px;
}

.subtitle {
  color: var(--text-secondary);
  font-size: 14px;
}

.grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 20px;
}

.card {
  min-width: 0;
  background: white;
  border-radius: 24px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
}

.span-1 {
  grid-column: span 1;
}

.span-2 {
  grid-column: span 2;
}

.span-3 {
  grid-column: span 3;
}

.kpi-card {
  border-radius: 24px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 0;
}

.kpi-card.dark {
  background: var(--ink);
  color: white;
}

.kpi-card.dark .kpi-value {
  color: var(--lime);
}

.kpi-card.blue {
  background: var(--blue);
  color: white;
}

.kpi-card.white {
  background: white;
}

.kpi-card.orange {
  background: var(--orange);
  color: var(--ink);
}

.kpi-label {
  font-size: 14px;
  font-weight: 600;
  opacity: 0.9;
}

.kpi-value {
  font-size: 32px;
  font-weight: 800;
  overflow-wrap: anywhere;
}

.kpi-sub {
  font-size: 12px;
  opacity: 0.7;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 16px;
  font-size: 14px;
}

.data-table th,
.data-table td {
  padding: 12px 0;
  border-bottom: 1px solid var(--line);
  text-align: left;
}

.data-table th {
  font-weight: 600;
}

.data-table .right {
  text-align: right;
}

.data-table th.right,
.data-table td.right {
  text-align: right;
}

.mono {
  font-family: monospace;
}

.muted {
  color: var(--text-secondary);
  font-size: 13px;
}

.duplicate-card {
  background: var(--cream);
  display: flex;
  flex-direction: column;
}

.dup-text {
  font-size: 14px;
  margin-bottom: 16px;
}

.dup-group {
  background: white;
  padding: 12px;
  border-radius: 12px;
  margin-bottom: 12px;
}

.dup-group p {
  margin: 0;
}

.mt-auto {
  margin-top: auto;
}

.loading {
  padding: 24px 0;
  color: var(--text-secondary);
  font-size: 14px;
}

.error-message {
  color: #dc2626;
  font-size: 14px;
  margin-top: 12px;
}

.error-message .btn {
  margin-left: 8px;
}

@media (max-width: 900px) {
  .grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .span-3 {
    grid-column: span 2;
  }
}

@media (max-width: 600px) {
  .grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .span-1,
  .span-2,
  .span-3 {
    grid-column: span 1;
  }

  .card,
  .kpi-card {
    padding: 18px;
    border-radius: 18px;
  }

  h1 {
    font-size: 24px;
  }

  .kpi-value {
    font-size: 28px;
  }

  .data-table {
    font-size: 12px;
  }
}
</style>