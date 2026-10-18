<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'

const router = useRouter()
const step = ref(1)
const errorMsg = ref('')
const successMsg = ref('')

const form = ref({
  email: '', password: '', full_name: '', customer_id: ''
})
const code = ref('')

const handleRegister = async () => {
  try {
    errorMsg.value = ''
    await api.post('/auth/register', form.value)
    step.value = 2
    successMsg.value = 'Code sent! Check server/dev_emails.log'
  } catch (err) {
    errorMsg.value = err.response?.data?.error || 'Registration failed'
  }
}

const handleVerify = async () => {
  try {
    errorMsg.value = ''
    await api.post('/auth/verify', { 
      email: form.value.email, 
      code: code.value,
      customer_id: form.value.customer_id 
    })
    router.push('/login')
  } catch (err) {
    errorMsg.value = err.response?.data?.error || 'Verification failed'
  }
}

const handleResend = async () => {
  try {
    successMsg.value = 'New code sent!'
    await api.post('/auth/resend-verification', { email: form.value.email })
  } catch (err) {
    errorMsg.value = 'Failed to resend code'
  }
}
</script>

<template>
  <div class="auth-wrapper">
    <div class="card login-card">
      <h1>Create Account</h1>
      <p class="subtitle">Join the platform to manage your orders</p>
      
      <div v-if="errorMsg" class="error-banner">{{ errorMsg }}</div>
      <div v-if="successMsg" class="success-banner">{{ successMsg }}</div>

      <!-- Step 1: Details -->
      <form v-if="step === 1" @submit.prevent="handleRegister">
        <label>Full Name</label>
        <input v-model="form.full_name" required placeholder="John Doe" />
        
        <label>Email</label>
        <input v-model="form.email" type="email" required placeholder="customer@test.local" />
        
        <label>Password</label>
        <input v-model="form.password" type="password" required placeholder="Min 8 characters" />
        
        <label>Customer ID (from your invoice)</label>
        <input v-model="form.customer_id" required placeholder="C0001" />
        
        <button type="submit" class="btn-primary" style="width: 100%; margin-top: 8px;">Register</button>
      </form>

      <!-- Step 2: OTP -->
      <form v-else @submit.prevent="handleVerify">
        <label>Enter 6-digit OTP</label>
        <input v-model="code" required maxlength="6" placeholder="123456" style="text-align: center; font-size: 24px; letter-spacing: 8px;" />
        <button type="submit" class="btn-primary" style="width: 100%; margin-top: 8px;">Verify Email</button>
        <button type="button" @click="handleResend" style="width: 100%; margin-top: 8px; background: transparent; color: var(--accent-blue);">Resend Code</button>
      </form>

      <p class="back-link"><router-link to="/login">← Back to Login</router-link></p>
    </div>
  </div>
</template>

<style scoped>
.auth-wrapper { min-height: 100vh; display: flex; align-items: center; justify-content: center; background: var(--bg-app); }
.login-card { width: 100%; max-width: 400px; }
h1 { font-size: 24px; margin-bottom: 4px; }
.subtitle { color: var(--text-secondary); font-size: 14px; margin-bottom: 24px; }
.error-banner { background: #FEE2E2; color: #991B1B; padding: 12px; border-radius: 8px; margin-bottom: 16px; font-size: 14px; }
.success-banner { background: #D1FAE5; color: #065F46; padding: 12px; border-radius: 8px; margin-bottom: 16px; font-size: 14px; }
.back-link { text-align: center; margin-top: 16px; font-size: 13px; }
.back-link a { color: var(--text-secondary); text-decoration: none; }
</style>