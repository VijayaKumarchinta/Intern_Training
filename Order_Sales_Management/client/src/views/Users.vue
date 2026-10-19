<script setup>
import { computed, onMounted, ref } from 'vue'
import api from '@/services/api'
import { number, percent } from '@/utils/format'

const users = ref([])
const loading = ref(true)
const errorMsg = ref('')

const admins = computed(() => users.value.filter((user) => user.role === 'admin'))
const unverified = computed(() => users.value.filter((user) => !user.is_verified))
const customers = computed(() => users.value.filter((user) => user.role === 'customer'))

const avatarTone = (role) => (role === 'admin' ? 'tone-dark' : 'tone-lavender')

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
  <div class="users-page">
    <header class="page-head">
      <div>
        <p class="eyebrow">OrderSync · Admin</p>
        <h1>Users</h1>
        <p class="page-sub">Everyone who has registered for the app.</p>
      </div>
      <div class="avatar">A</div>
    </header>

    <section class="stats">
      <div class="stat dark-stat">
        <p class="stat-label">Registered users</p>
        <p class="stat-big">{{ number(users.length) }}</p>
        <p class="stat-foot">100% of accounts</p>
      </div>
      <div class="stat blue-stat">
        <p class="stat-label">Admins</p>
        <p class="stat-big">{{ percent(admins.length, users.length).toFixed(1) }}%</p>
        <p class="stat-foot">
          {{ admins.length }} admin · {{ customers.length }} customers
        </p>
      </div>
      <div class="stat orange-stat">
        <p class="stat-label dark">Unverified</p>
        <p class="stat-big dark">{{ percent(unverified.length, users.length).toFixed(1) }}%</p>
        <p class="stat-foot dark">
          {{ unverified.length }} waiting for an email code
        </p>
      </div>
    </section>

    <div v-if="errorMsg" class="error-banner banner-gap">{{ errorMsg }}</div>

    <section class="card table-card">
      <div class="table-top">
        <h2>Registered users <span class="count-pill">{{ users.length }}</span></h2>
      </div>

      <div v-if="loading" class="spinner-state">Loading users…</div>

      <div v-else class="scroll-x">
        <table class="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Full name</th>
              <th>Email</th>
              <th>Role</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in users" :key="user.id">
              <td class="mono">{{ user.id }}</td>
              <td>
                <span class="user-cell">
                  <span class="user-avatar" :class="avatarTone(user.role)">
                    {{ (user.full_name || user.email).charAt(0).toUpperCase() }}
                  </span>
                  {{ user.full_name || '—' }}
                </span>
              </td>
              <td class="muted">{{ user.email }}</td>
              <td>
                <span
                  class="role-pill"
                  :class="user.role === 'admin' ? 'role-admin' : 'role-customer'"
                >
                  {{ user.role }}
                </span>
              </td>
              <td>
                <span class="status-text" :class="user.is_verified ? 'verified' : 'unverified'">
                  <i></i>{{ user.is_verified ? 'Verified' : 'Unverified' }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <p v-if="!loading && !users.length" class="empty-state">No registered users yet.</p>
    </section>
  </div>
</template>

<style scoped>
.users-page {
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
.orange-stat {
  background: var(--orange);
  color: var(--ink);
}
.stat-label {
  font-size: 13.5px;
  color: rgba(255, 255, 255, 0.85);
}
.stat-label.dark {
  color: var(--ink);
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
.stat-big.dark {
  color: var(--ink);
}
.stat-foot {
  font-size: 12.5px;
  color: rgba(255, 255, 255, 0.8);
}
.stat-foot.dark {
  color: #4a2a17;
}
.table-card {
  padding: 0;
  overflow: hidden;
}
.table-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 22px 24px;
}
h2 {
  font-size: 19px;
  font-weight: 700;
  letter-spacing: -0.03em;
  display: flex;
  align-items: center;
  gap: 10px;
}
.count-pill {
  background: #f1f3f8;
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
}
.user-cell {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-weight: 500;
}
.user-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  flex: none;
}
.tone-dark {
  background: var(--ink);
  color: var(--lime);
}
.tone-lavender {
  background: var(--lavender);
  color: #4b3fa8;
}
.role-pill {
  border-radius: 999px;
  padding: 5px 12px;
  font-size: 12px;
  font-weight: 600;
}
.role-admin {
  background: var(--lavender);
  color: #4b3fa8;
}
.role-customer {
  background: #f1f3f8;
  color: #4b5563;
}
.status-text {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-size: 12.5px;
  font-weight: 500;
}
.status-text i {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.verified {
  color: #4b5563;
}
.verified i {
  background: #17a34a;
}
.unverified {
  color: #8a5a00;
}
.unverified i {
  background: #f4c542;
}
.banner-gap {
  margin-bottom: 16px;
}
@media (max-width: 860px) {
  .stats {
    grid-template-columns: 1fr;
  }
}
</style>
