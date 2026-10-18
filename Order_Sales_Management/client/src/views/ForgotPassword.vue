<script setup>
import { ref } from 'vue'
import api from '@/services/api'

const email = ref('')
const message = ref('')
const errorMsg = ref('')

const handleSubmit = async () => {
  try {
    message.value = ''
    errorMsg.value = ''
    await api.post('/auth/forgot-password', { email: email.value })
    message.value = 'If the email exists, a reset link was sent. (Check server/dev_emails.log)'
  } catch (err) {
    errorMsg.value = 'Something went wrong.'
  }
}
</script>

<template>
  <div class="auth-wrapper">
    <div class="card login-card">
      <h1>Forgot Password</h1>
      <p class="subtitle">Enter your email to receive a reset link</p>
      
      <div v-if="errorMsg" class="error-banner">{{ errorMsg }}</div>
      <div v-if="message" class="success-banner">{{ message }}</div>

      <form @submit.prevent="handleSubmit" v-if="!message">
        <label>Email</label>
        <input v-model="email" type="email" required placeholder="admin@test.local" />
        <button type="submit" class="btn-primary" style="width: 100%; margin-top: 8px;">Send Reset Link</button>
      </form>
      <p class="back-link"><router-link to="/login">← Back to Login</router-link></p>
    </div>
  </div>
</template>

<style scoped>
.auth-wrapper { min-height: 100vh; display: flex; align-items: center; justify-content: center; background: var(--bg-app); }
.login-card { width: 100%; max-width: 420px; padding: 48px; border-radius: 24px; }
h1 { font-size: 28px; font-weight: 700; margin-bottom: 8px; text-align: center; }
.subtitle { color: var(--text-secondary); font-size: 14px; margin-bottom: 32px; text-align: center; }
.error-banner { background: #FEE2E2; color: #991B1B; padding: 12px; border-radius: 8px; margin-bottom: 16px; font-size: 14px; }
.success-banner { background: #D1FAE5; color: #065F46; padding: 12px; border-radius: 8px; margin-bottom: 16px; font-size: 14px; }
.back-link { text-align: center; margin-top: 16px; font-size: 13px; }
.back-link a { color: var(--text-secondary); text-decoration: none; }
</style>