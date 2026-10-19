<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Icon from '@/components/Icon.vue'

const router = useRouter()
const auth = useAuthStore()

const startPath = computed(() =>
  auth.isAuthenticated ? (auth.isAdmin ? '/app/reports' : '/app/my-orders') : '/login',
)

const bars = [40, 52, 36, 72, 60, 66, 30, 84, 58, 44, 48, 70, 38, 62]
</script>

<template>
  <div class="landing">
    <div class="landing-inner">
      <nav class="topbar">
        <router-link to="/" class="brand">
          <span class="brand-mark"><Icon name="layers" :size="22" :stroke-width="2.3" /></span>
          <span class="brand-name">OrderSync</span>
        </router-link>
        <div class="topbar-actions">
          <router-link to="/login" class="btn btn-ghost">Sign in</router-link>
          <router-link to="/register" class="btn btn-primary">Get started</router-link>
        </div>
      </nav>

      <main class="hero-grid">
        <section class="hero-card">
          <span class="hero-eyebrow">Orders · Sales · Reports</span>
          <h1>
            Manage orders.<br />
            Track sales.<br />
            <span class="accent">Detect anomalies.</span>
          </h1>
          <p class="hero-copy">
            A robust backend integration for high-volume retail. Designed for admins to
            securely manage state machines, prices, and analytics.
          </p>
          <div class="hero-actions">
            <router-link :to="startPath" class="btn btn-lime hero-btn">Go to app</router-link>
            <router-link to="/register" class="btn btn-ghost-dark hero-btn">
              Create an account
            </router-link>
          </div>
        </section>

        <div class="side-column">
          <section class="stat-card stat-blue">
            <p class="stat-label">Sales orders · live preview</p>
            <p class="stat-value">38.6%</p>
            <div class="bar-chart" aria-hidden="true">
              <span v-for="(height, index) in bars" :key="index" :style="{ height: `${height}%` }"></span>
            </div>
          </section>

          <section class="stat-card stat-orange">
            <p class="stat-title">Awaiting action</p>
            <p class="stat-value stat-value-dark">19.9%</p>
            <p class="stat-note">Pending and Received orders, one click from the queue.</p>
          </section>
        </div>
      </main>

      <section class="feature-grid">
        <article class="feature-card">
          <span class="feature-icon icon-soft-blue"><Icon name="arrowRight" :size="20" /></span>
          <h2>Order workflow</h2>
          <p>Strict transitions from Pending to Delivered. No skipping states.</p>
          <div class="chips">
            <span class="status-pill pending">Pending</span>
            <span class="status-pill shipped">Shipped</span>
            <span class="status-pill delivered">Delivered</span>
          </div>
        </article>

        <article class="feature-card feature-lime">
          <span class="feature-icon icon-dark"><Icon name="lock" :size="18" /></span>
          <h2>Server pricing</h2>
          <p>Price is calculated on the server. Client overrides are rejected.</p>
          <p class="formula mono">total = quantity × locked price</p>
        </article>

        <article class="feature-card feature-cream">
          <span class="feature-icon icon-white"><Icon name="alert" :size="20" /></span>
          <h2>Duplicate alerts</h2>
          <p>Automatically surfaces anomalies based on customer, product, and date.</p>
          <div class="chips">
            <span class="code-chip">ORD9991</span>
            <span class="code-chip">ORD9999</span>
          </div>
        </article>
      </section>

      <footer class="landing-footer">
        <span>OrderSync · Order and sales management</span>
        <span class="stack">Vue.js · Flask · PostgreSQL</span>
      </footer>
    </div>
  </div>
</template>

