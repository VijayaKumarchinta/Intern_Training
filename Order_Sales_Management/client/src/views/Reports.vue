<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'
import VueApexCharts from 'vue3-apexcharts'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const summary = ref({})
const loading = ref(true)
const errorMsg = ref('')

const chartOptions = ref({
  chart: { type: 'bar', toolbar: { show: false } },
  colors: ['#5A4FCF'],
  plotOptions: { bar: { borderRadius: 6, columnWidth: '40%' } },
  xaxis: { categories: [] },
  dataLabels: { enabled: false },
  grid: { show: false }
})
const chartSeries = ref([{ name: 'Revenue', data: [] }])

const donutOptions = ref({
  chart: { type: 'donut' },
  labels: [],
  colors: ['#5A4FCF', '#10B981', '#F59E0B', '#EC4899', '#6B7280', '#9CA3AF'],
  dataLabels: { enabled: false },
  legend: { show: false },
  stroke: { show: false }
})
const donutSeries = ref([])

onMounted(async () => {
  try {
    const res = await api.get('/reports/summary')
    summary.value = res.data

    chartOptions.value.xaxis.categories = res.data.monthly_breakdown.map(d => d.period.slice(0, 7))
    chartSeries.value[0].data = res.data.monthly_breakdown.map(d => d.revenue)

    const topProducts = res.data.product_breakdown.slice(0, 5)
    donutOptions.value.labels = topProducts.map(p => p.product)
    donutSeries.value = topProducts.map(p => p.revenue)
  } catch (err) {
    errorMsg.value = 'Failed to load dashboard data.'
  } finally {
    loading.value = false
  }
})

const downloadReport = (type, group = 'month') => {
  let url = `/api/reports/${type}?format=csv`
  if (type === 'date-wise') url += `&group=${group}`

  fetch(url, { headers: { Authorization: `Bearer ${auth.token}` } })
    .then(res => {
      if (!res.ok) throw new Error('Download failed')
      return res.blob()
    })
    .then(blob => {
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = `${type}_report_${new Date().toISOString().slice(0, 10)}.csv`
      link.click()
      URL.revokeObjectURL(link.href)
    })
    .catch(err => {
      console.error(err)
      alert('Failed to download report')
    })
}
</script>

<template>
  <div v-if="loading" class="loading-state">Loading dashboard...</div>
  <div v-else-if="errorMsg" class="card error-state">{{ errorMsg }}</div>
  
  <div v-else>
    <div class="report-actions">
      <h2>Sales Reports</h2>
      <div class="download-buttons">
        <button @click="downloadReport('product-wise')" class="btn-secondary">📥 Product-wise CSV</button>
        <button @click="downloadReport('date-wise', 'month')" class="btn-secondary">📥 Date-wise CSV</button>
      </div>
    </div>

    <div class="dashboard-grid">
      <div class="kpi-card kpi-purple">
        <span class="kpi-title">Revenue</span>
        <h2 class="kpi-value">₹{{ summary.revenue.toLocaleString(undefined, { minimumFractionDigits: 2 }) }}</h2>
      </div>
      <div class="kpi-card kpi-green">
        <span class="kpi-title">Sales Orders</span>
        <h2 class="kpi-value">{{ summary.sales_orders.toLocaleString() }}</h2>
      </div>
      <div class="kpi-card kpi-yellow">
        <span class="kpi-title">Units Sold</span>
        <h2 class="kpi-value">{{ summary.units_sold.toLocaleString() }}</h2>
      </div>
      <div class="kpi-card kpi-pink">
        <span class="kpi-title">Awaiting Action</span>
        <h2 class="kpi-value">{{ summary.awaiting_action.toLocaleString() }}</h2>
      </div>

      <div class="card chart-main">
        <h3>Revenue by Month</h3>
        <VueApexCharts type="bar" height="280" :options="chartOptions" :series="chartSeries" />
      </div>

      <div class="card chart-side">
        <h3>Revenue by Product</h3>
        <VueApexCharts type="donut" height="220" :options="donutOptions" :series="donutSeries" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.report-actions { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.download-buttons { display: flex; gap: 12px; }
.dashboard-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 24px; }
.kpi-card { padding: 24px; border-radius: var(--radius-card); display: flex; flex-direction: column; gap: 8px; }
.kpi-title { font-size: 14px; font-weight: 500; }
.kpi-value { font-size: 32px; font-weight: 700; letter-spacing: -1px; }
.kpi-purple { background: #E0E7FF; color: #3730A3; }
.kpi-green { background: #D1FAE5; color: #065F46; }
.kpi-yellow { background: #FEF3C7; color: #92400E; }
.kpi-pink { background: #FCE7F3; color: #9D174D; }
.chart-main { grid-column: span 2; }
.chart-side { grid-column: span 2; }
.loading-state, .error-state { padding: 40px; text-align: center; color: var(--text-secondary); }
</style>
