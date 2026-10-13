<script setup>
import { ref, onMounted } from 'vue'
import { useApi } from '../composables/useApi'

const { get, loading, error } = useApi()

const reportType = ref('product') // 'product' or 'date'
const productReport = ref(null)
const dateReport = ref(null)
const summaryReport = ref(null)

const fromDate = ref('')
const toDate = ref('')
const productId = ref('')

const summaryLoading = ref(false)

async function loadProductReport() {
  try {
    const params = new URLSearchParams()
    if (fromDate.value) params.set('from_date', fromDate.value)
    if (toDate.value) params.set('to_date', toDate.value)
    if (productId.value) params.set('product_id', productId.value)

    const response = await get(`/reports/product-sales?${params}`)
    productReport.value = response.data
  } catch (err) {
    console.error('Failed to load product report:', err)
  }
}

async function loadDateReport() {
  if (!fromDate.value || !toDate.value) {
    error.value = 'Both from_date and to_date are required for date-wise report'
    return
  }

  try {
    const params = new URLSearchParams({
      from_date: fromDate.value,
      to_date: toDate.value
    })
    const response = await get(`/reports/date-sales?${params}`)
    dateReport.value = response.data
  } catch (err) {
    console.error('Failed to load date report:', err)
  }
}

async function loadSummary() {
  summaryLoading.value = true
  try {
    const params = new URLSearchParams()
    if (fromDate.value) params.set('from_date', fromDate.value)
    if (toDate.value) params.set('to_date', toDate.value)

    const response = await get(`/reports/summary?${params}`)
    summaryReport.value = response.data
  } catch (err) {
    console.error('Failed to load summary:', err)
  } finally {
    summaryLoading.value = false
  }
}

function clearFilters() {
  fromDate.value = ''
  toDate.value = ''
  productId.value = ''
  productReport.value = null
  dateReport.value = null
  summaryReport.value = null
}

onMounted(() => {
  // Load summary by default
  loadSummary()
})
</script>

