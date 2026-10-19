<script setup>
import { onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Icon from '@/components/Icon.vue'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const links = [
  { name: 'Reports', label: 'Dashboard', admin: true },
  { name: 'Orders', label: 'Orders', admin: true },
  { name: 'Products', label: 'Products', admin: true },
  { name: 'Customers', label: 'Customers', admin: true },
  { name: 'Users', label: 'Users', admin: true },
  { name: 'Duplicates', label: 'Duplicates', admin: true },
  { name: 'Totals', label: 'Totals', admin: true },
  { name: 'MyOrders', label: 'My Orders', admin: false, customerOnly: true },
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
    <!-- Top Navigation Bar -->
    <header class="top-nav">
      <div class="nav-left">
        <router-link to="/" class="brand">
          <span class="brand-mark"><Icon name="layers" :size="20" :stroke-width="2.5" /></span>
          <span class="brand-name">OrderSync</span>
        </router-link>
        
        <nav class="nav-links" aria-label="Main navigation">
          <router-link
            v-for="link in visibleLinks()"
            :key="link.name"
            :to="link.name === 'MyOrders' ? '/app/my-orders' : `/app/${link.name.toLowerCase()}`"
            class="nav-link"
            :class="{ active: route.name === link.name }"
          >
            {{ link.label }}
          </router-link>
        </nav>
      </div>

      <div class="nav-right">
        <div class="user-profile">
          <span class="role-badge">{{ auth.user?.role || 'Admin' }}</span>
          <div class="avatar">{{ (auth.user?.full_name || 'A').charAt(0).toUpperCase() }}</div>
        </div>
        
        <button class="logout-btn" title="Log out" @click="handleLogout">
          <Icon name="logout" :size="18" />
        </button>
      </div>
    </header>

    <!-- Main Content -->
    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.app-shell { display: flex; flex-direction: column; min-height: 100vh; background: #f7f8fb; }
.top-nav { display: flex; align-items: center; justify-content: space-between; padding: 0 40px; height: 72px; background: #fff; border-bottom: 1px solid var(--line); position: sticky; top: 0; z-index: 50; }
.nav-left { display: flex; align-items: center; gap: 48px; }
.brand { display: flex; align-items: center; gap: 10px; text-decoration: none; color: var(--ink); }
.brand-mark { width: 36px; height: 36px; border-radius: 10px; background: var(--ink); color: var(--lime); display: flex; align-items: center; justify-content: center; }
.brand-name { font-family: 'Inter Tight', sans-serif; font-size: 20px; font-weight: 700; letter-spacing: -0.04em; }
.nav-links { display: flex; gap: 4px; }
.nav-link { text-decoration: none; color: var(--text-secondary); font-size: 14px; font-weight: 500; padding: 8px 16px; border-radius: 8px; transition: 0.2s; }
.nav-link:hover { background: #f4f6fa; color: var(--ink); }
.nav-link.active { background: #eef1f7; color: var(--ink); font-weight: 600; }
.nav-right { display: flex; align-items: center; gap: 20px; }
.user-profile { display: flex; align-items: center; gap: 12px; }
.role-badge { font-size: 13px; text-transform: capitalize; color: var(--text-secondary); background: #f1f3f8; padding: 6px 12px; border-radius: 99px; font-weight: 500; }
.avatar { width: 36px; height: 36px; border-radius: 50%; background: var(--ink); color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: 14px; }
.logout-btn { color: var(--text-secondary); padding: 8px; border-radius: 8px; transition: 0.2s; }
.logout-btn:hover { background: #fee2e2; color: #991b1b; }
.app-main { flex: 1; padding: 32px 40px; max-width: 1600px; margin: 0 auto; width: 100%; box-sizing: border-box; }

@media (max-width: 1100px) {
  .nav-links { display: none; }
  .top-nav { padding: 0 20px; }
  .app-main { padding: 20px; }
  .nav-left { gap: 20px; }
}
</style>