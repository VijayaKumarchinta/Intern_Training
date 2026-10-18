<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'

const products = ref([])
const loading = ref(true)
const errorMsg = ref('')
const successMsg = ref('')
const editId = ref(null)
const editPrice = ref(0)
const showCreate = ref(false)
const newProduct = ref({ pro_name: '', current_price: 0 })

const fetchProducts = async () => {
  try {
    const res = await api.get('/products')
    products.value = res.data.products
  } catch (err) {
    errorMsg.value = 'Failed to load products.'
  } finally {
    loading.value = false
  }
}

const startEdit = (p) => {
  editId.value = p.product_id
  editPrice.value = p.current_price || 0
}

const savePrice = async (id) => {
  try {
    errorMsg.value = ''
    await api.patch(`/products/${id}`, { current_price: editPrice.value })
    successMsg.value = 'Price updated'
    editId.value = null
    fetchProducts()
  } catch (err) {
    errorMsg.value = err.response?.data?.error || 'Failed to update'
  }
}

const createProduct = async () => {
  try {
    errorMsg.value = ''
    await api.post('/products', newProduct.value)
    successMsg.value = 'Product created'
    showCreate.value = false
    newProduct.value = { pro_name: '', current_price: 0 }
    fetchProducts()
  } catch (err) {
    errorMsg.value = err.response?.data?.error || 'Failed to create'
  }
}

const deleteProduct = async (id) => {
  if (!confirm('Delete this product?')) return
  try {
    errorMsg.value = ''
    await api.delete(`/products/${id}`)
    successMsg.value = 'Product deleted'
    fetchProducts()
  } catch (err) {
    errorMsg.value = err.response?.data?.error || 'Failed to delete'
  }
}

onMounted(fetchProducts)
</script>

<template>
  <div class="card">
    <div class="header">
      <div>
        <h2>Products</h2>
        <p class="sub">Manage your product catalog. Prices are in ₹.</p>
      </div>
      <button @click="showCreate = !showCreate" class="btn-primary">+ New Product</button>
    </div>

    <div v-if="errorMsg" class="error-banner">{{ errorMsg }}</div>
    <div v-if="successMsg" class="success-banner">{{ successMsg }}</div>

    <div v-if="showCreate" class="create-form">
      <h3>Create Product</h3>
      <input v-model="newProduct.pro_name" placeholder="Product Name (e.g. Webcam)" />
      <input v-model.number="newProduct.current_price" type="number" min="0" step="0.01" placeholder="Price (₹)" />
      <div class="actions">
        <button @click="createProduct" class="btn-primary">Save</button>
        <button @click="showCreate = false" class="btn-secondary">Cancel</button>
      </div>
    </div>

    <div v-if="loading" class="loading">Loading...</div>
    <table v-else class="data-table">
      <thead>
        <tr>
          <th>ID</th>
          <th>Name</th>
          <th>Price (₹)</th>
          <th style="text-align: right;">Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="p in products" :key="p.product_id">
          <td class="mono">{{ p.product_id }}</td>
          <td>{{ p.pro_name }}</td>
          <td>
            <input v-if="editId === p.product_id" v-model.number="editPrice" type="number" min="0" step="0.01" class="edit-input" />
            <span v-else class="mono">{{ p.current_price ? `₹${p.current_price.toFixed(2)}` : '—' }}</span>
          </td>
          <td style="text-align: right;">
            <template v-if="editId === p.product_id">
              <button @click="savePrice(p.product_id)" class="btn-primary btn-sm">Save</button>
              <button @click="editId = null" class="btn-secondary btn-sm">Cancel</button>
            </template>
            <template v-else>
              <button @click="startEdit(p)" class="btn-secondary btn-sm">Edit</button>
              <button @click="deleteProduct(p.product_id)" class="btn-danger btn-sm" style="margin-left: 8px;">Delete</button>
            </template>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; }
.header h2 { font-size: 20px; margin-bottom: 4px; }
.sub { color: var(--text-secondary); font-size: 14px; }
.create-form { background: var(--bg-app); padding: 20px; border-radius: 12px; margin-bottom: 24px; }
.create-form h3 { font-size: 16px; margin-bottom: 12px; }
.actions { display: flex; gap: 12px; margin-top: 8px; }
.edit-input { width: 120px; margin: 0; padding: 6px; }
.btn-sm { padding: 6px 12px; font-size: 13px; }
.btn-danger { background: #EF4444; color: white; }
.error-banner { background: #FEE2E2; color: #991B1B; padding: 12px; border-radius: 8px; margin-bottom: 16px; }
.success-banner { background: #D1FAE5; color: #065F46; padding: 12px; border-radius: 8px; margin-bottom: 16px; }
.loading { padding: 24px; text-align: center; color: var(--text-secondary); }
</style>