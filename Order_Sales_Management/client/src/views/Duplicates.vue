<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'

const duplicates = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    const res = await api.get('/orders/duplicates')
    duplicates.value = res.data.duplicates
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="card">
    <h2>Duplicate Orders</h2>
    <p style="color: var(--text-secondary); margin-bottom: 24px; font-size: 14px;">
      These orders share the same customer, product, quantity, and price.
    </p>

    <div v-if="loading">Loading...</div>
    <div v-else-if="duplicates.length === 0" style="text-align: center; padding: 32px; color: var(--text-secondary);">
      No duplicate orders detected.
    </div>
    <table v-else class="data-table">
      <thead>
        <tr>
          <th>Customer</th>
          <th>Product ID</th>
          <th>Quantity</th>
          <th>Price</th>
          <th>Date</th>
          <th>Order IDs</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(d, i) in duplicates" :key="i">
          <td>{{ d.customer_id }}</td>
          <td>{{ d.product_id }}</td>
          <td>{{ d.quantity }}</td>
          <td>${{ d.unit_price.toFixed(2) }}</td>
          <td>{{ d.order_date }}</td>
          <td class="mono">{{ d.order_ids.join(', ') }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
