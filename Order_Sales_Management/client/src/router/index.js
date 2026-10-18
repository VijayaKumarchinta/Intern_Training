import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  { path: '/', name: 'Landing', component: () => import('@/views/Landing.vue') },
  { path: '/login', name: 'Login', component: () => import('@/views/Login.vue') },
  { path: '/register', name: 'Register', component: () => import('@/views/Register.vue') },
  { path: '/forgot-password', name: 'ForgotPassword', component: () => import('@/views/ForgotPassword.vue') },
  { path: '/reset-password', name: 'ResetPassword', component: () => import('@/views/ResetPassword.vue') },
  { 
    path: '/app', 
    component: () => import('@/layouts/AppLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: '', redirect: '/app/orders' },
      { path: 'orders', name: 'Orders', component: () => import('@/views/Orders.vue') },
      { path: 'orders/:id', name: 'OrderDetail', component: () => import('@/views/OrderDetail.vue') },
      { path: 'products', name: 'Products', component: () => import('@/views/Products.vue'), meta: { requiresAdmin: true } },
      { path: 'customers', name: 'Customers', component: () => import('@/views/Customers.vue'), meta: { requiresAdmin: true } },
      { path: 'reports', name: 'Reports', component: () => import('@/views/Reports.vue'), meta: { requiresAdmin: true } },
      { path: 'duplicates', name: 'Duplicates', component: () => import('@/views/Duplicates.vue'), meta: { requiresAdmin: true } },
      { path: 'new-order', name: 'CreateOrder', component: () => import('@/views/CreateOrder.vue'), meta: { requiresAdmin: true } },
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    next('/login')
  } 
  else if (to.meta.requiresAdmin && !auth.isAdmin) {
    next('/app/orders')
  } 
  else {
    next()
  }
})

export default router