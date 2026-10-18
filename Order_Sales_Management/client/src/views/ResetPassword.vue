<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/services/api'

const route = useRoute()
const router = useRouter()
const token = route.query.token || ''
const password = ref('')
const errorMsg = ref('')

const handleSubmit = async () => {
  try {
    errorMsg.value = ''
    await api.post('/auth/reset-password', { token, new_password: password.value })
    router.push('/login')
  } catch (err) {
    errorMsg.value = err.response?.data?.error || 'Failed to reset password'
  }
}
</script>

<template>
  <div class="auth-wrapper">
    <div class="card login-card">
      <h1>Reset Password</h1>
      <p class="subtitle">Enter your new password below</p>
      
      <div v-if="!token" class="error-banner">Missing or invalid token.</div>
      <div v-if="errorMsg" class="error-banner">{{ errorMsg }}</div>

      <form @submit.prevent="handleSubmit" v-if="token">
        <label>New Password</label>
        <input v-model="password" type="password" required placeholder="••••••••" />
        <button type="submit" class="btn-primary" style="width: 100%; margin-top: 8px;">Update Password</button>
      </form>
    </div>
  </div>
</template>

<style scoped>
.auth-wrapper { min-height: 100vh; display: flex; align-items: center; justify-content: center; background: var(--bg-app); }
.login-card { width: 100%; max-width: 400px; }
h1 { font-size: 24px; margin-bottom: 4px; }
.subtitle { color: var(--text-secondary); font-size: 14px; margin-bottom: 24px; }
.error-banner { background: #FEE2E2; color: #991B1B; padding: 12px; border-radius: 8px; margin-bottom: 16px; font-size: 14px; }
</style>