<script setup>
import { computed, onMounted, ref } from 'vue'
import api from '@/services/api'
import { percent, number } from '@/utils/format'

const customers = ref([])
const loading = ref(true)
const errorMsg = ref('')
const successMsg = ref('')
const showCreate = ref(false)
const saving = ref(false)
const search = ref('')

// Link modal state
const linkingCustomer = ref(null)
const targetUserId = ref('')

const newCustomer = ref({ customer_id: '', cust_name: '', email: '' })

const filtered = computed(() => {
  const term = search.value.toLowerCase().trim()
  if (!term) return customers.value
  return customers.value.filter(
    (c) =>
      c.customer_id.toLowerCase().includes(term) ||
      (c.cust_name && c.cust_name.toLowerCase().includes(term)) ||
      (c.email && c.email.toLowerCase().includes(term))
  )
})

const linked = computed(() => customers.value.filter((c) => c.user_id))
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

const startLink = (customer) => {
  linkingCustomer.value = customer
  targetUserId.value = ''
}

const submitLink = async () => {
  if (!targetUserId.value) return
  try {
    errorMsg.value = ''
    successMsg.value = ''
    saving.value = true
    await api.patch(`/customers/${linkingCustomer.value.customer_id}/link`, {
      user_id: parseInt(targetUserId.value, 10),
    })
    successMsg.value = `Linked ${linkingCustomer.value.customer_id} to user ${targetUserId.value}.`
    linkingCustomer.value = null
    await fetchCustomers()
  } catch (err) {
    errorMsg.value = err.response?.data?.error || 'Failed to link customer.'
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  window.addEventListener('open-create-form', () => { showCreate.value = true })
  fetchCustomers()
})
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

    <div v-if="linkingCustomer" class="create-bar" style="background: var(--lavender);">
      <span class="create-label">Link {{ linkingCustomer.customer_id }} to User</span>
      <input v-model="targetUserId" class="input" type="number" placeholder="Enter User ID (e.g. 2)" />
      <button class="btn btn-dark" :disabled="saving" @click="submitLink">Link Now</button>
      <button class="btn btn-ghost" @click="linkingCustomer = null">Cancel</button>
    </div>

    <div v-if="errorMsg" class="error-banner banner-gap">{{ errorMsg }}</div>
    <div v-if="successMsg" class="success-banner banner-gap">{{ successMsg }}</div>

    <section class="card table-card">
      <div class="table-top">
        <h2>Customer records</h2>
        <div class="table-tools">
          <label class="search">
            <input v-model="search" type="search" placeholder="Search by name, email or ID" />
          </label>
          <span class="muted">{{ number(filtered.length) }} found</span>
        </div>
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
            <tr v-for="customer in filtered.slice(0, 100)" :key="customer.customer_id">
              <td class="mono strong">{{ customer.customer_id }}</td>
              <td>{{ customer.cust_name || '—' }}</td>
              <td class="muted">{{ customer.email || '—' }}</td>
              <td class="right">
                <span v-if="customer.user_id" class="pill user-pill">
                  User #{{ customer.user_id }}
                </span>
                <div v-else style="display:flex; gap:8px; justify-content:flex-end;">
                  <span class="pill unlinked-pill">Unlinked</span>
                  <button class="btn btn-sm btn-ghost" @click="startLink(customer)">Link</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<style scoped>
/* Add the same styles from before */
.customers-page { max-width: 1400px; }
.page-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 20px; margin-bottom: 20px; }
.page-head { margin-bottom: 20px; }
.page-head h1 { font-size: 32px; font-weight: 700; margin-top: 6px; }
.page-sub { color: var(--text-secondary); font-size: 14px; margin-top: 6px; }
.stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 16px; }
.stat { border-radius: 24px; padding: 24px; min-height: 150px; }
.dark-stat { background: var(--ink); color: white; }
.blue-stat { background: var(--blue); color: white; }
.light-stat { background: white; border: 1px solid var(--line); }
.stat-big { font-size: 36px; font-weight: 800; margin-top: 10px; }
.dark-stat .stat-big { color: var(--lime); }
.create-bar { display: flex; gap: 12px; background: var(--lime); border-radius: 20px; padding: 16px; margin-bottom: 16px; align-items: center; }
.create-bar .input { flex: 1; border-color: transparent; }
.table-card { padding: 0; }
.table-top { padding: 24px; display: flex; justify-content: space-between; }
.table { width: 100%; border-collapse: collapse; }
.table th, .table td { padding: 16px 24px; border-bottom: 1px solid var(--line); text-align: left; }
.right { text-align: right; }
.user-pill { background: var(--lavender); color: #4b3fa8; padding: 4px 10px; border-radius: 99px; }
.unlinked-pill { background: #f1f3f8; color: #6b7280; padding: 4px 10px; border-radius: 99px; }
.search input { border: 1px solid var(--line); border-radius: 99px; padding: 8px 16px; }
</style>