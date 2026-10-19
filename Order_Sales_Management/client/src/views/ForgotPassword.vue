<script setup>
import { ref } from 'vue'
import api from '@/services/api'
import AuthShell from '@/components/AuthShell.vue'

const email = ref('')
const message = ref('')
const errorMsg = ref('')
const submitting = ref(false)

const steps = ['Request link', 'Set new password']

const handleSubmit = async () => {
  try {
    message.value = ''
    errorMsg.value = ''
    submitting.value = true
    await api.post('/auth/forgot-password', { email: email.value })
    message.value =
      'If the email exists, a reset link was sent. Check server/dev_emails.log in development.'
  } catch (err) {
    errorMsg.value = err.response?.data?.error || 'Something went wrong.'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <AuthShell
    heading="Locked out?"
    accent="It happens."
    subtitle="We will send a reset link to your email. The link works once, and expires after an hour."
    :steps="steps"
    :active-step="1"
  >
    <h2 class="auth-title">Forgot password</h2>
    <p class="auth-sub">Enter your email to receive a reset link.</p>

    <div v-if="errorMsg" class="error-banner" role="alert">{{ errorMsg }}</div>
    <div v-if="message" class="success-banner" role="status">{{ message }}</div>

    <form v-if="!message" class="auth-form" @submit.prevent="handleSubmit">
      <div class="field">
        <label for="forgot-email">Email</label>
        <input
          id="forgot-email"
          v-model="email"
          class="input"
          type="email"
          autocomplete="email"
          required
          placeholder="admin@test.local"
        />
      </div>
      <button type="submit" class="btn btn-primary submit" :disabled="submitting">
        {{ submitting ? 'Sending…' : 'Send reset link' }}
      </button>
    </form>

    <p v-else class="sent-note">
      Next step: open the link from your email to choose a new password.
    </p>

    <p class="back-link"><router-link to="/login">← Back to login</router-link></p>
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
.auth-card > :deep(.error-banner),
.auth-card > :deep(.success-banner) {
  margin-bottom: 18px;
}
.sent-note {
  font-size: 13.5px;
  color: var(--text-secondary);
  background: #f7f8fb;
  border-radius: 14px;
  padding: 16px;
  line-height: 1.5;
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
