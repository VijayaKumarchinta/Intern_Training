<script setup>
import { computed, onMounted, ref } from 'vue'
import api from '@/services/api'
import { percent, number } from '@/utils/format'

const customers = ref([])
const loading = ref(true)
const showCreate = ref(false)
const errorMsg = ref('')
const successMsg = ref('')
const saving = ref(false)
const newCustomer = ref({ customer_id: '', cust_name: '', email: '' })

const linked = computed(() => customers.value.filter((customer) => customer.user_id))
const linkedShare = computed(() => percent(linked.value.length, customers.value.length))
const unlinkedShare = computed(() =>
  percent(customers.value.length - linked.value.length, customers.value.length),
)

const fetchCustomers = async () => {
  try {
    const res = await api.get('/customers')
    customers.value = res.data.customers
  } catch (err) {
    errorMsg.value = 'Failed to load customers.'
  } finally {
    loading.value = false
  }
}

const createCustomer = async () => {
  if (saving.value) return
  try {
    errorMsg.value = ''
    successMsg.value = ''
    saving.value = true
    await api.post('/customers', newCustomer.value)
    successMsg.value = 'Customer created.'
    showCreate.value = false
    newCustomer.value = { customer_id: '', cust_name: '', email: '' }
    await fetchCustomers()
  } catch (err) {
    errorMsg.value = err.response?.data?.error || 'Failed to create customer.'
  } finally {
    saving.value = false
  }
}

onMounted(fetchCustomers)
</script>

<template>
  <div class="customers-page">
    <header class="page-head">
      <div>
        <p class="eyebrow">OrderSync · Admin</p>
        <h1>Customers</h1>
        <p class="page-sub">Manage customer records. Only admins can see this list.</p>
      </div>
      <div class="head-actions">
        <button class="btn btn-primary" @click="showCreate = !showCreate">
          {{ showCreate ? 'Close' : '+ New customer' }}
        </button>
        <div class="avatar">A</div>
      </div>
    </header>

    <section class="stats">
      <div class="stat dark-stat">
        <p class="stat-label">Total customers</p>
        <p class="stat-big">{{ number(customers.length) }}</p>
        <p class="stat-foot">100% of records</p>
      </div>
      <div class="stat blue-stat">
        <p class="stat-label">Linked to a user</p>
        <p class="stat-big">{{ linkedShare.toFixed(1) }}%</p>
        <p class="stat-foot">{{ linked.length }} of {{ number(customers.length) }} registered</p>
      </div>
      <div class="stat light-stat">
        <p class="stat-label">Unlinked</p>
        <p class="stat-big">{{ unlinkedShare.toFixed(1) }}%</p>
        <p class="stat-foot">
          {{ number(customers.length - linked.length) }} have no login yet
        </p>
      </div>
    </section>

    <div v-if="showCreate" class="create-bar">
      <span class="create-label">New customer</span>
      <input v-model="newCustomer.customer_id" class="input" placeholder="Customer ID (e.g. C1234)" />
      <input v-model="newCustomer.cust_name" class="input" placeholder="Full name" />
      <input v-model="newCustomer.email" class="input" type="email" placeholder="Email (optional)" />
      <button class="btn btn-dark" :disabled="saving" @click="createCustomer">
        {{ saving ? 'Saving…' : 'Save' }}
      </button>
    </div>

    <div v-if="errorMsg" class="error-banner banner-gap">{{ errorMsg }}</div>
    <div v-if="successMsg" class="success-banner banner-gap">{{ successMsg }}</div>

    <section class="card table-card">
      <div class="table-top">
        <h2>Customer records</h2>
        <span class="muted">
          {{ loading ? 'Loading…' : `Showing first 50 of ${number(customers.length)}` }}
        </span>
      </div>

      <div v-if="loading" class="spinner-state">Loading customers…</div>

      <div v-else class="scroll-x">
        <table class="table">
          <thead>
            <tr>
              <th>Customer ID</th>
              <th>Name</th>
              <th>Email</th>
              <th class="right">Linked user</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="customer in customers.slice(0, 50)" :key="customer.customer_id">
              <td class="mono strong">{{ customer.customer_id }}</td>
              <td>{{ customer.cust_name || '—' }}</td>
              <td class="muted">{{ customer.email || '—' }}</td>
              <td class="right">
                <span v-if="customer.user_id" class="pill user-pill">
                  User #{{ customer.user_id }}
                </span>
                <span v-else class="pill unlinked-pill">Unlinked</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <p v-if="!loading && !customers.length" class="empty-state">No customers yet.</p>
    </section>
  </div>
</template>

<style scoped>
.customers-page {
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
.stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}
.stat {
  border-radius: 26px;
  padding: 24px;
  min-height: 150px;
  display: flex;
  flex-direction: column;
}
.dark-stat {
  background: var(--ink);
  color: #fff;
}
.blue-stat {
  background: var(--blue);
  color: #fff;
}
.light-stat {
  background: #fff;
}
.stat-label {
  font-size: 13.5px;
  color: rgba(255, 255, 255, 0.85);
}
.light-stat .stat-label {
  color: var(--text-secondary);
}
.stat-big {
  font-family: 'Inter Tight', sans-serif;
  font-size: clamp(34px, 3.4vw, 48px);
  font-weight: 800;
  letter-spacing: -0.05em;
  line-height: 1;
  margin: auto 0 10px;
}
.dark-stat .stat-big {
  color: var(--lime);
}
.stat-foot {
  font-size: 12.5px;
  color: rgba(255, 255, 255, 0.8);
}
.light-stat .stat-foot {
  color: var(--text-secondary);
}
.create-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  background: var(--lime);
  border-radius: 24px;
  padding: 16px 20px;
  margin-bottom: 16px;
}
.create-label {
  font-size: 14px;
  font-weight: 700;
  margin-right: 4px;
}
.create-bar .input {
  flex: 1;
  min-width: 180px;
  border-color: transparent;
  height: 46px;
}
.table-card {
  padding: 0;
  overflow: hidden;
}
.table-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 22px 24px;
  flex-wrap: wrap;
}
h2 {
  font-size: 19px;
  font-weight: 700;
  letter-spacing: -0.03em;
}
.table-top .muted {
  font-size: 12.5px;
}
.strong {
  font-weight: 600;
}
.right {
  text-align: right;
}
.user-pill {
  background: var(--lavender);
  color: #4b3fa8;
}
.unlinked-pill {
  background: #f1f3f8;
  color: #6b7280;
}
.banner-gap {
  margin-bottom: 16px;
}
@media (max-width: 860px) {
  .stats {
    grid-template-columns: 1fr;
  }
  .create-bar .input {
    min-width: 100%;
  }
}
</style>
