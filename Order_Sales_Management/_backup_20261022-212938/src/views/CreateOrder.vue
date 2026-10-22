<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import { money } from '@/utils/format'

const router = useRouter()
const products = ref([])
const customers = ref([])
const errorMsg = ref('')
const submitting = ref(false)
const loading = ref(true)
const customerSearch = ref('')

const form = ref({
  order_id: '',
  customer_id: '',
  order_date: new Date().toISOString().split('T')[0],
  product_id: '',
  quantity: 1,
})

const selectedProduct = computed(() =>
  products.value.find((product) => product.product_id === form.value.product_id),
)

const filteredCustomers = computed(() => {
  const term = customerSearch.value.toLowerCase().trim()
  if (!term) return customers.value.slice(0, 200)
  return customers.value.filter(
    (c) =>
      c.customer_id.toLowerCase().includes(term) ||
      (c.cust_name && c.cust_name.toLowerCase().includes(term)) ||
      (c.email && c.email.toLowerCase().includes(term))
  ).slice(0, 50)
})

const lineTotal = computed(
  () => (selectedProduct.value?.current_price || 0) * (Number(form.value.quantity) || 0),
)

onMounted(async () => {
  try {
    const [prodRes, custRes] = await Promise.all([
      api.get('/products'),
      api.get('/customers'),
    ])
    products.value = prodRes.data.products
    customers.value = custRes.data.customers

    if (products.value.length) form.value.product_id = products.value[0].product_id
    if (customers.value.length) form.value.customer_id = customers.value[0].customer_id
  } catch (err) {
    errorMsg.value = 'Failed to load products and customers.'
  } finally {
    loading.value = false
  }
})

const handleSubmit = async () => {
  try {
    errorMsg.value = ''
    submitting.value = true
    const payload = {
      order_id: form.value.order_id.trim().toUpperCase(),
      customer_id: form.value.customer_id,
      order_date: form.value.order_date,
      items: [
        {
          product_id: form.value.product_id,
          quantity: Number(form.value.quantity),
        },
      ],
    }
    const res = await api.post('/orders', payload)
    router.push(`/app/orders/${res.data.order_id}`)
  } catch (err) {
    const body = err.response?.data
    errorMsg.value =
      (body?.errors && body.errors.join(', ')) || body?.error || 'Failed to create order.'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="create-page">
    <header class="page-head">
      <div>
        <p class="eyebrow">OrderSync · Admin</p>
        <h1>Create order</h1>
      </div>
      <div class="head-actions" style="display:flex; gap:12px; align-items:center;">
        <div class="avatar">A</div>
      </div>
    </header>

    <div v-if="loading" class="spinner-state">Loading form data…</div>

    <div v-else class="create-grid">
      <section class="card form-card">
        <h2>New order</h2>
        <p class="form-sub">Orders are forced to Pending status when created.</p>

        <div v-if="errorMsg" class="error-banner banner-gap">{{ errorMsg }}</div>

        <form class="order-form" @submit.prevent="handleSubmit">
          <div class="field full">
            <label for="order-id">Order ID</label>
            <input
              id="order-id"
              v-model="form.order_id"
              class="input"
              required
              pattern="ORD\d{4}"
              placeholder="ORD1234"
              title="Format: ORD followed by 4 digits"
            />
            <span class="hint">Format: ORD followed by 4 digits</span>
          </div>

          <div class="field full">
            <label for="customer-search">Search Customer</label>
            <input
              id="customer-search"
              v-model="customerSearch"
              class="input"
              placeholder="Type a customer name or ID to filter..."
            />
          </div>

          <div class="field full">
            <label for="customer">Select Customer</label>
            <select id="customer" v-model="form.customer_id" class="input" required>
              <option v-for="customer in filteredCustomers" :key="customer.customer_id" :value="customer.customer_id">
                {{ customer.customer_id }} - {{ customer.cust_name || customer.email || 'Unnamed' }}
              </option>
            </select>
            <span class="hint" v-if="customerSearch">Showing up to 50 matches</span>
          </div>

          <div class="field full">
            <label for="order-date">Order date</label>
            <input id="order-date" v-model="form.order_date" class="input" type="date" required />
          </div>

          <div class="field full">
            <label for="product">Product (price is locked by the server)</label>
            <select id="product" v-model="form.product_id" class="input" required>
              <option v-for="product in products" :key="product.product_id" :value="product.product_id">
                {{ product.pro_name }} ({{ money(product.current_price) }})
              </option>
            </select>
          </div>

          <div class="field full">
            <label for="quantity">Quantity</label>
            <input
              id="quantity"
              v-model.number="form.quantity"
              class="input"
              type="number"
              min="1"
              max="1000"
              required
            />
          </div>

          <div class="full">
            <button type="submit" class="btn btn-primary submit" :disabled="submitting">
              {{ submitting ? 'Creating…' : 'Create order' }}
            </button>
          </div>
        </form>
      </section>

      <aside class="side-column">
        <section class="preview-card">
          <p class="preview-label">Order total preview</p>
          <p class="preview-value mono">{{ money(lineTotal) }}</p>
          <p class="preview-meta">
            {{ form.quantity || 0 }} × {{ money(selectedProduct?.current_price || 0) }} ·
            {{ selectedProduct?.pro_name || 'No product selected' }}
          </p>
        </section>

        <section class="validation-card">
          <p class="validation-title">Validation</p>
          <p>
            Duplicates are flagged when customer, product, quantity, price and date all match
            another order. The server ignores any price sent by the browser.
          </p>
        </section>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.create-page {
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
.create-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 330px;
  gap: 16px;
  align-items: start;
}
.form-card {
  padding: 30px;
  border-radius: 26px;
}
.form-card h2 {
  font-size: 24px;
  font-weight: 700;
  letter-spacing: -0.035em;
}
.form-sub {
  margin: 6px 0 26px;
  font-size: 13.5px;
  color: var(--text-secondary);
}
.order-form {
  display: grid;
  grid-template-columns: 1fr;
  gap: 18px;
}
.full {
  grid-column: 1 / -1;
}
.submit {
  width: 100%;
  height: 52px;
  font-size: 15px;
  margin-top: 6px;
}
.side-column {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.preview-card {
  background: var(--ink);
  color: #fff;
  border-radius: 26px;
  padding: 26px;
}
.preview-label {
  font-size: 13px;
  color: #9aa4b7;
}
.preview-value {
  font-family: 'Inter Tight', sans-serif;
  font-size: 40px;
  font-weight: 700;
  letter-spacing: -0.05em;
  color: var(--lime);
  margin: 12px 0 14px;
  word-break: break-word;
}
.preview-meta {
  font-size: 12px;
  color: #9aa4b7;
}
.validation-card {
  background: var(--cream);
  border-radius: 26px;
  padding: 24px;
}
.validation-title {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #8a5a00;
  margin-bottom: 10px;
}
.validation-card p:last-child {
  font-size: 13.5px;
  line-height: 1.6;
  color: #6f5a25;
}
.banner-gap {
  margin-bottom: 20px;
}
@media (max-width: 1050px) {
  .create-grid {
    grid-template-columns: 1fr;
  }
  .side-column {
    flex-direction: row;
    flex-wrap: wrap;
  }
  .side-column > * {
    flex: 1;
    min-width: 240px;
  }
}
@media (max-width: 640px) {
  .order-form {
    grid-template-columns: 1fr;
  }
  .form-card {
    padding: 22px;
  }
}
</style>