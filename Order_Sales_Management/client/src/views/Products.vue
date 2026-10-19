<script setup>
import { computed, onMounted, ref } from 'vue'
import api from '@/services/api'
import { useSummaryStore } from '@/stores/summary'
import { money, percent } from '@/utils/format'

const summaryStore = useSummaryStore()

const products = ref([])
const loading = ref(true)
const errorMsg = ref('')
const successMsg = ref('')
const editId = ref(null)
const editPrice = ref(0)
const showCreate = ref(false)
const saving = ref(false)
const newProduct = ref({ pro_name: '', current_price: null })

const COLORS = ['#2f5bff', '#c7f53c', '#ff7a45', '#2bb6a3', '#8b8cf7', '#f4c542', '#94a3b8']

const salesIndex = computed(() => {
  const rows = summaryStore.data?.product_breakdown || []
  return Object.fromEntries(rows.map((row) => [row.product, row]))
})

const cards = computed(() =>
  products.value.map((product, index) => {
    const sales = salesIndex.value[product.pro_name] || {}
    return {
      ...product,
      units: sales.units || 0,
      share: percent(sales.revenue, summaryStore.data?.revenue),
      color: COLORS[index % COLORS.length],
    }
  }),
)

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

const startEdit = (product) => {
  errorMsg.value = ''
  successMsg.value = ''
  editId.value = product.product_id
  editPrice.value = product.current_price || 0
  showCreate.value = false
}

const savePrice = async (id) => {
  if (saving.value) return
  try {
    errorMsg.value = ''
    saving.value = true
    await api.patch(`/products/${id}`, { current_price: editPrice.value })
    successMsg.value = 'Price updated. New orders will use it; existing orders keep their price.'
    editId.value = null
    await fetchProducts()
  } catch (err) {
    errorMsg.value = err.response?.data?.error || 'Failed to update price.'
  } finally {
    saving.value = false
  }
}

const createProduct = async () => {
  if (saving.value) return
  try {
    errorMsg.value = ''
    saving.value = true
    await api.post('/products', newProduct.value)
    successMsg.value = 'Product created.'
    showCreate.value = false
    newProduct.value = { pro_name: '', current_price: null }
    await fetchProducts()
  } catch (err) {
    errorMsg.value = err.response?.data?.error || 'Failed to create product.'
  } finally {
    saving.value = false
  }
}

const deleteProduct = async (product) => {
  if (!window.confirm(`Delete ${product.pro_name}? This cannot be undone.`)) return
  try {
    errorMsg.value = ''
    await api.delete(`/products/${product.product_id}`)
    successMsg.value = 'Product deleted.'
    await fetchProducts()
  } catch (err) {
    errorMsg.value = err.response?.data?.error || 'Failed to delete product.'
  }
}

onMounted(() => {
  summaryStore.fetch()
  fetchProducts()
})
</script>

