<script setup>
import { ref, onMounted } from 'vue'
import { useApi } from '../composables/useApi'

const { get, post, put, loading, error } = useApi()

const orders = ref([])
const orderItems = ref([])

const newOrder = ref({
  customer_id: '',
  items: '',
  order_id: '',
  discount_percent: '',
  shipping_address: '',
  notes: ''
})

const showForm = ref(false)
const formError = ref('')
const formSuccess = ref('')

const updateStatusForm = ref({
  order_id: '',
  status: 'processing'
})

async function loadOrders() {
  try {
    const response = await get('/orders?limit=20')
    orders.value = response.data.orders || []
  } catch (err) {
    console.error('Failed to load orders:', err)
  }
}

async function createOrder() {
  formError.value = ''
  formSuccess.value = ''

  if (!newOrder.value.customer_id || !newOrder.value.items) {
    formError.value = 'Customer ID and Items are required'
    return
  }

  let items
  try {
    items = JSON.parse(newOrder.value.items)
    if (!Array.isArray(items) || items.length === 0) {
      throw new Error('Items must be a non-empty array')
    }
  } catch (e) {
    formError.value = 'Invalid JSON for items. Use format: [{"product_id": "PROD-001", "quantity": 2}]'
    return
  }

  try {
    const response = await post('/orders', {
      customer_id: newOrder.value.customer_id,
      items: items,
      order_id: newOrder.value.order_id || undefined,
      discount_percent: newOrder.value.discount_percent ? parseFloat(newOrder.value.discount_percent) : undefined,
      shipping_address: newOrder.value.shipping_address || undefined,
      notes: newOrder.value.notes || undefined
    })
    formSuccess.value = `Order ${response.data.order_id} created! Total: $${response.data.total?.toFixed(2)}`
    newOrder.value = { customer_id: '', items: '', order_id: '', discount_percent: '', shipping_address: '', notes: '' }
    showForm.value = false
    await loadOrders()
  } catch (err) {
    formError.value = err.message
  }
}

async function updateStatus() {
  if (!updateStatusForm.value.order_id || !updateStatusForm.value.status) {
    formError.value = 'Please select an order and status'
    return
  }

  try {
    await put(`/orders/${updateStatusForm.value.order_id}/status`, {
      status: updateStatusForm.value.status
    })
    formSuccess.value = `Status updated to ${updateStatusForm.value.status}`
    updateStatusForm.value = { order_id: '', status: 'processing' }
    await loadOrders()
  } catch (err) {
    formError.value = err.message
  }
}

function resetForm() {
  newOrder.value = { customer_id: '', items: '', order_id: '', discount_percent: '', shipping_address: '', notes: '' }
  formError.value = ''
  formSuccess.value = ''
}

const statusOptions = [
  { value: 'pending', label: 'Pending' },
  { value: 'processing', label: 'Processing' },
  { value: 'shipped', label: 'Shipped' },
  { value: 'delivered', label: 'Delivered' },
  { value: 'cancelled', label: 'Cancelled' },
  { value: 'returned', label: 'Returned' }
]

onMounted(() => {
  loadOrders()
})
</script>

