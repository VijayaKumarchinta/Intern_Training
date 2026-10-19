<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Icon from '@/components/Icon.vue'
import TotalsPanel from '@/components/TotalsPanel.vue'

const auth = useAuthStore()
const router = useRouter()

const links = [
  { name: 'Reports', label: 'Dashboard', icon: 'dashboard', admin: true },
  { name: 'Orders', label: 'Orders', icon: 'orders', admin: true },
  { name: 'MyOrders', label: 'My orders', icon: 'orders', admin: false, customerOnly: true },
  { name: 'Products', label: 'Products', icon: 'products', admin: true },
  { name: 'Customers', label: 'Customers', icon: 'customers', admin: true },
  { name: 'Users', label: 'Users', icon: 'users', admin: true },
  { name: 'Duplicates', label: 'Duplicates', icon: 'duplicates', admin: true },
]

const visibleLinks = () =>
  links.filter((link) => (auth.isAdmin ? link.admin : link.customerOnly))

const handleLogout = () => {
  auth.logout()
  router.replace('/login')
}

onMounted(() => {
  auth.fetchMe()
})
</script>

<template>
  <div class="app-shell">
    <aside class="rail">
      <router-link to="/" class="rail-brand" title="OrderSync home">
        <span class="rail-mark"><Icon name="layers" :size="24" :stroke-width="2.2" /></span>
      </router-link>

      <nav class="rail-nav" aria-label="Main navigation">
        <router-link
          v-for="link in visibleLinks()"
          :key="link.name"
          :to="link.name === 'MyOrders' ? '/app/my-orders' : `/app/${link.name.toLowerCase()}`"
          class="rail-link"
          :title="link.label"
        >
          <Icon :name="link.icon" :size="21" />
          <span>{{ link.label }}</span>
        </router-link>
      </nav>

      <button class="rail-logout" title="Log out" aria-label="Log out" @click="handleLogout">
        <Icon name="logout" :size="21" />
      </button>
    </aside>

    <TotalsPanel v-if="auth.isAdmin" />

    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.app-shell {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  min-height: 100vh;
  padding: 16px;
}
.rail {
  width: 112px;
  flex: none;
  position: sticky;
  top: 16px;
  height: calc(100vh - 32px);
  background: #fff;
  border-radius: 28px;
  padding: 18px 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  box-shadow: var(--shadow-card);
  z-index: 20;
}
.rail-brand {
  display: block;
  margin-bottom: 26px;
}
.rail-mark {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  background: var(--ink);
  color: var(--lime);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.rail-nav {
  display: flex;
  flex-direction: column;
  gap: 6px;
  width: 100%;
}
.rail-link {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
  padding: 11px 4px;
  border-radius: 14px;
  color: #7a8497;
  text-decoration: none;
  font-size: 10.5px;
  font-weight: 600;
  line-height: 1.2;
  transition: background 0.18s ease, color 0.18s ease;
}
.rail-link:hover {
  background: #f4f6fa;
  color: var(--ink);
}
.rail-link.router-link-active {
  background: var(--lime);
  color: var(--ink);
}
.rail-link span {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.rail-logout {
  margin-top: auto;
  width: 46px;
  height: 46px;
  border-radius: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #8b95a8;
  transition: 0.18s ease;
}
.rail-logout:hover {
  background: #fff1f1;
  color: #d92d20;
}
.app-main {
  flex: 1;
  min-width: 0;
  padding: 12px 24px 40px 8px;
}
@media (max-width: 1280px) {
  .app-shell {
    gap: 12px;
  }
  .app-main {
    padding: 8px 8px 40px 4px;
  }
}
@media (max-width: 1120px) {
  .app-shell > :global(.totals-panel) {
    display: none;
  }
}
@media (max-width: 820px) {
  .app-shell {
    flex-direction: column;
    padding: 12px;
    gap: 12px;
  }
  .rail {
    position: sticky;
    top: 8px;
    width: 100%;
    height: auto;
    flex-direction: row;
    align-items: center;
    padding: 8px;
    border-radius: 22px;
  }
  .rail-brand {
    margin-bottom: 0;
    margin-right: 4px;
  }
  .rail-mark {
    width: 42px;
    height: 42px;
  }
  .rail-nav {
    flex-direction: row;
    gap: 2px;
    overflow-x: auto;
  }
  .rail-link {
    padding: 9px 10px;
  }
  .rail-link span {
    display: none;
  }
  .rail-logout {
    margin-top: 0;
    margin-left: auto;
    width: 42px;
    height: 42px;
  }
  .app-main {
    width: 100%;
    padding: 4px 0 32px;
  }
}
</style>
