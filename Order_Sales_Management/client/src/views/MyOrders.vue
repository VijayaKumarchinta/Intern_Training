<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import { formatDate, money, number, percent } from '@/utils/format'

const router = useRouter()
const auth = useAuthStore()

const STATUSES = ['Pending', 'Received', 'Shipped', 'Delivered', 'Cancelled', 'Returned']

const orders = ref([])
const loading = ref(true)
const errorMsg = ref('')
const statusFilter = ref('')

const customerId = computed(() => auth.user?.customer_id || null)
const firstName = computed(() => auth.user?.full_name?.split(' ')[0] || 'there')

const filteredOrders = computed(() => {
  if (!statusFilter.value) return orders.value
  return orders.value.filter((order) => order.order_status === statusFilter.value)
})

const countByStatus = (status) =>
  orders.value.filter((order) => order.order_status === status).length

const deliveredShare = computed(() =>
  percent(countByStatus('Delivered'), orders.value.length),
)

const inTransitShare = computed(() =>
  percent(countByStatus('Pending') + countByStatus('Shipped'), orders.value.length),
)

const spent = computed(() =>
  orders.value
    .filter((order) => ['Shipped', 'Delivered'].includes(order.order_status))
    .reduce((total, order) => total + Number(order.total || 0), 0),
)

const distribution = computed(() => {
  const total = orders.value.length || 1
  return [
    { status: 'Delivered', count: countByStatus('Delivered'), share: percent(countByStatus('Delivered'), total), tone: 'lime' },
    { status: 'Shipped', count: countByStatus('Shipped'), share: percent(countByStatus('Shipped'), total), tone: 'blue' },
    { status: 'Pending', count: countByStatus('Pending'), share: percent(countByStatus('Pending'), total), tone: 'orange' },
    { status: 'Cancelled', count: countByStatus('Cancelled'), share: percent(countByStatus('Cancelled'), total), tone: 'red' },
  ].filter((entry) => entry.count > 0)
})

const fetchOrders = async () => {
  loading.value = true
  errorMsg.value = ''
  try {
    await auth.fetchMe()
    const res = await api.get('/orders', { params: { per_page: 200 } })
    orders.value = res.data.orders
  } catch (err) {
    errorMsg.value = 'Failed to load your orders.'
  } finally {
    loading.value = false
  }
}

onMounted(fetchOrders)
</script>

