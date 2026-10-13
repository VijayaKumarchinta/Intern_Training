<script setup>
import { ref, onMounted } from 'vue'
import CustomerPanel from './components/CustomerPanel.vue'
import ProductPanel from './components/ProductPanel.vue'
import OrderPanel from './components/OrderPanel.vue'
import ReportPanel from './components/ReportPanel.vue'

const activeTab = ref('customers')

const tabs = [
  { id: 'customers', label: 'Customers', icon: '👥' },
  { id: 'products', label: 'Products', icon: '📦' },
  { id: 'orders', label: 'Orders', icon: '🛒' },
  { id: 'reports', label: 'Reports', icon: '📊' }
]
</script>

<template>
  <div class="app">
    <header class="header">
      <h1>📦 Order & Sales Management</h1>
      <p>Flask + Vue.js + PostgreSQL</p>
    </header>

    <nav class="tabs">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        :class="{ active: activeTab === tab.id }"
        @click="activeTab = tab.id"
      >
        {{ tab.icon }} {{ tab.label }}
      </button>
    </nav>

    <main class="content">
      <CustomerPanel v-if="activeTab === 'customers'" />
      <ProductPanel v-else-if="activeTab === 'products'" />
      <OrderPanel v-else-if="activeTab === 'orders'" />
      <ReportPanel v-else-if="activeTab === 'reports'" />
    </main>

    <footer class="footer">
      <span>Order & Sales Management Application</span>
    </footer>
  </div>
</template>

<style scoped>
.app {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.header {
  text-align: center;
  margin-bottom: 24px;
}

.header h1 {
  color: #42b983;
  margin: 0;
}

.header p {
  color: #666;
  margin: 8px 0 0;
}

.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.tabs button {
  padding: 12px 20px;
  border: none;
  background: #f0f0f0;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 8px;
}

.tabs button:hover {
  background: #e0e0e0;
}

.tabs button.active {
  background: #42b983;
  color: white;
}

.content {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.footer {
  text-align: center;
  margin-top: 24px;
  color: #999;
  font-size: 12px;
}
</style>
