<script setup>
import Icon from '@/components/Icon.vue'

defineProps({
  heading: { type: String, required: true },
  accent: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  steps: { type: Array, default: () => [] },
  activeStep: { type: Number, default: 0 },
})
</script>

<template>
  <div class="auth-shell">
    <section class="brand-panel">
      <div class="brand">
        <span class="brand-mark"><Icon name="layers" :size="24" :stroke-width="2.2" /></span>
        <span class="brand-name">OrderSync</span>
      </div>

      <div class="brand-copy">
        <h1>
          {{ heading }}<br v-if="accent" />
          <span v-if="accent" class="accent">{{ accent }}</span>
        </h1>
        <p v-if="subtitle">{{ subtitle }}</p>
      </div>

      <div v-if="steps.length" class="steps">
        <template v-for="(step, index) in steps" :key="step">
          <div class="step" :class="{ done: index + 1 < activeStep, active: index + 1 === activeStep }">
            <span class="step-dot">{{ index + 1 }}</span>
            <span class="step-label">{{ step }}</span>
          </div>
          <span v-if="index < steps.length - 1" class="step-line"></span>
        </template>
      </div>

      <div v-else class="chips">
        <span class="chip">Admin</span>
        <span class="chip">Customer</span>
        <span class="chip chip-accent">Email verified</span>
      </div>
    </section>

    <section class="form-panel">
      <div class="auth-card">
        <slot />
      </div>
    </section>
  </div>
</template>

<style scoped>
.auth-shell {
  min-height: 100vh;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 0.96fr);
  gap: 24px;
  padding: 24px;
  background: var(--bg-app);
}
.brand-panel {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: calc(100vh - 48px);
  padding: clamp(32px, 4vw, 60px);
  border-radius: 32px;
  background: var(--ink);
  color: #fff;
  overflow: hidden;
}
.brand-panel::after {
  content: '';
  position: absolute;
  width: 520px;
  height: 520px;
  right: -220px;
  bottom: -260px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(199, 245, 60, 0.1), transparent 65%);
  pointer-events: none;
}
.brand {
  display: flex;
  align-items: center;
  gap: 14px;
  position: relative;
  z-index: 1;
}
.brand-mark {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  background: var(--lime);
  color: var(--ink);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.brand-name {
  font-family: 'Inter Tight', sans-serif;
  font-weight: 700;
  font-size: 23px;
  letter-spacing: -0.04em;
}
.brand-copy {
  position: relative;
  z-index: 1;
  max-width: 660px;
  padding: 48px 0;
}
.brand-copy h1 {
  font-size: clamp(42px, 4.6vw, 72px);
  line-height: 0.98;
  font-weight: 800;
  letter-spacing: -0.05em;
}
.accent {
  color: var(--lime);
}
.brand-copy p {
  margin-top: 28px;
  max-width: 520px;
  color: #aab3c5;
  font-size: 17px;
  line-height: 1.6;
}
.chips {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  position: relative;
  z-index: 1;
}
.chip {
  padding: 10px 20px;
  border-radius: 999px;
  background: #1a2437;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
}
.chip-accent {
  background: var(--lime);
  color: var(--ink);
}
.steps {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
  position: relative;
  z-index: 1;
}
.step {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #8f99ac;
  font-size: 14px;
  font-weight: 600;
}
.step-dot {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #1a2437;
  color: #8f99ac;
  font-size: 13px;
}
.step.active .step-dot,
.step.done .step-dot {
  background: var(--lime);
  color: var(--ink);
}
.step.active .step-label,
.step.done .step-label {
  color: #fff;
}
.step-line {
  width: 56px;
  height: 1px;
  background: #2a3549;
}
.form-panel {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}
.auth-card {
  width: 100%;
  max-width: 560px;
  padding: clamp(30px, 3.2vw, 52px);
  background: #fff;
  border-radius: 32px;
  box-shadow: var(--shadow-float);
}
@media (max-width: 980px) {
  .auth-shell {
    grid-template-columns: 1fr;
    padding: 16px;
    gap: 16px;
  }
  .brand-panel {
    min-height: auto;
    padding: 32px;
    gap: 32px;
  }
  .brand-copy {
    padding: 0;
  }
  .brand-copy h1 {
    font-size: clamp(34px, 7vw, 48px);
  }
  .brand-copy p {
    margin-top: 18px;
    font-size: 15px;
  }
  .form-panel {
    padding: 8px 0 24px;
  }
  .auth-card {
    padding: 32px 24px;
  }
  .steps,
  .chips {
    display: none;
  }
}
</style>
