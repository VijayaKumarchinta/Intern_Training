<script setup>
import { ref, onMounted } from 'vue'
import { useApi } from '../composables/useApi'

const { get, post, loading, error } = useApi()

const products = ref([])
const totalCount = ref(0)

const newProduct = ref({
  product_id: '',
  name: '',
  category: '',
  unit_price: '',
  stock_quantity: 0,
  description: ''
})

const showForm = ref(false)
const formError = ref('')
const formSuccess = ref('')

async function loadProducts() {
  try {
    const response = await get('/products')
    products.value = response.data.products || []
    totalCount.value = response.data.total || 0
  } catch (err) {
    console.error('Failed to load products:', err)
  }
}

async function createProduct() {
  formError.value = ''
  formSuccess.value = ''

  if (!newProduct.value.product_id || !newProduct.value.name || !newProduct.value.unit_price) {
    formError.value = 'Product ID, Name, and Unit Price are required'
    return
  }

  try {
    const response = await post('/products', {
      product_id: newProduct.value.product_id,
      name: newProduct.value.name,
      category: newProduct.value.category || null,
      unit_price: parseFloat(newProduct.value.unit_price),
      stock_quantity: parseInt(newProduct.value.stock_quantity) || 0,
      description: newProduct.value.description || null
    })
    formSuccess.value = `Product ${response.data.product_id} created successfully!`
    newProduct.value = { product_id: '', name: '', category: '', unit_price: '', stock_quantity: 0, description: '' }
    showForm.value = false
    await loadProducts()
  } catch (err) {
    formError.value = err.message
  }
}

function resetForm() {
  newProduct.value = { product_id: '', name: '', category: '', unit_price: '', stock_quantity: 0, description: '' }
  formError.value = ''
  formSuccess.value = ''
}

onMounted(() => {
  loadProducts()
})
</script>

<template>
  <div class="panel">
    <div class="panel-header">
      <h2>📦 Products</h2>
      <span class="count">Total: {{ totalCount }}</span>
    </div>

    <div class="actions">
      <button @click="showForm = !showForm" :disabled="loading">
        {{ showForm ? 'Cancel' : '+' }} Add Product
      </button>
      <button @click="loadProducts" class="secondary" :disabled="loading">
        Refresh
      </button>
    </div>

    <div v-if="showForm" class="form-card">
      <h3>New Product</h3>
      <div class="form-group">
        <label>Product ID *</label>
        <input v-model="newProduct.product_id" placeholder="PROD-001" />
      </div>
      <div class="form-group">
        <label>Name *</label>
        <input v-model="newProduct.name" placeholder="Widget" />
      </div>
      <div class="form-group">
        <label>Category</label>
        <input v-model="newProduct.category" placeholder="Electronics" />
      </div>
      <div class="form-group">
        <label>Unit Price *</label>
        <input v-model="newProduct.unit_price" type="number" step="0.01" placeholder="29.99" />
      </div>
      <div class="form-group">
        <label>Stock Quantity</label>
        <input v-model.number="newProduct.stock_quantity" type="number" placeholder="100" />
      </div>
      <div class="form-group">
        <label>Description</label>
        <textarea v-model="newProduct.description" rows="2" placeholder="Product description..."></textarea>
      </div>
      <div class="form-actions">
        <button @click="createProduct" :disabled="loading">Create</button>
        <button @click="resetForm" class="secondary">Clear</button>
      </div>
      <p v-if="formError" class="error">{{ formError }}</p>
      <p v-if="formSuccess" class="success">{{ formSuccess }}</p>
    </div>

    <div v-if="error" class="error">{{ error }}</div>

    <div v-if="products.length > 0" class="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>Product ID</th>
            <th>Name</th>
            <th>Category</th>
            <th>Price</th>
            <th>Stock</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="prod in products" :key="prod.id">
            <td><strong>{{ prod.product_id }}</strong></td>
            <td>{{ prod.name }}</td>
            <td>{{ prod.category || '-' }}</td>
            <td>${{ prod.unit_price?.toFixed(2) }}</td>
            <td>{{ prod.stock_quantity }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <p v-else class="empty-state">
      {{ products.length === 0 && !showForm ? 'No products found. Add some products first.' : '' }}
    </p>
  </div>
</template>

<style scoped>
.panel {
  max-width: 900px;
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

.count {
  color: #666;
  font-size: 14px;
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
.form-group textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
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

.empty-state {
  text-align: center;
  color: #999;
  padding: 40px;
}
</style>
