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
    let url = `/orders?page=${page.value}&per_page=20`
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
  <div class="card">
    <div class="header-row">
      <h2>Orders <span style="font-size: 14px; color: var(--text-secondary); font-weight: 400;">({{ total }} total)</span></h2>
      <select v-model="statusFilter" @change="page = 1; fetchOrders()">
        <option value="">All Statuses</option>
        <option value="Pending">Pending</option>
        <option value="Received">Received</option>
        <option value="Shipped">Shipped</option>
        <option value="Delivered">Delivered</option>
        <option value="Cancelled">Cancelled</option>
        <option value="Returned">Returned</option>
      </select>
    </div>

    <div v-if="errorMsg" class="error-banner">{{ errorMsg }}</div>
    <div v-if="loading" style="padding: 20px;">Loading...</div>
    
    <table v-else-if="orders.length > 0" class="data-table">
      <thead>
        <tr>
          <th>Order ID</th>
          <th>Customer</th>
          <th>Date</th>
          <th>Status</th>
          <th>Items</th>
          <th>Total</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="order in orders" :key="order.order_id" @click="router.push(`/app/orders/${order.order_id}`)" class="clickable-row">
          <td class="mono">{{ order.order_id }}</td>
          <td>{{ order.customer_id }}</td>
          <td>{{ order.order_date }}</td>
          <td>
            <span class="status-pill" :class="order.order_status.toLowerCase()">{{ order.order_status }}</span>
          </td>
          <td>{{ order.item_count }}</td>
          <td class="mono">${{ order.total.toFixed(2) }}</td>
        </tr>
      </tbody>
    </table>

    <div v-else class="empty-state">No orders found.</div>

    <div class="pagination" v-if="pages > 1">
      <button @click="prevPage" :disabled="page === 1" class="btn-primary" style="background: white; color: black; border: 1px solid var(--border-color);">Previous</button>
      <span>Page {{ page }} of {{ pages }}</span>
      <button @click="nextPage" :disabled="page === pages" class="btn-primary" style="background: white; color: black; border: 1px solid var(--border-color);">Next</button>
    </div>
  </div>
</template>

<style scoped>
.header-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.header-row select { width: 200px; margin-bottom: 0; }
.clickable-row { cursor: pointer; transition: background 0.1s; }
.clickable-row:hover { background: #F9FAFB; }
.status-pill { padding: 4px 10px; border-radius: 99px; font-size: 12px; font-weight: 600; }
.status-pill.pending { background: #F3F4F6; color: #374151; }
.status-pill.shipped { background: #DBEAFE; color: #1E40AF; }
.status-pill.delivered { background: #D1FAE5; color: #065F46; }
.status-pill.cancelled { background: #FEE2E2; color: #991B1B; }
.status-pill.received { background: #FEF3C7; color: #92400E; }
.status-pill.returned { background: #FCE7F3; color: #9D174D; }
.error-banner { background: #FEE2E2; color: #991B1B; padding: 12px; border-radius: 8px; margin-bottom: 16px; font-size: 14px; }
.empty-state { text-align: center; padding: 40px; color: var(--text-secondary); }
.pagination { display: flex; justify-content: center; align-items: center; gap: 16px; margin-top: 24px; font-size: 14px; }
</style>