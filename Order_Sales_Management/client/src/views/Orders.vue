<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/services/api'
import { useSummaryStore } from '@/stores/summary'
import { useAuthStore } from '@/stores/auth'
import { formatDate, money, number, percent } from '@/utils/format'
import Icon from '@/components/Icon.vue'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const summaryStore = useSummaryStore()

const STATUSES = ['Pending', 'Received', 'Shipped', 'Delivered', 'Cancelled', 'Returned']
const ACTIONS = {
  Pending: [
    { status: 'Received', label: 'Receive', tone: 'dark' },
    { status: 'Shipped', label: 'Ship', tone: 'dark' },
    { status: 'Cancelled', label: 'Cancel', tone: 'danger' },
  ],
  Received: [
    { status: 'Shipped', label: 'Ship', tone: 'dark' },
    { status: 'Cancelled', label: 'Cancel', tone: 'danger' },
  ],
  Shipped: [
    { status: 'Delivered', label: 'Deliver', tone: 'dark' },
    { status: 'Returned', label: 'Return', tone: 'danger' },
  ],
  Delivered: [{ status: 'Returned', label: 'Return', tone: 'danger' }],
  Cancelled: [],
  Returned: [],
}

const orders = ref([])
const loading = ref(true)
const errorMsg = ref('')
const total = ref(0)
const pages = ref(1)
const page = ref(1)
const statusFilter = ref(route.query.status || '')
const search = ref('')
const updatingId = ref('')

const summary = computed(() => summaryStore.data || {})
const totalOrders = computed(() => summary.value.total_orders || 0)

const statusCounts = computed(() => {
  const rows = summary.value.status_breakdown || []
  return Object.fromEntries(rows.map((row) => [row.status, row.count]))
})

const tiles = computed(() => [
  {
    key: '',
    label: 'All orders',
    count: totalOrders.value,
    share: '100%',
    tone: 'all',
  },
  ...STATUSES.map((status) => ({
    key: status,
    label: status,
    count: statusCounts.value[status] || 0,
    share: `${percent(statusCounts.value[status], totalOrders.value).toFixed(1)}%`,
    tone: status.toLowerCase(),
  })),
])

let searchTimer = null

const fetchOrders = async () => {
  loading.value = true
  errorMsg.value = ''
  try {
    const params = { page: page.value, per_page: 10 }
    if (statusFilter.value) params.status = statusFilter.value
    if (search.value.trim()) params.q = search.value.trim()
    const res = await api.get('/orders', { params })
    orders.value = res.data.orders
    total.value = res.data.total
    pages.value = res.data.pages || 1
    const params2 = { ...route.query }
    if (statusFilter.value) params2.status = statusFilter.value
    else delete params2.status
    router.replace({ query: params2 })
  } catch (err) {
    errorMsg.value = err.response?.data?.error || 'Failed to load orders.'
  } finally {
    loading.value = false
  }
}

const selectStatus = (status) => {
  statusFilter.value = status
  page.value = 1
  fetchOrders()
}

const onSearch = () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    page.value = 1
    fetchOrders()
  }, 300)
}

const changeStatus = async (order, nextStatus) => {
  if (updatingId.value) return
  try {
    updatingId.value = order.order_id
    await api.patch(`/orders/${order.order_id}/status`, { order_status: nextStatus })
    order.order_status = nextStatus
    summaryStore.fetch(true)
  } catch (err) {
    errorMsg.value = err.response?.data?.error || 'Failed to update status.'
  } finally {
    updatingId.value = ''
  }
}

watch(total, (next) => {
  if (next === 0 && pages.value > 1 && page.value > 1) {
    page.value = 1
    fetchOrders()
  }
})

onMounted(async () => {
  await Promise.all([summaryStore.fetch(), fetchOrders()])
})
</script>

