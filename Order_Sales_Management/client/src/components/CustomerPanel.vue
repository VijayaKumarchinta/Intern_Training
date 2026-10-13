<script setup>
import { ref, onMounted } from 'vue'
import { useApi } from '../composables/useApi'

const { get, post, loading, error } = useApi()

const customers = ref([])
const totalCount = ref(0)
const searchQuery = ref('')

const newCustomer = ref({
  customer_id: '',
  name: '',
  email: '',
  phone: '',
  address: ''
})

const showForm = ref(false)
const formError = ref('')
const formSuccess = ref('')

async function loadCustomers() {
  try {
    const response = await get('/customers')
    customers.value = response.data.customers || []
    totalCount.value = response.data.total || 0
  } catch (err) {
    console.error('Failed to load customers:', err)
  }
}

async function createCustomer() {
  formError.value = ''
  formSuccess.value = ''

  if (!newCustomer.value.customer_id || !newCustomer.value.name || !newCustomer.value.email) {
    formError.value = 'Customer ID, Name, and Email are required'
    return
  }

  try {
    const response = await post('/customers', {
      customer_id: newCustomer.value.customer_id,
      name: newCustomer.value.name,
      email: newCustomer.value.email,
      phone: newCustomer.value.phone || null,
      address: newCustomer.value.address || null
    })
    formSuccess.value = `Customer ${response.data.customer_id} created successfully!`
    newCustomer.value = { customer_id: '', name: '', email: '', phone: '', address: '' }
    showForm.value = false
    await loadCustomers()
  } catch (err) {
    formError.value = err.message
  }
}

function resetForm() {
  newCustomer.value = { customer_id: '', name: '', email: '', phone: '', address: '' }
  formError.value = ''
  formSuccess.value = ''
}

onMounted(() => {
  loadCustomers()
})
</script>

<template>
  <div class="panel">
    <div class="panel-header">
      <h2>👥 Customers</h2>
      <span class="count">Total: {{ totalCount }}</span>
    </div>

    <div class="actions">
      <button @click="showForm = !showForm" :disabled="loading">
        {{ showForm ? 'Cancel' : '+' }} Add Customer
      </button>
      <button @click="loadCustomers" class="secondary" :disabled="loading">
        Refresh
      </button>
    </div>

    <div v-if="showForm" class="form-card">
      <h3>New Customer</h3>
      <div class="form-group">
        <label>Customer ID *</label>
        <input v-model="newCustomer.customer_id" placeholder="CUST-001" />
      </div>
      <div class="form-group">
        <label>Name *</label>
        <input v-model="newCustomer.name" placeholder="John Doe" />
      </div>
      <div class="form-group">
        <label>Email *</label>
        <input v-model="newCustomer.email" type="email" placeholder="john@example.com" />
      </div>
      <div class="form-group">
        <label>Phone</label>
        <input v-model="newCustomer.phone" placeholder="+1234567890" />
      </div>
      <div class="form-group">
        <label>Address</label>
        <textarea v-model="newCustomer.address" rows="2" placeholder="123 Main St..."></textarea>
      </div>
      <div class="form-actions">
        <button @click="createCustomer" :disabled="loading">Create</button>
        <button @click="resetForm" class="secondary">Clear</button>
      </div>
      <p v-if="formError" class="error">{{ formError }}</p>
      <p v-if="formSuccess" class="success">{{ formSuccess }}</p>
    </div>

    <div v-if="error" class="error">{{ error }}</div>

    <div v-if="customers.length > 0" class="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>Customer ID</th>
            <th>Name</th>
            <th>Email</th>
            <th>Phone</th>
            <th>Created</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="cust in customers" :key="cust.id">
            <td><strong>{{ cust.customer_id }}</strong></td>
            <td>{{ cust.name }}</td>
            <td>{{ cust.email }}</td>
            <td>{{ cust.phone || '-' }}</td>
            <td>{{ cust.created_at?.split('T')[0] }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <p v-else class="empty-state">
      {{ customers.length === 0 && !showForm ? 'No customers found. Add one above.' : '' }}
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
