<script setup>
import { computed, onMounted, ref } from 'vue'
import VueApexCharts from 'vue3-apexcharts'
import { useSummaryStore } from '@/stores/summary'
import { money, number, percent } from '@/utils/format'
import Icon from '@/components/Icon.vue'

const summaryStore = useSummaryStore()

const loading = ref(true)
const summary = computed(() => summaryStore.data || {})
const totalOrders = computed(() => summary.value.total_orders || 0)

const products = computed(() =>
  (summary.value.product_breakdown || []).map((item) => ({
    ...item,
    share: percent(item.revenue, summary.value.revenue),
  }))
)

const statusRows = computed(() => {
  const rows = summary.value.status_breakdown || []
  const byStatus = Object.fromEntries(rows.map((row) => [row.status, row.count]))
  return ['Pending', 'Received', 'Shipped', 'Delivered', 'Cancelled', 'Returned'].map((status) => ({
    status,
    count: byStatus[status] || 0,
    share: percent(byStatus[status] || 0, totalOrders.value)
  }))
})

onMounted(async () => {
  await summaryStore.fetch(true)
  loading.value = false
})
</script>

<template>
  <div class="totals-page">
    <header class="page-header">
      <div>
        <p class="eyebrow">OrderSync · Financials</p>
        <h1>Totals</h1>
        <p class="subtitle">Complete lifetime summary of revenue, orders, and performance.</p>
      </div>
    </header>

    <div v-if="loading" class="spinner-state">Loading totals…</div>

    <div v-else class="totals-layout">
      <!-- Hero Revenue Section -->
      <section class="hero-card">
        <div class="hero-top">
          <span class="hero-label">Total Lifetime Revenue</span>
          <span class="hero-badge">Shipped + Delivered</span>
        </div>
        <p class="hero-value">{{ money(summary.revenue) }}</p>
        <div class="hero-stats">
          <div class="hero-stat">
            <span class="stat-label">Total Orders</span>
            <span class="stat-value">{{ number(totalOrders) }}</span>
          </div>
          <div class="hero-stat">
            <span class="stat-label">Units Sold</span>
            <span class="stat-value">{{ number(summary.units_sold) }}</span>
          </div>
          <div class="hero-stat">
            <span class="stat-label">Avg. Order Value</span>
            <span class="stat-value">{{ money(summary.revenue / (summary.sales_orders || 1)) }}</span>
          </div>
        </div>
      </section>

      <div class="grid-row">
        <!-- Top Products Table -->
        <section class="card span-2">
          <div class="card-head">
            <h2>Top Products by Revenue</h2>
          </div>
          <table class="data-table">
            <thead>
              <tr>
                <th>Product Name</th>
                <th class="right">Units Sold</th>
                <th class="right">Revenue</th>
                <th class="right">Share</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="p in products" :key="p.product">
                <td class="font-medium">{{ p.product }}</td>
                <td class="right mono">{{ number(p.units) }}</td>
                <td class="right mono font-medium">{{ money(p.revenue) }}</td>
                <td class="right">
                  <span class="share-bar-bg">
                    <span class="share-bar-fill" :style="{ width: p.share + '%' }"></span>
                  </span>
                  {{ p.share.toFixed(1) }}%
                </td>
              </tr>
            </tbody>
          </table>
        </section>

        <!-- Order Status Breakdown -->
        <section class="card span-1">
          <div class="card-head">
            <h2>Order Status</h2>
          </div>
          <ul class="status-list">
            <li v-for="row in statusRows" :key="row.status">
              <div class="status-top">
                <span class="status-name">{{ row.status }}</span>
                <span class="status-count">{{ number(row.count) }}</span>
              </div>
              <div class="status-bar-bg">
                <div class="status-bar-fill" :class="row.status.toLowerCase()" :style="{ width: row.share + '%' }"></div>
              </div>
            </li>
          </ul>
        </section>
      </div>
    </div>
  </div>
</template>

