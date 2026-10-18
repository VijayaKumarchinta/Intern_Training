<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'

const router = useRouter()
const products = ref([])
const customers = ref([])
const errorMsg = ref('')
const form = ref({
  order_id: '',
  customer_id: '',
  order_date: new Date().toISOString().split('T')[0],
  product_id: '',
  quantity: 1
})

onMounted(async () => {
  try {
    const [prodRes, custRes] = await Promise.all([
      api.get('/products'),
      api.get('/customers')
    ])
    
    products.value = prodRes.data.products
    customers.value = custRes.data.customers
    
    if (products.value.length) form.value.product_id = products.value[0].product_id
    if (customers.value.length) form.value.customer_id = customers.value[0].customer_id
  } catch (err) {
    errorMsg.value = 'Failed to load form data.'
  }
})

const handleSubmit = async () => {
  try {
    errorMsg.value = ''
    const payload = {
      order_id: form.value.order_id,
      customer_id: form.value.customer_id,
      order_date: form.value.order_date,
      items: [{ product_id: form.value.product_id, quantity: form.value.quantity }]
    }
    await api.post('/orders', payload)
    router.push('/app/orders')
  } catch (err) {
    errorMsg.value = err.response?.data?.errors?.join(', ') || err.response?.data?.error || 'Failed to create order'
  }
}
</script>

<template>
  <div class="card" style="max-width: 600px; margin: 0 auto;">
    <h2>Create New Order</h2>
    <p style="color: var(--text-secondary); margin-bottom: 24px; font-size: 14px;">Orders are forced to Pending status upon creation.</p>
    <div v-if="errorMsg" class="error-banner">{{ errorMsg }}</div>
    
    <form @submit.prevent="handleSubmit">
      <label>Order ID</label>
      <input v-model="form.order_id" required pattern="ORD\d{4}" placeholder="e.g. ORD1234" />

      <label>Customer</label>
      <select v-model="form.customer_id" required>
        <option v-for="c in customers" :key="c.customer_id" :value="c.customer_id">
          {{ c.customer_id }} - {{ c.cust_name || c.email || 'Unknown' }}
        </option>
      </select>

      <label>Order Date</label>
      <input v-model="form.order_date" type="date" required />

      <label>Product (Price is locked by server)</label>
      <select v-model="form.product_id" required>
        <option v-for="p in products" :key="p.product_id" :value="p.product_id">
          {{ p.pro_name }} (₹{{ p.current_price }})
        </option>
      </select>

      <label>Quantity</label>
      <input v-model.number="form.quantity" type="number" min="1" max="1000" required />

      <button type="submit" class="btn-primary" style="width: 100%; margin-top: 16px; padding: 14px;">Create Order</button>
    </form>
  </div>
</template>

<style scoped>
.error-banner { background: #FEE2E2; color: #991B1B; padding: 12px; border-radius: 8px; margin-bottom: 16px; font-size: 14px; }
</style>