<template>
  <div class="customer-page">
    <header class="page-head">
      <div>
        <p class="eyebrow">OrderSync · Customer</p>
        <h1>Hello, {{ firstName }}</h1>
        <p class="page-sub">
          <template v-if="customerId">
            You can only see orders placed under your customer ID, {{ customerId }}.
          </template>
          <template v-else>
            Your account is not linked to a customer record yet. An admin can link it for you.
          </template>
        </p>
      </div>
      <div class="avatar">{{ firstName.charAt(0).toUpperCase() }}</div>
    </header>

    <div v-if="loading" class="spinner-state">Loading your orders…</div>
    <div v-else-if="errorMsg" class="error-banner">{{ errorMsg }}</div>

    <template v-else>
      <section class="stats">
        <div class="stat dark-stat">
          <p class="stat-label">Delivered so far</p>
          <p class="stat-big">{{ deliveredShare.toFixed(1) }}%</p>
          <p class="stat-foot">
            {{ countByStatus('Delivered') }} of your {{ orders.length }} orders
          </p>
          <div class="distribution">
            <div class="dist-bar">
              <span
                v-for="entry in distribution"
                :key="entry.status"
                :class="`tone-${entry.tone}`"
                :style="{ width: `${entry.share}%` }"
              ></span>
            </div>
            <div class="dist-legend">
              <span v-for="entry in distribution" :key="entry.status">
                <i :class="`tone-${entry.tone}`"></i>{{ entry.status }}
                {{ entry.share.toFixed(1) }}%
              </span>
            </div>
          </div>
        </div>

        <div class="stat blue-stat">
          <p class="stat-label">Total orders</p>
          <p class="stat-big">{{ number(orders.length) }}</p>
        </div>

        <div class="stat orange-stat">
          <p class="stat-label dark">Still on its way</p>
          <p class="stat-big dark">{{ inTransitShare.toFixed(1) }}%</p>
          <p class="stat-foot dark">
            {{ countByStatus('Pending') + countByStatus('Shipped') }} orders pending or shipped
          </p>
        </div>

        <div class="stat light-stat">
          <p class="stat-label">Spent on shipped + delivered</p>
          <p class="stat-big">{{ money(spent) }}</p>
        </div>
      </section>

      <section class="card orders-card">
        <div class="orders-head">
          <h2>My orders <span class="count-pill">{{ filteredOrders.length }}</span></h2>
          <select v-model="statusFilter" class="input filter" aria-label="Filter orders by status">
            <option value="">All statuses</option>
            <option v-for="status in STATUSES" :key="status" :value="status">{{ status }}</option>
          </select>
        </div>

        <div class="scroll-x">
          <table class="table">
            <thead>
              <tr>
                <th>Order ID</th>
                <th>Date</th>
                <th>Status</th>
                <th>Items</th>
                <th class="right">Total</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="order in filteredOrders"
                :key="order.order_id"
                class="clickable"
                @click="router.push(`/app/orders/${order.order_id}`)"
              >
                <td>
                  <span class="order-link">{{ order.order_id }}</span>
                </td>
                <td class="muted">{{ formatDate(order.order_date) }}</td>
                <td>
                  <span class="status-pill" :class="order.order_status.toLowerCase()">
                    {{ order.order_status }}
                  </span>
                </td>
                <td class="muted">{{ order.item_count }}</td>
                <td class="right mono">{{ money(order.total) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <p v-if="!orders.length" class="empty-state">
          No orders yet. If you recently registered, ask an admin to link your customer ID.
        </p>
        <p v-else-if="!filteredOrders.length" class="empty-state">
          No orders with that status.
        </p>
      </section>
    </template>
  </div>
</template>

<style scoped>
.customer-page {
  max-width: 1400px;
}
.page-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
  margin-bottom: 22px;
}
.page-head h1 {
  font-size: clamp(30px, 2.8vw, 42px);
  font-weight: 700;
  letter-spacing: -0.045em;
  margin-top: 6px;
}
.page-sub {
  margin-top: 8px;
  font-size: 14px;
  color: var(--text-secondary);
  max-width: 620px;
}
.stats {
  display: grid;
  grid-template-columns: 1.5fr 1fr 1fr;
  grid-template-rows: auto auto;
  gap: 16px;
  margin-bottom: 16px;
}
.stat {
  border-radius: 26px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  min-height: 148px;
}
.dark-stat {
  grid-row: span 2;
  background: var(--ink);
  color: #fff;
}
.blue-stat {
  background: var(--blue);
  color: #fff;
}
.orange-stat {
  background: var(--orange);
  color: var(--ink);
}
.light-stat {
  background: #fff;
}
.stat-label {
  font-size: 13.5px;
  color: rgba(255, 255, 255, 0.85);
}
.dark-stat .stat-label,
.light-stat .stat-label {
  color: #9aa4b7;
}
.blue-stat .stat-label {
  color: rgba(255, 255, 255, 0.88);
}
.stat-label.dark {
  color: var(--ink);
}
.stat-big {
  font-family: 'Inter Tight', sans-serif;
  font-size: clamp(34px, 3.4vw, 52px);
  font-weight: 800;
  letter-spacing: -0.05em;
  line-height: 1;
  margin: auto 0 10px;
}
.dark-stat .stat-big {
  color: var(--lime);
  font-size: clamp(44px, 4.4vw, 64px);
}
.stat-big.dark {
  color: var(--ink);
}
.stat-foot {
  font-size: 12.5px;
  color: rgba(255, 255, 255, 0.78);
}
.dark-stat .stat-foot {
  color: #9aa4b7;
}
.stat-foot.dark {
  color: #4a2a17;
}
.distribution {
  margin-top: auto;
  padding-top: 22px;
}
.dist-bar {
  display: flex;
  gap: 3px;
  height: 8px;
}
.dist-bar span {
  height: 100%;
  border-radius: 999px;
}
.dist-bar span:first-child {
  border-radius: 999px 0 0 999px;
}
.dist-bar span:last-child {
  border-radius: 0 999px 999px 0;
}
.dist-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  margin-top: 12px;
  font-size: 11px;
  color: #9aa4b7;
}
.dist-legend span {
  display: inline-flex;
  flex-direction: column;
  gap: 3px;
}
.dist-legend i {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}
.tone-lime {
  background: var(--lime);
}
.tone-blue {
  background: #6b8bff;
}
.tone-orange {
  background: #ff9c6e;
}
.tone-red {
  background: #ef5350;
}
.orders-card {
  padding: 0;
  overflow: hidden;
}
.orders-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 22px 24px;
  flex-wrap: wrap;
}
h2 {
  font-size: 19px;
  font-weight: 700;
  letter-spacing: -0.03em;
  display: flex;
  align-items: center;
  gap: 10px;
}
.count-pill {
  background: #f1f3f8;
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
}
.filter {
  width: auto;
  min-width: 160px;
  height: 42px;
}
.order-link {
  color: var(--blue);
  font-weight: 600;
}
.clickable {
  cursor: pointer;
}
.right {
  text-align: right;
}
@media (max-width: 980px) {
  .stats {
    grid-template-columns: 1fr 1fr;
  }
  .dark-stat {
    grid-row: span 1;
    grid-column: span 2;
  }
}
@media (max-width: 600px) {
  .stats {
    grid-template-columns: 1fr;
  }
  .dark-stat {
    grid-column: span 1;
  }
}
</style>
