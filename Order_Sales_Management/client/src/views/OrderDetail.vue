<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/services/api'

const route = useRoute()
const router = useRouter()
const order = ref(null)
const loading = ref(true)
const errorMsg = ref('')
const isAdmin = ref(false)

const allowedTransitions = {
  Pending: ['Received', 'Shipped', 'Cancelled'],
  Received: ['Shipped', 'Cancelled'],
  Shipped: ['Delivered', 'Returned'],
  Delivered: ['Returned'],
  Cancelled: [],
  Returned: []
}

const fetchOrder = async () => {
  try {
    const res = await api.get(`/orders/${route.params.id}`)
    order.value = res.data
  } catch (err) {
    errorMsg.value = 'Order not found or access denied.'
  } finally {
    loading.value = false
  }
}

const updateStatus = async (newStatus) => {
  try {
    await api.patch(`/orders/${order.value.order_id}/status`, { order_status: newStatus })
    order.value.order_status = newStatus
  } catch (err) {
    alert(err.response?.data?.error || 'Failed to update status')
  }
}

onMounted(() => {
  const user = JSON.parse(localStorage.getItem('user'))
  isAdmin.value = user?.role === 'admin'
  fetchOrder()
})
</script>

<template>
  <div v-if="loading">Loading...</div>
  <div v-else-if="errorMsg" class="card">{{ errorMsg }}</div>
  <div v-else class="order-detail">
    <button @click="router.push('/app/orders')" class="back-btn">← Back to Orders</button>
    
    <div class="card header-card">
      <div>
        <h2>Order #{{ order.order_id }}</h2>
        <p style="color: var(--text-secondary); margin-top: 4px;">Placed on {{ order.order_date }}</p>
      </div>
      <div class="status-action">
        <span class="status-pill" :class="order.order_status.toLowerCase()">{{ order.order_status }}</span>
        <select v-if="isAdmin && allowedTransitions[order.order_status].length > 0" @change="updateStatus($event.target.value)" class="status-select">
          <option value="">Change Status...</option>
          <option v-for="s in allowedTransitions[order.order_status]" :key="s" :value="s">{{ s }}</option>
        </select>
      </div>
    </div>

    <div class="card">
      <h3>Line Items</h3>
      <table class="data-table" style="margin-top: 16px;">
        <thead>
          <tr><th>Product ID</th><th>Quantity</th><th>Unit Price</th><th>Line Total</th></tr>
        </thead>
        <tbody>
          <tr v-for="item in order.items" :key="item.order_item_id">
            <td>{{ item.product_id }}</td>
            <td>{{ item.quantity }}</td>
            <td class="mono">${{ item.unit_price.toFixed(2) }}</td>
            <td class="mono">${{ item.line_total.toFixed(2) }}</td>
          </tr>
        </tbody>
      </table>
      <div class="total-row">
        <span>Total:</span>
        <span class="mono">${{ order.total.toFixed(2) }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.back-btn { background: none; border: none; color: var(--accent-blue); cursor: pointer; padding: 0 0 16px 0; font-size: 14px; font-weight: 500; }
.header-card { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.status-action { display: flex; align-items: center; gap: 16px; }
.status-select { width: auto; margin-bottom: 0; padding: 8px; }
.total-row { display: flex; justify-content: space-between; font-weight: 700; font-size: 18px; margin-top: 16px; padding-top: 16px; border-top: 1px solid var(--border-color); }
.status-pill { padding: 6px 12px; border-radius: 99px; font-size: 14px; font-weight: 600; }
.status-pill.pending { background: #F3F4F6; color: #374151; }
.status-pill.shipped { background: #DBEAFE; color: #1E40AF; }
.status-pill.delivered { background: #D1FAE5; color: #065F46; }
.status-pill.cancelled { background: #FEE2E2; color: #991B1B; }
.status-pill.received { background: #FEF3C7; color: #92400E; }
.status-pill.returned { background: #FCE7F3; color: #9D174D; }
</style>