<template>
  <div class="panel">
    <div class="panel-header">
      <h2>📊 Sales Reports</h2>
    </div>

    <div class="tabs">
      <button :class="{ active: reportType === 'product' }" @click="reportType = 'product'">
        Product-wise Sales
      </button>
      <button :class="{ active: reportType === 'date' }" @click="reportType = 'date'">
        Date-wise Sales
      </button>
      <button :class="{ active: reportType === 'summary' }" @click="reportType = 'summary'; loadSummary()">
        Summary (KPIs)
      </button>
    </div>

    <!-- Filter Form -->
    <div class="filter-card">
      <div class="form-row">
        <div class="form-group">
          <label>From Date</label>
          <input v-model="fromDate" type="datetime-local" />
        </div>
        <div class="form-group">
          <label>To Date</label>
          <input v-model="toDate" type="datetime-local" />
        </div>
      </div>
      <div v-if="reportType === 'product'" class="form-group">
        <label>Product ID (optional filter)</label>
        <input v-model="productId" placeholder="PROD-001 (leave empty for all)" />
      </div>
      <div class="filter-actions">
        <button @click="reportType === 'product' ? loadProductReport() : loadDateReport()" :disabled="loading">
          Generate Report
        </button>
        <button @click="clearFilters" class="secondary">Clear</button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading">
      Loading...
    </div>

    <!-- Error -->
    <div v-if="error" class="error">{{ error }}</div>

    <!-- Product Report -->
    <div v-if="productReport" class="report-content">
      <div class="report-summary">
        <h3>Summary</h3>
        <div class="summary-grid">
          <div class="summary-item">
            <span class="label">Total Revenue</span>
            <span class="value">${{ productReport.summary.total_revenue?.toFixed(2) }}</span>
          </div>
          <div class="summary-item">
            <span class="label">Total Items Sold</span>
            <span class="value">{{ productReport.summary.total_quantity_sold }}</span>
          </div>
          <div class="summary-item">
            <span class="label">Total Orders</span>
            <span class="value">{{ productReport.summary.total_orders }}</span>
          </div>
          <div class="summary-item">
            <span class="label">Products</span>
            <span class="value">{{ productReport.summary.product_count }}</span>
          </div>
        </div>
      </div>

      <div class="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>Product</th>
              <th>Category</th>
              <th>Qty Sold</th>
              <th>Revenue</th>
              <th>Discounts</th>
              <th>Orders</th>
              <th>Last Sold</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="prod in productReport.products" :key="prod.product_id">
              <td><strong>{{ prod.product_name }}</strong></td>
              <td>{{ prod.category || '-' }}</td>
              <td>{{ prod.total_quantity_sold }}</td>
              <td>${{ prod.total_revenue?.toFixed(2) }}</td>
              <td>-${{ prod.total_discounts?.toFixed(2) }}</td>
              <td>{{ prod.order_count }}</td>
              <td>{{ prod.last_sold?.split('T')[0] }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Date Report -->
    <div v-if="dateReport" class="report-content">
      <div class="report-summary">
        <h3>Summary</h3>
        <div class="summary-grid">
          <div class="summary-item">
            <span class="label">Period</span>
            <span class="value">{{ dateReport.summary.period_days }} days</span>
          </div>
          <div class="summary-item">
            <span class="label">Total Revenue</span>
            <span class="value">${{ dateReport.summary.total_revenue?.toFixed(2) }}</span>
          </div>
          <div class="summary-item">
            <span class="label">Total Orders</span>
            <span class="value">{{ dateReport.summary.total_orders }}</span>
          </div>
          <div class="summary-item">
            <span class="label">Avg Daily Revenue</span>
            <span class="value">${{ dateReport.summary.average_daily_revenue?.toFixed(2) }}</span>
          </div>
          <div class="summary-item">
            <span class="label">Total Items Sold</span>
            <span class="value">{{ dateReport.summary.total_items_sold }}</span>
          </div>
          <div class="summary-item">
            <span class="label">Total Discounts</span>
            <span class="value">${{ dateReport.summary.total_discounts?.toFixed(2) }}</span>
          </div>
        </div>
      </div>

      <div class="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Orders</th>
              <th>Items</th>
              <th>Subtotal</th>
              <th>Discounts</th>
              <th>Tax</th>
              <th>Revenue</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="day in dateReport.daily_sales" :key="day.date">
              <td><strong>{{ day.date?.split('T')[0] }}</strong></td>
              <td>{{ day.order_count }}</td>
              <td>{{ day.item_count }}</td>
              <td>${{ day.total_subtotal?.toFixed(2) }}</td>
              <td>-${{ day.total_discounts?.toFixed(2) }}</td>
              <td>${{ day.total_tax?.toFixed(2) }}</td>
              <td><strong>${{ day.total_revenue?.toFixed(2) }}</strong></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Summary Report -->
    <div v-if="summaryReport" class="report-content">
      <h3>Key Performance Indicators</h3>
      <div class="summary-grid">
        <div class="summary-item large">
          <span class="label">Total Customers</span>
          <span class="value">{{ summaryReport.data.summary.total_customers }}</span>
        </div>
        <div class="summary-item large">
          <span class="label">Total Products</span>
          <span class="value">{{ summaryReport.data.summary.total_products }}</span>
        </div>
        <div class="summary-item large">
          <span class="label">Total Revenue</span>
          <span class="value highlight">${{ summaryReport.data.summary.total_revenue?.toFixed(2) }}</span>
        </div>
        <div class="summary-item large">
          <span class="label">Total Orders</span>
          <span class="value">{{ summaryReport.data.summary.total_orders }}</span>
        </div>
        <div class="summary-item large">
          <span class="label">Total Items Sold</span>
          <span class="value">{{ summaryReport.data.summary.total_items_sold }}</span>
        </div>
        <div class="summary-item large">
          <span class="label">Total Discounts</span>
          <span class="value">${{ summaryReport.data.summary.total_discounts?.toFixed(2) }}</span>
        </div>
        <div class="summary-item large">
          <span class="label">Avg Order Value</span>
          <span class="value">${{ summaryReport.data.summary.average_order_value?.toFixed(2) }}</span>
        </div>
      </div>

      <div v-if="summaryReport.data.summary.top_product" class="top-product-card">
        <h4>🏆 Top Product</h4>
        <div class="top-product-info">
          <strong>{{ summaryReport.data.summary.top_product.product_name }}</strong>
          <span>Category: {{ summaryReport.data.summary.top_product.category || 'N/A' }}</span>
          <span>Revenue: ${{ summaryReport.data.summary.top_product.total_revenue?.toFixed(2) }}</span>
          <span>Units Sold: {{ summaryReport.data.summary.top_product.total_quantity_sold }}</span>
        </div>
      </div>
    </div>

    <p v-if="!productReport && !dateReport && !summaryReport && !loading" class="empty-state">
      Configure date filters above and click "Generate Report"
    </p>
  </div>
</template>

<style scoped>
.panel {
  max-width: 1000px;
}

.panel-header {
  margin-bottom: 16px;
}

.panel-header h2 {
  margin: 0;
}

.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.tabs button {
  padding: 10px 20px;
  border: none;
  background: #f0f0f0;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
}

.tabs button:hover {
  background: #e0e0e0;
}

.tabs button.active {
  background: #42b983;
  color: white;
}

.filter-card {
  background: #f8f9fa;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.form-group {
  margin-bottom: 12px;
}

.form-group label {
  display: block;
  margin-bottom: 4px;
  font-weight: 500;
  color: #555;
}

.form-group input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.filter-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.filter-actions button {
  padding: 8px 16px;
  border: none;
  background: #42b983;
  color: white;
  border-radius: 6px;
}

.filter-actions button.secondary {
  background: #6c757d;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #666;
}

.error {
  color: #dc3545;
  margin-bottom: 16px;
}

.report-content {
  margin-top: 16px;
}

.report-content h3 {
  margin-bottom: 16px;
  color: #333;
}

.report-summary {
  margin-bottom: 24px;
}

.report-summary h3 {
  margin-bottom: 12px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
}

.summary-item {
  background: #f8f9fa;
  padding: 12px 16px;
  border-radius: 8px;
}

.summary-item .label {
  display: block;
  font-size: 12px;
  color: #666;
  margin-bottom: 4px;
}

.summary-item .value {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.summary-item .value.highlight {
  color: #42b983;
  font-size: 24px;
}

.summary-item.large {
  grid-column: span 1;
}

.table-wrapper {
  overflow-x: auto;
  margin-top: 16px;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #eee;
}

th {
  background: #f8f9fa;
  font-weight: 600;
  color: #555;
}

.top-product-card {
  background: #f8f9fa;
  padding: 16px;
  border-radius: 8px;
  margin-top: 24px;
}

.top-product-card h4 {
  margin-bottom: 12px;
}

.top-product-info {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  color: #555;
}

.top-product-info strong {
  color: #333;
}

.empty-state {
  text-align: center;
  color: #999;
  padding: 40px;
}
</style>