<template>
  <div class="products-page">
    <header class="page-head">
      <div>
        <p class="eyebrow">OrderSync · Admin</p>
        <h1>Products</h1>
        <p class="page-sub">Manage your catalog. Prices are in ₹ and apply to new orders only.</p>
      </div>
      <div class="head-actions">
        <button class="btn btn-primary" @click="showCreate = !showCreate">
          {{ showCreate ? 'Close' : '+ New product' }}
        </button>
        <div class="avatar">A</div>
      </div>
    </header>

    <div v-if="showCreate" class="create-bar">
      <span class="create-label">Create product</span>
      <input v-model="newProduct.pro_name" class="input" placeholder="Product name (e.g. Webcam)" />
      <input
        v-model.number="newProduct.current_price"
        class="input price-input"
        type="number"
        min="0"
        step="0.01"
        placeholder="Price (₹)"
      />
      <button class="btn btn-dark" :disabled="saving" @click="createProduct">Save</button>
      <button class="btn btn-ghost" @click="showCreate = false">Cancel</button>
    </div>

    <div v-if="errorMsg" class="error-banner banner-gap">{{ errorMsg }}</div>
    <div v-if="successMsg" class="success-banner banner-gap">{{ successMsg }}</div>

    <div v-if="loading" class="spinner-state">Loading products…</div>

    <div v-else class="product-grid">
      <article v-for="product in cards" :key="product.product_id" class="product-card">
        <div class="product-top">
          <span class="product-tag">
            <i :style="{ background: product.color }"></i>ID {{ product.product_id }}
          </span>
          <span class="share-tag">
            {{ product.share.toFixed(1) }}% of revenue
          </span>
        </div>

        <h2>{{ product.pro_name }}</h2>

        <template v-if="editId === product.product_id">
          <label class="price-label" :for="`price-${product.product_id}`">New price (₹)</label>
          <input
            :id="`price-${product.product_id}`"
            v-model.number="editPrice"
            class="input price-edit"
            type="number"
            min="0"
            step="0.01"
          />
        </template>
        <p v-else class="product-price">{{ money(product.current_price) }}</p>

        <div class="share-bar">
          <span :style="{ width: `${Math.max(product.share, 2)}%`, background: product.color }"></span>
        </div>
        <p class="units">{{ product.units }} units sold</p>

        <div class="product-actions">
          <template v-if="editId === product.product_id">
            <button class="btn btn-sm btn-dark" :disabled="saving" @click="savePrice(product.product_id)">
              Save
            </button>
            <button class="btn btn-sm btn-ghost" @click="editId = null">Cancel</button>
          </template>
          <template v-else>
            <button class="btn btn-sm btn-ghost" @click="startEdit(product)">Edit price</button>
            <button class="btn btn-sm btn-outline-red" @click="deleteProduct(product)">Delete</button>
          </template>
        </div>
      </article>

      <p v-if="!cards.length" class="empty-state">No products yet. Create your first one.</p>
    </div>
  </div>
</template>

<style scoped>
.products-page {
  max-width: 1400px;
}
.page-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
  margin-bottom: 20px;
}
.page-head h1 {
  font-size: clamp(30px, 2.6vw, 40px);
  font-weight: 700;
  letter-spacing: -0.045em;
  margin-top: 6px;
}
.page-sub {
  margin-top: 6px;
  font-size: 14px;
  color: var(--text-secondary);
}
.head-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}
.create-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  background: var(--lime);
  border-radius: 24px;
  padding: 16px 20px;
  margin-bottom: 18px;
}
.create-label {
  font-size: 14px;
  font-weight: 700;
  margin-right: 4px;
}
.create-bar .input {
  border-color: transparent;
  height: 46px;
  flex: 1;
  min-width: 200px;
}
.price-input {
  max-width: 180px;
}
.product-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 16px;
}
.product-card {
  background: #fff;
  border-radius: 24px;
  padding: 22px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 250px;
  box-shadow: var(--shadow-card);
}
.product-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  flex-wrap: wrap;
}
.product-tag {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-size: 11.5px;
  font-weight: 600;
  color: var(--text-secondary);
}
.product-tag i {
  width: 9px;
  height: 9px;
  border-radius: 50%;
}
.share-tag {
  background: #f1f3f8;
  border-radius: 999px;
  padding: 5px 10px;
  font-size: 10.5px;
  font-weight: 600;
  color: #4b5563;
  white-space: nowrap;
}
.product-card h2 {
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.035em;
}
.product-price {
  font-family: 'Inter Tight', sans-serif;
  font-size: 28px;
  font-weight: 700;
  letter-spacing: -0.04em;
}
.price-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: -6px;
}
.price-edit {
  height: 44px;
  border-color: var(--blue);
}
.share-bar {
  height: 5px;
  border-radius: 999px;
  background: #eef0f5;
  overflow: hidden;
  margin-top: auto;
}
.share-bar span {
  display: block;
  height: 100%;
  border-radius: 999px;
}
.units {
  font-size: 12px;
  color: var(--text-secondary);
}
.product-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.banner-gap {
  margin-bottom: 18px;
}
@media (max-width: 600px) {
  .create-bar .input,
  .price-input {
    max-width: none;
    width: 100%;
  }
}
</style>
