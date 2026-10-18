<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'
import VueApexCharts from 'vue3-apexcharts'

const productData = ref([])
const totalRevenue = ref(0)
const loading = ref(true)
const errorMsg = ref('')

const chartOptions = ref({
  chart: { type: 'area', toolbar: { show: false } },
  colors: ['#4A90D9'],
  stroke: { curve: 'smooth', width: 2 },
  fill: { type: 'gradient', gradient: { opacityFrom: 0.4, opacityTo: 0.05 } },
  xaxis: { categories: [] },
  dataLabels: { enabled: false }
})
const chartSeries = ref([{ name: 'Revenue', data: [] }])

onMounted(async () => {
  try {
    const [prodRes, dateRes] = await Promise.all([
      api.get('/reports/product-wise'),
      api.get('/reports/date-wise?group=month')
    ])
    productData.value = prodRes.data
    totalRevenue.value = prodRes.data.reduce((sum, item) => sum + item.revenue, 0)
    chartOptions.value.xaxis.categories = dateRes.data.map(d => d.period)
    chartSeries.value[0].data = dateRes.data.map(d => d.revenue)
  } catch (err) {
    errorMsg.value = 'Failed to load reports.'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div v-if="errorMsg" class="error-banner">{{ errorMsg }}</div>
  <div v-else-if="loading">Loading Reports...</div>
  <div v-else class="reports-grid">
    <div class="card kpi-card">
      <h3>Total Revenue</h3>
      <p class="kpi-value">${{ totalRevenue.toLocaleString(undefined, { minimumFractionDigits: 2 }) }}</p>
      <span class="kpi-sub">From Shipped & Delivered</span>
    </div>

    <div class="card chart-card">
      <h3>Revenue Over Time</h3>
      <div v-if="chartSeries[0].data.length === 0" class="empty-state">No revenue data yet. Ship some orders!</div>
      <VueApexCharts v-else type="area" height="300" :options="chartOptions" :series="chartSeries" />
    </div>

    <div class="card" style="grid-column: 1 / -1;">
      <h3>Product Breakdown</h3>
      <div v-if="productData.length === 0" class="empty-state">No sales data yet.</div>
      <table v-else class="data-table" style="margin-top: 16px;">
        <thead>
          <tr><th>Product</th><th>Units</th><th>Revenue</th></tr>
        </thead>
        <tbody>
          <tr v-for="prod in productData" :key="prod.product">
            <td>{{ prod.product }}</td>
            <td>{{ prod.units }}</td>
            <td class="mono">${{ prod.revenue.toFixed(2) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.reports-grid { display: grid; grid-template-columns: 1fr 2fr; gap: 24px; }
.kpi-value { font-size: 40px; font-weight: 700; margin: 12px 0; letter-spacing: -1px; }
.kpi-sub { color: var(--text-secondary); font-size: 13px; }
.error-banner { background: #FEE2E2; color: #991B1B; padding: 12px; border-radius: 8px; margin-bottom: 16px; font-size: 14px; }
.empty-state { text-align: center; padding: 40px; color: var(--text-secondary); font-size: 14px; }
</style>