<script setup>
import Icon from '@/components/Icon.vue'
</script>

<template>
  <div class="auth-layout">
    <div class="auth-card">
      <router-link to="/" class="brand">
        <span class="brand-mark"><Icon name="layers" :size="20" :stroke-width="2.5" /></span>
        <span class="brand-name">OrderSync</span>
      </router-link>
      <slot />
    </div>
  </div>
</template>

<style scoped>
.auth-layout {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f4f6fb;
  padding: 24px;
}
.auth-card {
  width: 100%;
  max-width: 420px;
  background: #fff;
  border-radius: 24px;
  padding: 40px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.05);
}
.brand {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  text-decoration: none;
  margin-bottom: 32px;
}
.brand-mark {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  background: var(--ink);
  color: var(--lime);
  display: flex;
  align-items: center;
  justify-content: center;
}
.brand-name {
  font-family: 'Inter Tight', sans-serif;
  font-size: 24px;
  font-weight: 800;
  color: var(--ink);
}
</style>