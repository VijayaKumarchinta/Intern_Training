<script setup>
import { computed, onMounted } from 'vue'
import { useSummaryStore } from '@/stores/summary'
import { money, number, percent } from '@/utils/format'

const summaryStore = useSummaryStore()

onMounted(() => summaryStore.fetch())

const summary = computed(() => summaryStore.data || {})
const totalOrders = computed(() => summary.value.total_orders || 0)
const salesPct = computed(() => percent(summary.value.sales_orders, totalOrders.value))
const awaitingPct = computed(() => percent(summary.value.awaiting_action, totalOrders.value))
const totalUnits = computed(() => summary.value.units_sold || 0)

const colors = ['#2f5bff', '#c7f53c', '#ff7a45', '#2bb6a3', '#8b8cf7', '#f4c542', '#94a3b8']

const products = computed(() =>
  (summary.value.product_breakdown || []).slice(0, 7).map((item, index) => ({
    ...item,
    share: percent(item.revenue, summary.value.revenue),
    color: colors[index % colors.length],
    width: Math.max(percent(item.revenue, summary.value.revenue), 2),
  })),
)
</script>

<template>
  <aside class="totals-panel">
    <div class="totals-head">
      <h2>Totals</h2>
      <span class="all-time">All time</span>
    </div>

    <p class="totals-label">Revenue · Shipped + Delivered</p>
    <p class="totals-revenue mono">
      {{ money(summary.revenue || 0) }}
    </p>

    <div class="totals-split">
      <div class="totals-tile">
        <span>Sales orders</span>
        <strong>{{ salesPct.toFixed(1) }}%</strong>
        <small>{{ number(summary.sales_orders) }} of {{ number(totalOrders) }}</small>
      </div>
      <div class="totals-tile">
        <span>Awaiting</span>
        <strong>{{ awaitingPct.toFixed(1) }}%</strong>
        <small>{{ number(summary.awaiting_action) }} of {{ number(totalOrders) }}</small>
      </div>
    </div>

    <p class="by-product">By product</p>

    <div v-if="summaryStore.loading && !summaryStore.data" class="totals-loading">
      Loading totals…
    </div>
    <div v-else-if="summaryStore.error" class="totals-loading">
      {{ summaryStore.error }}
    </div>
    <ul v-else class="product-list">
      <li v-for="product in products" :key="product.product">
        <div class="product-row">
          <span class="product-name">
            <i :style="{ background: product.color }"></i>{{ product.product }}
          </span>
          <span class="mono">{{ product.share.toFixed(1) }}%</span>
        </div>
        <div class="product-bar">
          <span :style="{ width: `${product.width}%`, background: product.color }"></span>
        </div>
        <div class="product-meta">
          <span>{{ number(product.units) }} units</span>
          <span>{{ money(product.revenue, 0) }}</span>
        </div>
      </li>
    </ul>
    <div v-if="!summaryStore.loading && !products.length" class="totals-loading">
      No sales recorded yet.
    </div>

    <div class="totals-foot">
      <span>Total</span>
      <span class="mono">{{ number(totalUnits) }} units · 100%</span>
    </div>
  </aside>
</template>

<style scoped>
.totals-panel {
  width: 316px;
  flex: none;
  position: sticky;
  top: 16px;
  height: calc(100vh - 32px);
  display: flex;
  flex-direction: column;
  background: var(--ink);
  color: #fff;
  border-radius: 28px;
  padding: 28px 24px;
  overflow-y: auto;
}
.totals-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 22px;
}
.totals-head h2 {
  font-size: 22px;
  font-weight: 700;
  color: #fff;
}
.all-time {
  border: 1px solid rgba(199, 245, 60, 0.5);
  color: var(--lime);
  border-radius: 999px;
  padding: 5px 12px;
  font-size: 11.5px;
  font-weight: 600;
}
.totals-label {
  color: #9aa4b7;
  font-size: 12.5px;
  margin-bottom: 8px;
}
.totals-revenue {
  color: var(--lime);
  font-family: 'Inter Tight', sans-serif;
  font-size: 31px;
  font-weight: 700;
  letter-spacing: -0.04em;
  margin-bottom: 22px;
  word-break: break-word;
}
.totals-split {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-bottom: 26px;
}
.totals-tile {
  background: var(--ink-soft);
  border-radius: 16px;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.totals-tile span {
  color: #a9b2c3;
  font-size: 11.5px;
}
.totals-tile strong {
  font-family: 'Inter Tight', sans-serif;
  font-size: 24px;
  font-weight: 700;
  letter-spacing: -0.03em;
}
.totals-tile small {
  color: #808b9f;
  font-size: 10.5px;
}
.by-product {
  color: #808b9f;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  margin-bottom: 16px;
}
.product-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 15px;
}
.product-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-size: 12.5px;
  font-weight: 600;
  margin-bottom: 6px;
}
.product-name {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.product-name i {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex: none;
}
.product-bar {
  height: 4px;
  border-radius: 999px;
  background: #253048;
  overflow: hidden;
}
.product-bar span {
  display: block;
  height: 100%;
  border-radius: 999px;
}
.product-meta {
  margin-top: 5px;
  display: flex;
  justify-content: space-between;
  color: #808b9f;
  font-size: 10.5px;
}
.totals-loading {
  color: #808b9f;
  font-size: 12.5px;
  padding: 12px 0;
}
.totals-foot {
  margin-top: auto;
  padding-top: 18px;
  border-top: 1px solid #253048;
  display: flex;
  justify-content: space-between;
  color: #8b95a8;
  font-size: 11.5px;
  font-weight: 600;
}
.totals-foot .mono {
  color: var(--lime);
}
@media (max-width: 1280px) {
  .totals-panel {
    width: 280px;
    padding: 24px 20px;
  }
  .totals-revenue {
    font-size: 27px;
  }
}
</style>
