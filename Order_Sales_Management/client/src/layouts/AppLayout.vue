<script setup>
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()

const handleLogout = () => {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <div class="app-layout">
    <aside class="sidebar">
      <div class="logo">OS</div>
      <nav>
        <router-link to="/app/orders" title="Orders">Orders</router-link>
        <router-link v-if="auth.isAdmin" to="/app/reports" title="Reports">Reports</router-link>
        <router-link v-if="auth.isAdmin" to="/app/duplicates" title="Duplicates">Duplicates</router-link>
        <router-link v-if="auth.isAdmin" to="/app/new-order" title="New Order">New Order</router-link>
      </nav>
      <button class="logout-btn" @click="handleLogout" title="Logout">Logout</button>
    </aside>

    <main class="main-content">
      <header class="topbar">
        <h1>{{ $route.name }}</h1>
        <div class="user-info">
          <span>{{ auth.user?.full_name || auth.user?.email }}</span>
          <span class="role-badge">{{ auth.user?.role }}</span>
        </div>
      </header>
      <div class="page-container">
        <router-view />
      </div>
    </main>
  </div>
</template>

<style scoped>
.app-layout { display: flex; min-height: 100vh; }
.sidebar { width: 140px; background: white; border-right: 1px solid var(--border-color); display: flex; flex-direction: column; padding: 24px 0; }
.logo { font-weight: 800; font-size: 20px; margin-bottom: 32px; padding-left: 24px; }
nav { display: flex; flex-direction: column; gap: 4px; flex: 1; }
nav a { text-decoration: none; font-size: 14px; color: var(--text-secondary); padding: 10px 24px; transition: 0.2s; }
nav a:hover, nav a.router-link-active { background: #F3F4F6; color: var(--text-primary); font-weight: 500; }
.logout-btn { background: transparent; font-size: 14px; color: var(--accent-red); text-align: left; padding: 10px 24px; }
.main-content { flex: 1; display: flex; flex-direction: column; }
.topbar { height: 64px; background: white; border-bottom: 1px solid var(--border-color); display: flex; align-items: center; justify-content: space-between; padding: 0 32px; }
.topbar h1 { font-size: 20px; font-weight: 600; }
.user-info { display: flex; align-items: center; gap: 12px; font-size: 14px; }
.role-badge { padding: 4px 8px; border-radius: 99px; font-size: 12px; text-transform: capitalize; background: #F3F4F6; }
.page-container { padding: 32px; max-width: 1200px; margin: 0 auto; width: 100%; }
</style>