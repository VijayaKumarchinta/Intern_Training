<script setup>
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const email = ref('')
const password = ref('')
const errorMsg = ref('')
const auth = useAuthStore()
const router = useRouter()

const handleLogin = async () => {
  try {
    errorMsg.value = ''
    await auth.login(email.value, password.value)
    router.push('/app/orders')
  } catch (err) {
    errorMsg.value = err.response?.data?.error || 'Login failed'
  }
}
</script>

<template>
  <div class="auth-wrapper">
    <div class="card login-card">
      <h1>Welcome back</h1>
      <p class="subtitle">Enter your credentials to access the dashboard</p>
      
      <div v-if="errorMsg" class="error-banner">{{ errorMsg }}</div>

      <form @submit.prevent="handleLogin">
        <label>Email</label>
        <input v-model="email" type="email" required placeholder="admin@test.local" />
        
        <label>Password</label>
        <input v-model="password" type="password" required placeholder="Password" />
        
        <button type="submit" class="btn-primary" style="width: 100%; margin-top: 8px;">Login</button>
      </form>
      
      <div class="links">
        <router-link to="/forgot-password">Forgot Password?</router-link>
        <router-link to="/register">Create an account</router-link>
      </div>
      <p class="back-link"><router-link to="/">← Back to Home</router-link></p>
    </div>
  </div>
</template>

<style scoped>
.auth-wrapper { min-height: 100vh; display: flex; align-items: center; justify-content: center; background: var(--bg-app); }
.login-card { width: 100%; max-width: 420px; padding: 48px; border-radius: 24px; }
h1 { font-size: 28px; font-weight: 700; margin-bottom: 8px; text-align: center; }
.subtitle { color: var(--text-secondary); font-size: 14px; margin-bottom: 32px; text-align: center; }
.error-banner { background: #FEE2E2; color: #991B1B; padding: 12px; border-radius: 8px; margin-bottom: 16px; font-size: 14px; }
.links { display: flex; justify-content: space-between; margin-top: 16px; font-size: 13px; }
.links a { color: var(--accent-blue); text-decoration: none; }
.back-link { text-align: center; margin-top: 16px; font-size: 13px; }
.back-link a { color: var(--text-secondary); text-decoration: none; }
</style>