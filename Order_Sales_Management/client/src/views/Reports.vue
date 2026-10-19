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

const summary = computed(() => summaryStore.data || {})
const totalOrders = computed(() => summary.value.total_orders || 0)
const firstName = computed(() => auth.user?.full_name?.split(' ')[0] || 'Admin')
const greeting = computed(() => {
  const hour = new Date().getHours()
  return hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening'
})

// Line Chart (Last 12 Months)
const chartOptions = ref({
  chart: { type: 'area', height: 300, toolbar: { show: false } },
  colors: ['#2f5bff'],
  stroke: { curve: 'smooth', width: 3 },
  fill: { type: 'gradient', gradient: { opacityFrom: 0.3, opacityTo: 0.05 } },
  xaxis: { categories: [], axisBorder: { show: false }, axisTicks: { show: false } },
  grid: { borderColor: '#eef0f5', strokeDashArray: 4 },
  dataLabels: { enabled: false }
})
const chartSeries = ref([{ name: 'Revenue', data: [] }])

const duplicates = computed(() => summary.value.duplicate_groups || [])

onMounted(async () => {
  try {
    await summaryStore.fetch(true)
    // Limit to last 12 months for Dashboard
    const monthly = (summary.value.monthly_breakdown || []).slice(-12)
    chartOptions.value.xaxis.categories = monthly.map((m) => m.period.slice(0, 7))
    chartSeries.value[0].data = monthly.map((m) => m.revenue)
  } catch (e) {
    errorMsg.value = 'Failed to load dashboard.'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="dashboard">
    <header class="page-header">
      <div>
        <h1>{{ greeting }}, {{ firstName }}</h1>
        <p class="subtitle">Here's what's happening with your orders and sales today.</p>
      </div>
    </header>

    <div v-if="loading" class="loading">Loading dashboard...</div>
    
    <div v-else class="grid">
      <!-- 4 KPI Cards -->
      <div class="kpi-card dark">
        <span class="kpi-label">Revenue</span>
        <span class="kpi-value">{{ money(summary.revenue) }}</span>
      </div>
      <div class="kpi-card blue">
        <span class="kpi-label">Sales Orders</span>
        <span class="kpi-value">{{ percent(summary.sales_orders, totalOrders).toFixed(1) }}%</span>
        <span class="kpi-sub">{{ number(summary.sales_orders) }} of {{ number(totalOrders) }}</span>
      </div>
      <div class="kpi-card white">
        <span class="kpi-label">Units Sold</span>
        <span class="kpi-value">{{ number(summary.units_sold) }}</span>
      </div>
      <div class="kpi-card orange">
        <span class="kpi-label">Awaiting Action</span>
        <span class="kpi-value">{{ percent(summary.awaiting_action, totalOrders).toFixed(1) }}%</span>
        <span class="kpi-sub">{{ number(summary.awaiting_action) }} open queue</span>
      </div>

      <!-- Line Chart (Full Width) -->
      <div class="card span-3">
        <h2>Revenue Over Time (Last 12 Months)</h2>
        <VueApexCharts type="area" height="300" :options="chartOptions" :series="chartSeries" />
      </div>

      <!-- Latest Orders (Span 2) -->
      <div class="card span-2">
        <h2>Latest Orders</h2>
        <table class="data-table">
          <thead>
            <tr><th>Order ID</th><th>Customer</th><th>Status</th><th class="right">Total</th></tr>
          </thead>
          <tbody>
            <tr v-for="o in summary.latest_orders" :key="o.order_id">
              <td class="mono">{{ o.order_id }}</td>
              <td>{{ o.customer_id }}</td>
              <td><span class="status-pill" :class="o.order_status.toLowerCase()">{{ o.order_status }}</span></td>
              <td class="right mono">{{ money(o.total) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Duplicate Alert (Span 1) -->
      <div class="card duplicate-card" v-if="duplicates.length">
        <h2>Duplicate Alert</h2>
        <p class="dup-text">{{ duplicates.length }} group(s) of duplicate orders found.</p>
        <div class="dup-group" v-for="(g, i) in duplicates.slice(0, 2)" :key="i">
          <p class="mono">{{ g.order_ids.join(' • ') }}</p>
          <p class="muted">{{ g.customer_id }} · Qty {{ g.quantity }}</p>
        </div>
        <router-link to="/app/duplicates" class="btn btn-ghost mt-auto">Review Duplicates</router-link>
      </div>
      <div class="card span-1" v-else>
        <h2>Duplicates</h2>
        <p class="muted">No duplicates found. All orders are unique.</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard { max-width: 1600px; margin: 0 auto; }
.page-header { margin-bottom: 24px; }
h1 { font-size: 28px; font-weight: 700; margin-bottom: 8px; }
.subtitle { color: var(--text-secondary); font-size: 14px; }
.grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
.card { background: white; border-radius: 24px; padding: 24px; box-shadow: 0 4px 12px rgba(0,0,0,0.03); }
.span-2 { grid-column: span 2; }
.span-3 { grid-column: span 3; }
.span-1 { grid-column: span 1; }
.kpi-card { border-radius: 24px; padding: 24px; display: flex; flex-direction: column; gap: 8px; }
.kpi-card.dark { background: var(--ink); color: white; }
.kpi-card.dark .kpi-value { color: var(--lime); }
.kpi-card.blue { background: var(--blue); color: white; }
.kpi-card.white { background: white; }
.kpi-card.orange { background: var(--orange); color: var(--ink); }
.kpi-label { font-size: 14px; font-weight: 600; opacity: 0.9; }
.kpi-value { font-size: 32px; font-weight: 800; }
.kpi-sub { font-size: 12px; opacity: 0.7; }
.data-table { width: 100%; border-collapse: collapse; margin-top: 16px; font-size: 14px; }
.data-table th, .data-table td { padding: 12px 0; border-bottom: 1px solid var(--line); text-align: left; }
.right { text-align: right; }
.mono { font-family: monospace; }
.duplicate-card { background: var(--cream); }
.dup-text { font-size: 14px; margin-bottom: 16px; }
.dup-group { background: white; padding: 12px; border-radius: 12px; margin-bottom: 12px; }
.dup-group p { margin: 0; }
.mt-auto { margin-top: auto; }
</style>