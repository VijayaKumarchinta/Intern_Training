<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'

const users = ref([])
const loading = ref(true)
const errorMsg = ref('')

onMounted(async () => {
  try {
    const res = await api.get('/users')
    users.value = res.data.users
  } catch (err) {
    errorMsg.value = 'Failed to load users.'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="card" style="padding: 0; overflow: hidden;">
    <div class="table-header">
      <h2>Registered Users <span class="count">{{ users.length }}</span></h2>
    </div>

    <div v-if="errorMsg" class="error-banner" style="margin: 24px;">{{ errorMsg }}</div>
    <div v-if="loading" style="padding: 40px; text-align: center; color: var(--text-secondary);">Loading users...</div>

    <table v-else-if="users.length > 0" class="data-table">
      <thead>
        <tr>
          <th>ID</th>
          <th>Full Name</th>
          <th>Email</th>
          <th>Role</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="user in users" :key="user.id">
          <td class="mono">{{ user.id }}</td>
          <td>{{ user.full_name || '—' }}</td>
          <td>{{ user.email }}</td>
          <td>
            <span class="status-pill" :style="{ 
              background: user.role === 'admin' ? '#E0E7FF' : '#F3F4F6', 
              color: user.role === 'admin' ? '#3730A3' : '#374151' 
            }">
              {{ user.role }}
            </span>
          </td>
          <td>
            <span style="color: var(--text-secondary); font-size: 13px;">
              {{ user.is_verified ? 'Verified' : 'Unverified' }}
            </span>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.table-header { display: flex; justify-content: space-between; align-items: center; padding: 24px 32px; border-bottom: 1px solid var(--border-color); }
.table-header h2 { font-size: 18px; font-weight: 600; display: flex; align-items: center; gap: 12px; }
.count { background: var(--bg-app); padding: 4px 10px; border-radius: 99px; font-size: 12px; color: var(--text-secondary); }
</style>