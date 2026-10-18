<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'

const customers = ref([])
const loading = ref(true)
const showCreate = ref(false)
const errorMsg = ref('')
const newCustomer = ref({ customer_id: '', cust_name: '', email: '' })

const fetchCustomers = async () => {
  try {
    const res = await api.get('/customers')
    customers.value = res.data.customers
  } catch (err) {
    errorMsg.value = 'Failed to load'
  } finally {
    loading.value = false
  }
}

const createCustomer = async () => {
  try {
    errorMsg.value = ''
    await api.post('/customers', newCustomer.value)
    showCreate.value = false
    newCustomer.value = { customer_id: '', cust_name: '', email: '' }
    fetchCustomers()
  } catch (err) {
    errorMsg.value = err.response?.data?.error || 'Failed to create'
  }
}

onMounted(fetchCustomers)
</script>

<template>
  <div class="card">
    <div class="header">
      <div>
        <h2>Customers</h2>
        <p class="sub">Manage customer records. {{ customers.length }} total.</p>
      </div>
      <button @click="showCreate = !showCreate" class="btn-primary">+ New Customer</button>
    </div>

    <div v-if="errorMsg" class="error-banner">{{ errorMsg }}</div>

    <div v-if="showCreate" class="create-form">
      <input v-model="newCustomer.customer_id" placeholder="Customer ID (e.g. C1234)" />
      <input v-model="newCustomer.cust_name" placeholder="Full Name" />
      <input v-model="newCustomer.email" type="email" placeholder="Email (optional)" />
      <div class="actions">
        <button @click="createCustomer" class="btn-primary">Save</button>
        <button @click="showCreate = false" class="btn-secondary">Cancel</button>
      </div>
    </div>

    <div v-if="loading" class="loading">Loading...</div>
    <table v-else class="data-table">
      <thead>
        <tr>
          <th>Customer ID</th>
          <th>Name</th>
          <th>Email</th>
          <th>Linked User</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="c in customers.slice(0, 50)" :key="c.customer_id">
          <td class="mono">{{ c.customer_id }}</td>
          <td>{{ c.cust_name || '—' }}</td>
          <td>{{ c.email || '—' }}</td>
          <td>{{ c.user_id ? `User #${c.user_id}` : 'Unlinked' }}</td>
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
.actions { display: flex; gap: 12px; margin-top: 8px; }
.error-banner { background: #FEE2E2; color: #991B1B; padding: 12px; border-radius: 8px; margin-bottom: 16px; }
.loading { padding: 24px; text-align: center; color: var(--text-secondary); }
</style>