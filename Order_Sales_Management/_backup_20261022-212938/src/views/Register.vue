<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import AuthShell from '@/components/AuthShell.vue'
import Icon from '@/components/Icon.vue'

const router = useRouter()
const step = ref(1)
const errorMsg = ref('')
const successMsg = ref('')
const submitting = ref(false)
const resending = ref(false)

const form = ref({ email: '', password: '', full_name: '', customer_id: '' })
const code = ref('')

const steps = ['Details', 'Verify email']
const activeStep = computed(() => step.value)

const handleRegister = async () => {
  try {
    errorMsg.value = ''
    submitting.value = true
    await api.post('/auth/register', form.value)
    step.value = 2
    successMsg.value = 'Code sent. In development, read it from server/logs/dev_emails.log.'
  } catch (err) {
    errorMsg.value = err.response?.data?.error || 'Registration failed'
  } finally {
    submitting.value = false
  }
}

const handleVerify = async () => {
  try {
    errorMsg.value = ''
    submitting.value = true
    await api.post('/auth/verify', {
      email: form.value.email,
      code: code.value.trim(),
      customer_id: form.value.customer_id,
    })
    router.push('/login')
  } catch (err) {
    errorMsg.value = err.response?.data?.error || 'Verification failed'
  } finally {
    submitting.value = false
  }
}

const handleResend = async () => {
  if (resending.value) return
  try {
    errorMsg.value = ''
    resending.value = true
    await api.post('/auth/resend-verification', { email: form.value.email })
    successMsg.value = 'A new 6-digit code has been sent.'
  } catch (err) {
    errorMsg.value = err.response?.data?.error || 'Failed to resend code'
  } finally {
    resending.value = false
  }
}

const backToDetails = () => {
  step.value = 1
  successMsg.value = ''
  errorMsg.value = ''
}
</script>

<template>
  <AuthShell
    heading="Join the"
    accent="platform."
    :subtitle="
      step === 1
        ? 'Use the customer ID from your invoice and we will link your orders to your account.'
        : 'We sent a 6-digit code to your email. It expires in 2 minutes.'
    "
    :steps="steps"
    :active-step="activeStep"
  >
    <template v-if="step === 1">
      <h2 class="auth-title">Create account</h2>
      <p class="auth-sub">Join the platform to manage your orders.</p>

      <div v-if="errorMsg" class="error-banner" role="alert">{{ errorMsg }}</div>

      <form class="auth-form" @submit.prevent="handleRegister">
        <div class="field">
          <label for="reg-name">Full name</label>
          <input id="reg-name" v-model="form.full_name" class="input" required placeholder="John Doe" />
        </div>

        <div class="field">
          <label for="reg-email">Email</label>
          <input id="reg-email" v-model="form.email" class="input" type="email" required placeholder="customer@test.local" />
        </div>

        <div class="field">
          <label for="reg-password">Password</label>
          <input
            id="reg-password"
            v-model="form.password"
            class="input"
            type="password"
            minlength="8"
            required
            placeholder="Min 8 characters"
          />
        </div>

        <div class="field">
          <label for="reg-customer">Customer ID <span class="muted">(from your invoice)</span></label>
          <input id="reg-customer" v-model="form.customer_id" class="input" required placeholder="C0001" />
        </div>

        <button type="submit" class="btn btn-primary submit" :disabled="submitting">
          {{ submitting ? 'Creating account…' : 'Register' }}
        </button>
      </form>
    </template>

    <template v-else>
      <div class="step-head">
        <span class="mail-badge"><Icon name="mail" :size="20" /></span>
        <h2 class="auth-title">Verify email</h2>
        <p class="auth-sub">
          Enter the 6-digit code sent to <strong>{{ form.email }}</strong>.
        </p>
      </div>

      <div v-if="errorMsg" class="error-banner" role="alert">{{ errorMsg }}</div>
      <div v-if="successMsg" class="success-banner">{{ successMsg }}</div>

      <form class="auth-form" @submit.prevent="handleVerify">
        <div class="field">
          <label for="otp">6-digit code</label>
          <input
            id="otp"
            v-model="code"
            class="input otp-input"
            inputmode="numeric"
            autocomplete="one-time-code"
            :maxlength="6"
            pattern="\d{6}"
            required
            placeholder="123456"
          />
        </div>

        <button type="submit" class="btn btn-primary submit" :disabled="submitting">
          {{ submitting ? 'Verifying…' : 'Verify email' }}
        </button>
        <button type="button" class="btn btn-ghost" :disabled="resending" @click="handleResend">
          {{ resending ? 'Sending…' : 'Resend code' }}
        </button>
      </form>

      <p class="switch-step">
        Wrong email?
        <button type="button" @click="backToDetails">Edit details</button>
      </p>
    </template>

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
  line-height: 1.5;
  margin-bottom: 26px;
}
.auth-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.submit {
  width: 100%;
  height: 52px;
  margin-top: 4px;
  font-size: 15px;
}
.auth-card > :deep(.error-banner),
.auth-card > :deep(.success-banner) {
  margin-bottom: 18px;
}
.step-head {
  margin-bottom: 8px;
}
.mail-badge {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  background: var(--lime-soft);
  color: var(--ink);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}
.otp-input {
  text-align: center;
  font-size: 26px;
  font-weight: 700;
  letter-spacing: 0.42em;
  height: 62px;
  padding-left: 0.42em;
}
.switch-step {
  margin-top: 16px;
  text-align: center;
  font-size: 13px;
  color: var(--text-secondary);
}
.switch-step button {
  color: var(--blue);
  font-weight: 600;
  font-size: 13px;
}
.switch-step button:hover {
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
