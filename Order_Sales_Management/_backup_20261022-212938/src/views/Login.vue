<script setup>
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRoute, useRouter } from 'vue-router'
import AuthShell from '@/components/AuthShell.vue'

const email = ref('')
const password = ref('')
const errorMsg = ref('')
const submitting = ref(false)
const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const handleLogin = async () => {
  try {
    errorMsg.value = ''
    submitting.value = true
    await auth.login(email.value, password.value)
    router.push(auth.isAdmin ? '/app/reports' : '/app/my-orders')
  } catch (err) {
    errorMsg.value = err.response?.data?.error || 'Login failed'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <AuthShell>
    <h2 class="auth-title">Welcome back</h2>
    <p class="auth-sub">Enter your credentials to access the dashboard.</p>

    <div v-if="route.query.reset === 'success'" class="success-banner" role="status">
      Password updated. Sign in with your new password.
    </div>
    <div v-if="errorMsg" class="error-banner" role="alert">{{ errorMsg }}</div>

    <form class="auth-form" @submit.prevent="handleLogin">
      <div class="field">
        <label for="login-email">Email</label>
        <input
          id="login-email"
          v-model="email"
          class="input"
          type="email"
          autocomplete="email"
          required
          placeholder="admin@test.local"
        />
      </div>

      <div class="field">
        <label for="login-password">Password</label>
        <input
          id="login-password"
          v-model="password"
          class="input"
          type="password"
          autocomplete="current-password"
          required
          placeholder="Password"
        />
      </div>

      <button type="submit" class="btn btn-primary submit" :disabled="submitting">
        {{ submitting ? 'Signing in…' : 'Log in' }}
      </button>
    </form>

    <div class="auth-links">
      <router-link to="/forgot-password">Forgot password?</router-link>
      <router-link to="/register">Create an account</router-link>
    </div>
    <p class="back-link"><router-link to="/">← Back to home</router-link></p>
  </AuthShell>
</template>

<style scoped>
.auth-title {
  font-size: 32px;
  font-weight: 700;
  letter-spacing: -0.04em;
  margin-bottom: 8px;
}
.auth-sub {
  color: var(--text-secondary);
  font-size: 14px;
  margin-bottom: 26px;
}
.auth-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.success-banner {
  margin-bottom: 18px;
}
.error-banner {
  margin-bottom: 18px;
}
.submit {
  width: 100%;
  height: 52px;
  margin-top: 4px;
  font-size: 15px;
}
.auth-links {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-top: 22px;
  font-size: 13px;
  font-weight: 600;
}
.auth-links a {
  color: var(--blue);
  text-decoration: none;
}
.auth-links a:hover {
  text-decoration: underline;
}
.back-link {
  text-align: center;
  margin-top: 22px;
  font-size: 13px;
}
.back-link a {
  color: var(--text-secondary);
  text-decoration: none;
}
.back-link a:hover {
  color: var(--text-primary);
}
</style>