<style scoped>
.totals-page {
  max-width: 1400px;
  margin: 0 auto;
}

/* Header */
.page-header { margin-bottom: 32px; }
.eyebrow { font-size: 12px; font-weight: 700; letter-spacing: 0.16em; text-transform: uppercase; color: var(--text-secondary); }
h1 { font-size: 32px; font-weight: 800; letter-spacing: -0.04em; margin-top: 8px; color: var(--ink); }
.subtitle { color: var(--text-secondary); font-size: 15px; margin-top: 8px; }

/* Hero Card */
.hero-card {
  background: var(--ink);
  color: #fff;
  border-radius: 32px;
  padding: 40px;
  margin-bottom: 24px;
  box-shadow: 0 10px 30px rgba(11, 18, 32, 0.15);
}
.hero-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.hero-label { font-size: 15px; font-weight: 600; color: #9aa4b7; }
.hero-badge { font-size: 12px; font-weight: 700; text-transform: uppercase; background: rgba(199, 245, 60, 0.15); color: var(--lime); padding: 6px 12px; border-radius: 99px; }
.hero-value { font-family: 'Inter Tight', sans-serif; font-size: 72px; font-weight: 800; letter-spacing: -0.05em; color: var(--lime); line-height: 1; margin-bottom: 40px; }

.hero-stats { display: flex; gap: 48px; border-top: 1px solid #2b3350; padding-top: 24px; }
.hero-stat { display: flex; flex-direction: column; gap: 6px; }
.stat-label { font-size: 13px; color: #9aa4b7; font-weight: 500; }
.stat-value { font-family: 'Inter Tight', sans-serif; font-size: 28px; font-weight: 700; color: #fff; }

/* Grid Row */
.grid-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; }
.span-2 { grid-column: span 2; }
.span-1 { grid-column: span 1; }
.card { background: #fff; border-radius: 24px; padding: 32px; box-shadow: 0 4px 12px rgba(0,0,0,0.03); border: 1px solid var(--line); }
.card-head { margin-bottom: 24px; }
h2 { font-size: 18px; font-weight: 700; color: var(--ink); }

/* Tables & Bars */
.data-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.data-table th { text-align: left; padding: 12px 0; border-bottom: 1px solid var(--line); color: var(--text-secondary); font-weight: 500; }
.data-table td { padding: 16px 0; border-bottom: 1px solid var(--line); vertical-align: middle; }
.right { text-align: right; }
.mono { font-family: monospace; }
.font-medium { font-weight: 600; color: var(--ink); }

.share-bar-bg { display: inline-block; width: 60px; height: 6px; background: #eef0f5; border-radius: 99px; margin-right: 8px; vertical-align: middle; }
.share-bar-fill { display: block; height: 100%; background: var(--blue); border-radius: 99px; }

.status-list { list-style: none; display: flex; flex-direction: column; gap: 20px; }
.status-top { display: flex; justify-content: space-between; font-size: 14px; margin-bottom: 8px; }
.status-name { font-weight: 500; color: var(--ink); }
.status-count { font-family: monospace; font-weight: 600; }
.status-bar-bg { height: 8px; background: #eef0f5; border-radius: 99px; overflow: hidden; }
.status-bar-fill { height: 100%; border-radius: 99px; }
.status-bar-fill.pending { background: #f4c542; }
.status-bar-fill.received { background: #8b8cf7; }
.status-bar-fill.shipped { background: var(--blue); }
.status-bar-fill.delivered { background: #2bb6a3; }
.status-bar-fill.cancelled { background: #ef5350; }
.status-bar-fill.returned { background: #ec4899; }

.spinner-state { text-align: center; padding: 60px; color: var(--text-secondary); }

@media (max-width: 1024px) {
  .grid-row { grid-template-columns: 1fr; }
  .span-2, .span-1 { grid-column: span 1; }
  .hero-value { font-size: 56px; }
  .hero-stats { flex-direction: column; gap: 24px; }
}
</style>