<template>
  <div class="panel">
    <div class="panel-header">
      <h2>🛒 Orders</h2>
    </div>

    <div class="actions">
      <button @click="showForm = !showForm" :disabled="loading">
        {{ showForm ? 'Cancel' : '+' }} Create Order
      </button>
      <button @click="loadOrders" class="secondary" :disabled="loading">
        Refresh
      </button>
    </div>

    <!-- Create Order Form -->
    <div v-if="showForm" class="form-card">
      <h3>New Order</h3>
      <div class="form-group">
        <label>Customer ID *</label>
        <input v-model="newOrder.customer_id" placeholder="CUST-001" />
      </div>
      <div class="form-group">
        <label>Items (JSON) *</label>
        <textarea v-model="newOrder.items" rows="4" placeholder='[{"product_id": "PROD-001", "quantity": 2}]'></textarea>
        <small class="hint">Format: [{"product_id": "PROD-001", "quantity": 2}, {"product_id": "PROD-002", "quantity": 1}]</small>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>Order ID (optional)</label>
          <input v-model="newOrder.order_id" placeholder="Auto-generated if empty" />
        </div>
        <div class="form-group">
          <label>Discount %</label>
          <input v-model="newOrder.discount_percent" type="number" step="0.01" placeholder="0" />
        </div>
      </div>
      <div class="form-group">
        <label>Shipping Address</label>
        <textarea v-model="newOrder.shipping_address" rows="2" placeholder="Shipping address..."></textarea>
      </div>
      <div class="form-group">
        <label>Notes</label>
        <textarea v-model="newOrder.notes" rows="2" placeholder="Order notes..."></textarea>
      </div>
      <div class="form-actions">
        <button @click="createOrder" :disabled="loading">Create Order</button>
        <button @click="resetForm" class="secondary">Clear</button>
      </div>
      <p v-if="formError" class="error">{{ formError }}</p>
      <p v-if="formSuccess" class="success">{{ formSuccess }}</p>
    </div>

    <!-- Update Status Form -->
    <div class="status-section">
      <h3>Update Order Status</h3>
      <div class="form-row">
        <div class="form-group">
          <label>Order ID</label>
          <input v-model="updateStatusForm.order_id" placeholder="ORD-..." />
        </div>
        <div class="form-group">
          <label>New Status</label>
          <select v-model="updateStatusForm.status">
            <option v-for="opt in statusOptions" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </option>
          </select>
        </div>
      </div>
      <button @click="updateStatus" class="update-btn" :disabled="loading">Update Status</button>
    </div>

    <div v-if="error" class="error">{{ error }}</div>

    <div v-if="orders.length > 0" class="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>Order ID</th>
            <th>Customer</th>
            <th>Date</th>
            <th>Status</th>
            <th>Subtotal</th>
            <th>Discount</th>
            <th>Tax</th>
            <th>Total</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="order in orders" :key="order.id">
            <td><strong>{{ order.order_id }}</strong></td>
            <td>{{ order.customer?.name || order.customer?.customer_id }}</td>
            <td>{{ order.order_date?.split('T')[0] }}</td>
            <td>
              <span :class="['status-badge', 'status-' + order.status]">
                {{ order.status }}
              </span>
            </td>
            <td>${{ order.subtotal?.toFixed(2) }}</td>
            <td>-${{ order.discount?.toFixed(2) }}</td>
            <td>${{ order.tax?.toFixed(2) }}</td>
            <td><strong>${{ order.total?.toFixed(2) }}</strong></td>
          </tr>
        </tbody>
      </table>
    </div>

    <p v-else class="empty-state">
      {{ orders.length === 0 && !showForm ? 'No orders found. Create one above.' : '' }}
    </p>
  </div>
</template>

<style scoped>
.panel {
  max-width: 1100px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.panel-header h2 {
  margin: 0;
}

.actions {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.actions button {
  padding: 8px 16px;
  border: none;
  background: #42b983;
  color: white;
  border-radius: 6px;
  font-size: 14px;
}

.actions button.secondary {
  background: #6c757d;
}

.actions button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.form-card {
  background: #f8f9fa;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.form-card h3 {
  margin-bottom: 12px;
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

.form-group input,
.form-group textarea,
.form-group select {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
}

.form-group .hint {
  color: #999;
  font-size: 12px;
  margin-top: 4px;
  display: block;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.form-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.form-actions button {
  padding: 8px 16px;
  border: none;
  background: #42b983;
  color: white;
  border-radius: 6px;
}

.form-actions button.secondary {
  background: #6c757d;
}

.error {
  color: #dc3545;
  margin-top: 8px;
  font-size: 14px;
}

.success {
  color: #28a745;
  margin-top: 8px;
  font-size: 14px;
}

.status-section {
  background: #f8f9fa;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.status-section h3 {
  margin-bottom: 12px;
}

.update-btn {
  padding: 8px 16px;
  border: none;
  background: #007bff;
  color: white;
  border-radius: 6px;
  margin-top: 8px;
}

.update-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.table-wrapper {
  overflow-x: auto;
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

.status-badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

.status-pending { background: #fff3cd; color: #856404; }
.status-processing { background: #cce5ff; color: #004085; }
.status-shipped { background: #d4edda; color: #155724; }
.status-delivered { background: #c3e6cb; color: #245245; }
.status-cancelled { background: #f8d7da; color: #721c24; }
.status-returned { background: #e2e3e5; color: #383d41; }

.empty-state {
  text-align: center;
  color: #999;
  padding: 40px;
}
</style>