<style scoped>
.landing {
  min-height: 100vh;
  background: var(--bg-app);
  padding: 24px;
}
.landing-inner {
  max-width: 1560px;
  margin: 0 auto;
}
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  background: #fff;
  border-radius: 22px;
  padding: 14px 20px;
  margin-bottom: 20px;
  box-shadow: var(--shadow-card);
}
.brand {
  display: flex;
  align-items: center;
  gap: 13px;
  text-decoration: none;
}
.brand-mark {
  width: 44px;
  height: 44px;
  border-radius: 13px;
  background: var(--ink);
  color: var(--lime);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.brand-name {
  font-family: 'Inter Tight', sans-serif;
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.04em;
  color: var(--ink);
}
.topbar-actions {
  display: flex;
  gap: 10px;
}
.hero-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.62fr) minmax(0, 1fr);
  gap: 20px;
}
.hero-card {
  background: var(--ink);
  color: #fff;
  border-radius: 32px;
  padding: clamp(36px, 4vw, 68px);
  display: flex;
  flex-direction: column;
  min-height: 560px;
}
.hero-eyebrow {
  align-self: flex-start;
  border: 1px solid rgba(199, 245, 60, 0.45);
  color: var(--lime);
  border-radius: 999px;
  padding: 7px 16px;
  font-size: 11.5px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  margin-bottom: clamp(28px, 4vw, 52px);
}
.hero-card h1 {
  font-size: clamp(42px, 5.4vw, 82px);
  line-height: 0.98;
  font-weight: 800;
  letter-spacing: -0.055em;
}
.accent {
  color: var(--lime);
}
.hero-copy {
  color: #a7b0c2;
  font-size: 17px;
  line-height: 1.65;
  max-width: 600px;
  margin-top: 28px;
}
.hero-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: auto;
  padding-top: 40px;
}
.hero-btn {
  height: 54px;
  padding: 0 30px;
  font-size: 15px;
}
.btn-ghost-dark {
  border: 1px solid #35415a;
  color: #fff;
  background: transparent;
}
.btn-ghost-dark:hover {
  background: #1a2437;
}
.side-column {
  display: grid;
  grid-template-rows: 1.46fr 1fr;
  gap: 20px;
}
.stat-card {
  border-radius: 32px;
  padding: clamp(26px, 2.6vw, 40px);
  display: flex;
  flex-direction: column;
}
.stat-blue {
  background: var(--blue);
  color: #fff;
}
.stat-label {
  font-size: 14px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.85);
}
.stat-value {
  font-family: 'Inter Tight', sans-serif;
  font-size: clamp(48px, 5vw, 76px);
  font-weight: 800;
  letter-spacing: -0.05em;
  line-height: 1;
  margin-top: 12px;
}
.stat-value-dark {
  color: var(--ink);
}
.bar-chart {
  display: flex;
  align-items: flex-end;
  gap: clamp(5px, 0.7vw, 10px);
  height: 74px;
  margin-top: auto;
  padding-top: 24px;
}
.bar-chart span {
  flex: 1;
  border-radius: 5px;
  background: var(--lime);
  min-width: 5px;
}
.stat-orange {
  background: var(--orange);
  color: var(--ink);
}
.stat-title {
  font-size: 14px;
  font-weight: 600;
}
.stat-note {
  margin-top: auto;
  padding-top: 16px;
  font-size: 13.5px;
  line-height: 1.45;
}
.feature-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 20px;
  margin-top: 20px;
}
.feature-card {
  background: #fff;
  border-radius: 28px;
  padding: 30px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 250px;
}
.feature-card h2 {
  font-size: 21px;
  font-weight: 700;
  letter-spacing: -0.03em;
}
.feature-card p {
  font-size: 14px;
  line-height: 1.55;
  color: #5f6b7d;
}
.feature-lime {
  background: var(--lime);
}
.feature-lime h2 {
  color: var(--ink);
}
.feature-lime p {
  color: #2f3a1e;
}
.feature-cream {
  background: var(--cream);
}
.feature-icon {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 6px;
}
.icon-soft-blue {
  background: #e6ecff;
  color: var(--blue);
}
.icon-dark {
  background: var(--ink);
  color: var(--lime);
}
.icon-white {
  background: #fff;
  color: var(--ink);
}
.chips {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: auto;
}
.code-chip {
  background: #fff;
  border-radius: 999px;
  padding: 5px 12px;
  font-size: 11.5px;
  font-weight: 700;
  font-family: 'Inter', sans-serif;
  letter-spacing: 0.02em;
  color: var(--ink);
}
.formula {
  margin-top: auto;
  font-size: 13px;
  font-weight: 600;
  color: var(--ink);
}
.landing-footer {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 26px 6px 10px;
  font-size: 13px;
  color: #6b7280;
}
.stack {
  letter-spacing: 0.02em;
}
@media (max-width: 1100px) {
  .hero-grid {
    grid-template-columns: 1fr;
  }
  .side-column {
    grid-template-rows: none;
    grid-template-columns: 1fr 1fr;
  }
  .feature-grid {
    grid-template-columns: 1fr;
  }
  .feature-card {
    min-height: auto;
  }
}
@media (max-width: 720px) {
  .landing {
    padding: 14px;
  }
  .topbar {
    padding: 12px 14px;
  }
  .topbar .btn-ghost {
    display: none;
  }
  .hero-card {
    min-height: auto;
    padding: 32px 24px;
    border-radius: 26px;
  }
  .hero-actions {
    padding-top: 28px;
  }
  .hero-btn {
    height: 46px;
    padding: 0 20px;
    font-size: 14px;
  }
  .side-column {
    grid-template-columns: 1fr;
  }
  .landing-footer {
    flex-direction: column;
    gap: 4px;
  }
}
</style>
