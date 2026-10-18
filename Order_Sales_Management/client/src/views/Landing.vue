<script setup>
import { useRouter } from 'vue-router'
const router = useRouter()
</script>

<template>
  <div class="landing-page">
    <nav class="navbar">
      <div class="logo">OrderSync</div>
      <div style="display: flex; gap: 12px;">
        <button @click="router.push('/login')" style="background: transparent; color: var(--text-primary); border: 1px solid var(--border-color);">Sign In</button>
        <button class="btn-primary" @click="router.push('/register')">Get Started</button>
      </div>
    </nav>

    <main class="hero">
      <h1>Manage Orders.<br>Track Sales. Detect Anomalies.</h1>
      <p>A robust backend integration for high-volume retail. Designed for admins to securely manage state machines, prices, and analytics.</p>
      <button class="btn-primary hero-btn" @click="router.push('/login')">Go to App</button>
    </main>

    <section class="features">
      <div class="feature-card card">
        <h3>Order Workflow</h3>
        <p>Strict transitions from Pending to Delivered. No skipping states.</p>
      </div>
      <div class="feature-card card">
        <h3>Server Pricing</h3>
        <p>Price is calculated on the server. Client overrides are rejected.</p>
      </div>
      <div class="feature-card card">
        <h3>Duplicate Alerts</h3>
        <p>Automatically surfaces anomalies based on customer, product, and date.</p>
      </div>
    </section>
  </div>
</template>

<style scoped>
.landing-page { min-height: 100vh; background: white; padding: 0 5%; }
.navbar { display: flex; justify-content: space-between; align-items: center; padding: 24px 0; }
.logo { font-size: 24px; font-weight: 800; letter-spacing: -1px; }
.hero { text-align: center; padding: 100px 0 60px; max-width: 800px; margin: 0 auto; }
.hero h1 { font-size: 56px; line-height: 1.1; font-weight: 800; letter-spacing: -2px; margin-bottom: 24px; }
.hero p { font-size: 18px; color: var(--text-secondary); max-width: 600px; margin: 0 auto 40px; line-height: 1.6; }
.hero-btn { font-size: 16px; padding: 14px 32px; }
.features { display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; padding-bottom: 100px; }
.feature-card h3 { margin-bottom: 12px; font-size: 18px; }
.feature-card p { color: var(--text-secondary); line-height: 1.5; font-size: 14px; }
</style>