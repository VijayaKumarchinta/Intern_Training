<script setup>
import { useAuthStore } from '@/stores/auth'
import { useRouter, useRoute } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const handleLogout = () => {
  auth.logout()
  router.replace('/login')
}
</script>

<template>
  <div class="app-layout">
    <aside class="sidebar">
      <div class="logo">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
      </div>
      <nav>
        <router-link v-if="auth.isAdmin" to="/app/reports" title="Dashboard" class="nav-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>
        </router-link>
        <router-link to="/app/orders" title="Orders" class="nav-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line></svg>
        </router-link>
        <router-link v-if="auth.isAdmin" to="/app/products" title="Products" class="nav-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 7h-9m3 10H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2z"></path><circle cx="12" cy="12" r="3"></circle></svg>
        </router-link>
        <router-link v-if="auth.isAdmin" to="/app/customers" title="Customers" class="nav-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle></svg>
        </router-link>
        <router-link v-if="auth.isAdmin" to="/app/users" title="Users" class="nav-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><line x1="19" y1="8" x2="19" y2="14"></line><line x1="22" y1="11" x2="16" y2="11"></line></svg>
        </router-link>
        <router-link v-if="auth.isAdmin" to="/app/duplicates" title="Duplicates" class="nav-icon">
           <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
        </router-link>
      </nav>
      <button class="logout-btn" @click="handleLogout" title="Logout">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>
      </button>
    </aside>

    <main class="main-content">
      <header class="topbar">
        <div class="header-left">
          <h1 v-if="route.name === 'Reports'">Good afternoon, {{ auth.user?.full_name?.split(' ')[0] || 'Admin' }}</h1>
          <h1 v-else>{{ route.name }}</h1>
          <p class="subtitle" v-if="route.name === 'Reports'">Here is how orders and sales look today.</p>
        </div>
        
        <div class="header-right">
          <button v-if="auth.isAdmin" class="btn-primary" @click="router.push('/app/new-order')">New order</button>
          <div class="avatar">{{ auth.user?.full_name?.charAt(0) || 'A' }}</div>
        </div>
      </header>

      <div class="page-container">
        <router-view />
      </div>
    </main>
  </div>
</template>

<style scoped>
.app-layout { display: flex; min-height: 100vh; background: var(--bg-app); }
.sidebar { width: 88px; background: white; display: flex; flex-direction: column; align-items: center; padding: 32px 0; border-right: 1px solid var(--border-color); }
.logo { width: 44px; height: 44px; background: var(--brand-purple); color: white; border-radius: 12px; display: flex; align-items: center; justify-content: center; margin-bottom: 48px; }
nav { display: flex; flex-direction: column; gap: 12px; flex: 1; }
.nav-icon { width: 48px; height: 48px; display: flex; align-items: center; justify-content: center; border-radius: 12px; color: var(--text-secondary); transition: 0.2s; }
.nav-icon:hover { background: var(--bg-app); color: var(--text-primary); }
.nav-icon.router-link-active { background: var(--kpi-purple-bg); color: var(--brand-purple); }
.logout-btn { background: transparent; padding: 12px; color: var(--text-secondary); border-radius: 12px; transition: 0.2s; }
.logout-btn:hover { background: #FEE2E2; color: #991B1B; }
.main-content { flex: 1; display: flex; flex-direction: column; }
.topbar { display: flex; justify-content: space-between; align-items: flex-start; padding: 40px 48px 24px 48px; }
.header-left h1 { font-size: 28px; font-weight: 700; margin-bottom: 6px; letter-spacing: -0.5px; }
.subtitle { color: var(--text-secondary); font-size: 15px; }
.header-right { display: flex; align-items: center; gap: 16px; }
.avatar { width: 44px; height: 44px; border-radius: 50%; background: #1A1D21; color: white; display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: 16px; }
.page-container { padding: 0 48px 48px 48px; max-width: 1600px; width: 100%; margin: 0 auto; }
</style>