<template>
  <div class="orders-page">
    <header class="page-head">
      <div>
        <p class="eyebrow">OrderSync · Admin</p>
        <h1>Orders</h1>
      </div>
      <div class="head-actions">
        <button class="btn btn-primary" @click="router.push('/app/new-order')">
          <Icon name="plus" :size="15" /> New order
        </button>
        <div class="avatar">{{ (auth.user?.full_name || 'A').charAt(0).toUpperCase() }}</div>
      </div>
    </header>

    <div class="tiles">
      <button
        v-for="tile in tiles"
        :key="tile.key || 'all'"
        class="tile"
        :class="[`tile-${tile.tone}`, { active: statusFilter === tile.key }]"
        @click="selectStatus(tile.key)"
      >
        <span class="tile-label">{{ tile.label }}</span>
        <strong class="tile-share">{{ tile.share }}</strong>
        <span class="tile-count">{{ number(tile.count) }} orders</span>
      </button>
    </div>

    <section class="card table-card">
      <div class="table-top">
        <h2>All orders <span class="count-pill">{{ number(total) }}</span></h2>
        <div class="table-tools">
          <label class="search">
            <Icon name="search" :size="16" />
            <input
              v-model="search"
              type="search"
              placeholder="Search order or customer"
              aria-label="Search orders"
              @input="onSearch"
            />
          </label>
          <select v-model="statusFilter" class="input filter" aria-label="Filter by status" @change="page = 1; fetchOrders()">
            <option value="">All statuses</option>
            <option v-for="status in STATUSES" :key="status" :value="status">{{ status }}</option>
          </select>
        </div>
      </div>

      <div v-if="errorMsg" class="error-banner banner-gap">{{ errorMsg }}</div>
      <div v-if="loading" class="spinner-state">Loading orders…</div>

      <div v-else class="scroll-x">
        <table class="table">
          <thead>
            <tr>
              <th>Order ID</th>
              <th>Customer</th>
              <th>Date</th>
              <th>Status</th>
              <th>Items</th>
              <th class="right">Total</th>
              <th class="right">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="order in orders" :key="order.order_id">
              <td>
                <router-link :to="`/app/orders/${order.order_id}`" class="order-link">
                  {{ order.order_id }}
                </router-link>
              </td>
              <td class="muted">{{ order.customer_id }}</td>
              <td class="muted">{{ formatDate(order.order_date) }}</td>
              <td>
                <span class="status-pill" :class="order.order_status.toLowerCase()">
                  {{ order.order_status }}
                </span>
              </td>
              <td class="muted">{{ order.item_count }}</td>
              <td class="right mono">{{ money(order.total) }}</td>
              <td class="right">
                <div class="row-actions">
                  <button
                    v-for="action in ACTIONS[order.order_status] || []"
                    :key="action.status"
                    class="btn btn-sm"
                    :class="action.tone === 'danger' ? 'btn-outline-red' : 'btn-dark'"
                    :disabled="updatingId === order.order_id"
                    @click="changeStatus(order, action.status)"
                  >
                    {{ action.label }}
                  </button>
                  <span v-if="!ACTIONS[order.order_status]?.length" class="muted dash">—</span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <p v-if="!loading && !orders.length && !errorMsg" class="empty-state">
        No orders match this filter.
      </p>

      <div v-if="pages > 1" class="pagination">
        <button class="btn btn-ghost" :disabled="page === 1" @click="page--; fetchOrders()">
          Previous
        </button>
        <span class="page-info">Page {{ page }} of {{ pages }}</span>
        <button class="btn btn-dark" :disabled="page >= pages" @click="page++; fetchOrders()">
          Next
        </button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.orders-page {
  max-width: 1400px;
}
.page-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
  margin-bottom: 20px;
}
.page-head h1 {
  font-size: clamp(30px, 2.6vw, 40px);
  font-weight: 700;
  letter-spacing: -0.045em;
  margin-top: 6px;
}
.head-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}
.tiles {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 16px;
}
.tile {
  display: flex;
  flex-direction: column;
  gap: 4px;
  align-items: flex-start;
  padding: 16px 16px 14px;
  border-radius: 18px;
  text-align: left;
  transition: transform 0.16s ease, box-shadow 0.16s ease;
}
.tile:hover {
  transform: translateY(-2px);
}
.tile.active {
  outline: 2px solid var(--ink);
  outline-offset: 2px;
}
.tile-label {
  font-size: 12.5px;
  font-weight: 600;
}
.tile-share {
  font-family: 'Inter Tight', sans-serif;
  font-size: 24px;
  font-weight: 700;
  letter-spacing: -0.03em;
}
.tile-count {
  font-size: 11px;
  opacity: 0.75;
}
.tile-all {
  background: var(--ink);
  color: #fff;
}
.tile-pending {
  background: var(--cream);
  color: #8a5a00;
}
.tile-received {
  background: var(--lavender);
  color: #4b3fa8;
}
.tile-shipped {
  background: var(--blue-soft);
  color: #1f45c9;
}
.tile-delivered {
  background: var(--mint);
  color: #137a3b;
}
.tile-cancelled {
  background: #ffe1e1;
  color: #b42318;
}
.tile-returned {
  background: var(--pink);
  color: #b4235a;
}
.table-card {
  padding: 0;
  overflow: hidden;
}
.table-top {
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
.table-tools {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.search {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  height: 44px;
  padding: 0 16px;
  border: 1px solid var(--line-strong);
  border-radius: 999px;
  background: #fff;
  color: #9aa4b7;
  min-width: 260px;
}
.search input {
  border: 0;
  outline: 0;
  background: transparent;
  font-size: 13.5px;
  color: var(--text-primary);
  width: 100%;
}
.search:focus-within {
  border-color: var(--blue);
  box-shadow: 0 0 0 3px rgba(47, 91, 255, 0.1);
}
.filter {
  width: auto;
  min-width: 160px;
  height: 44px;
  border-radius: 999px;
}
.order-link {
  color: var(--blue);
  font-weight: 600;
  text-decoration: none;
}
.order-link:hover {
  text-decoration: underline;
}
.right {
  text-align: right;
}
.row-actions {
  display: inline-flex;
  gap: 6px;
  justify-content: flex-end;
  flex-wrap: wrap;
}
.dash {
  font-size: 13px;
}
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 18px;
  padding: 22px;
  border-top: 1px solid var(--line);
}
.page-info {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
}
.banner-gap {
  margin: 0 24px 20px;
}
@media (max-width: 1280px) {
  .tiles {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}
@media (max-width: 760px) {
  .tiles {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .search {
    min-width: 0;
    width: 100%;
  }
  .filter {
    width: 100%;
  }
}
</style>
