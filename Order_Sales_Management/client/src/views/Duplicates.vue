<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'

const duplicates = ref([])
const loading = ref(true)
const errorMsg = ref('')

onMounted(async () => {
  try {
    const res = await api.get('/orders/duplicates')
    duplicates.value = res.data.duplicates
  } catch (err) {
    errorMsg.value = 'Failed to load duplicates.'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div v-if="loading" class="loading-state">Loading...</div>
  <div v-else-if="errorMsg" class="card error-state">{{ errorMsg }}</div>

  <div v-else-if="duplicates.length > 0" class="card warning-card">
    <div class="warning-header">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#92400E" stroke-width="2">
        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
        <line x1="12" y1="9" x2="12" y2="13"></line>
        <line x1="12" y1="17" x2="12.01" y2="17"></line>
      </svg>
      <h2>Duplicate Orders Detected</h2>
    </div>
    <p class="warning-text">These orders share the same customer, product, quantity, and price.</p>

    <div v-for="(d, i) in duplicates" :key="i" class="dup-group">
      <div class="dup-meta">
        <strong>Customer:</strong> {{ d.customer_id }} |
        <strong>Product ID:</strong> {{ d.product_id }} |
        <strong>Qty:</strong> {{ d.quantity }} |
        <strong>Price:</strong> ₹{{ d.unit_price.toFixed(2) }} |
        <strong>Date:</strong> {{ d.order_date }}
      </div>
      <div class="dup-ids">
        <span v-for="id in d.order_ids" :key="id" class="dup-id">{{ id }}</span>
      </div>
    </div>
  </div>

  <div v-else class="card success-card">
    <div class="success-header">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#065F46" stroke-width="2">
        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
        <polyline points="22 4 12 14.01 9 11.01"></polyline>
      </svg>
      <h2>No Duplicates Found</h2>
    </div>
    <p class="success-text">All orders are unique. Everything looks good!</p>
  </div>
</template>

<style scoped>
.loading-state, .error-state { padding: 40px; text-align: center; color: var(--text-secondary); }

.warning-card { background: #FEF3C7; border: none; }
.warning-header { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.warning-header h2 { color: #92400E; font-size: 18px; font-weight: 600; }
.warning-text { color: #92400E; margin-bottom: 24px; font-size: 14px; }

.dup-group {
  background: white;
  padding: 16px;
  border-radius: 12px;
  margin-bottom: 12px;
}
.dup-meta { font-size: 13px; color: #92400E; margin-bottom: 8px; }
.dup-ids { display: flex; gap: 8px; flex-wrap: wrap; }
.dup-id {
  background: #FEF3C7;
  padding: 4px 10px;
  border-radius: 99px;
  font-size: 12px;
  font-weight: 600;
  color: #92400E;
  font-family: monospace;
}

.success-card { background: #D1FAE5; border: none; }
.success-header { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.success-header h2 { color: #065F46; font-size: 18px; font-weight: 600; }
.success-text { color: #065F46; font-size: 14px; }
</style>