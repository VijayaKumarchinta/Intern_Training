<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/services/api'
import AuthShell from '@/components/AuthShell.vue'

const route = useRoute()
const router = useRouter()
const token = route.query.token || ''
const password = ref('')
const errorMsg = ref('')
const submitting = ref(false)

const steps = ['Request link', 'Set new password']

const handleSubmit = async () => {
  try {
    errorMsg.value = ''
    submitting.value = true
    await api.post('/auth/reset-password', { token, new_password: password.value })
    router.push({ path: '/login', query: { reset: 'success' } })
  } catch (err) {
    errorMsg.value = err.response?.data?.error || 'Failed to reset password'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <AuthShell
    heading="A fresh start,"
    accent="new password."
    subtitle="Choose a password you have not used here before. Your old password stops working immediately."
    :steps="steps"
    :active-step="2"
  >
    <h2 class="auth-title">Reset password</h2>
    <p class="auth-sub">Enter your new password below.</p>

    <div v-if="!token" class="error-banner" role="alert">
      Missing or invalid token. Request a new reset link to continue.
    </div>
    <div v-if="errorMsg" class="error-banner" role="alert">{{ errorMsg }}</div>

    <form v-if="token" class="auth-form" @submit.prevent="handleSubmit">
      <div class="field">
        <label for="new-password">New password</label>
        <input
          id="new-password"
          v-model="password"
          class="input"
          type="password"
          autocomplete="new-password"
          minlength="8"
          required
          placeholder="••••••••"
        />
        <span class="hint">At least 8 characters.</span>
      </div>
      <button type="submit" class="btn btn-primary submit" :disabled="submitting">
        {{ submitting ? 'Updating…' : 'Update password' }}
      </button>
    </form>

    <p v-if="!token" class="back-link"><router-link to="/forgot-password">Request a new link</router-link></p>
    <p v-else class="back-link"><router-link to="/login">← Back to login</router-link></p>
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
.submit {
  width: 100%;
  height: 52px;
  font-size: 15px;
}
.auth-card > :deep(.error-banner) {
  margin-bottom: 18px;
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
