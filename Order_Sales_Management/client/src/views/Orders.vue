<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'

const router = useRouter()
const orders = ref([])
const loading = ref(true)
const errorMsg = ref('')
const statusFilter = ref('')
const page = ref(1)
const total = ref(0)
const pages = ref(1)

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
          <td class="mono" style="text-align: right;">₹{{ order.total.toFixed(2) }}</td>
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
</style>