<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import { useSummaryStore } from '@/stores/summary'
import { formatDate, money, percent } from '@/utils/format'
import Icon from '@/components/Icon.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const summaryStore = useSummaryStore()

const order = ref(null)
const loading = ref(true)
const errorMsg = ref('')
const updating = ref('')

const PROGRESS = ['Pending', 'Received', 'Shipped', 'Delivered']

const allowedTransitions = {
  Pending: ['Received', 'Shipped', 'Cancelled'],
  Received: ['Shipped', 'Cancelled'],
  Shipped: ['Delivered', 'Returned'],
  Delivered: ['Returned'],
  Cancelled: [],
  Returned: [],
}

const nextStatuses = computed(() =>
  order.value ? allowedTransitions[order.value.order_status] || [] : [],
)

const progressIndex = computed(() => {
  if (!order.value) return -1
  return PROGRESS.indexOf(order.value.order_status)
})

const revenueShare = computed(() => {
  const revenue = summaryStore.data?.revenue
  if (!order.value || !revenue) return 0
  return percent(order.value.total, revenue)
})

const itemCount = computed(
  () => (order.value?.items || []).reduce((sum, item) => sum + item.quantity, 0),
)

const fetchOrder = async () => {
  loading.value = true
  errorMsg.value = ''
  try {
    const res = await api.get(`/orders/${route.params.id}`)
    order.value = res.data
  } catch (err) {
    errorMsg.value =
      err.response?.status === 404
        ? 'Order not found, or you do not have access to it.'
        : 'Failed to load this order.'
  } finally {
    loading.value = false
  }
}

const updateStatus = async (newStatus) => {
  if (updating.value) return
  try {
    updating.value = newStatus
    const res = await api.patch(`/orders/${order.value.order_id}/status`, {
      order_status: newStatus,
    })
    order.value.order_status = res.data.order_status
    summaryStore.fetch(true)
  } catch (err) {
    errorMsg.value = err.response?.data?.error || 'Failed to update status.'
  } finally {
    updating.value = ''
  }
}

const backTarget = computed(() => (auth.isAdmin ? '/app/orders' : '/app/my-orders'))

onMounted(() => {
  if (auth.isAdmin) summaryStore.fetch()
  fetchOrder()
})
</script>

<template>
  <div class="detail-page">
    <button class="back-link" @click="router.push(backTarget)">
      <Icon name="arrowLeft" :size="15" /> Back to orders
    </button>

    <header class="page-head">
      <div>
        <p class="eyebrow">OrderSync · {{ auth.isAdmin ? 'Admin' : 'Customer' }}</p>
        <h1>Order detail</h1>
      </div>
      <div class="avatar">
        {{ (auth.user?.full_name || 'A').charAt(0).toUpperCase() }}
      </div>
    </header>

    <div v-if="loading" class="spinner-state">Loading order…</div>
    <div v-else-if="errorMsg && !order" class="card error-card">
      <p>{{ errorMsg }}</p>
      <button class="btn btn-ghost" @click="fetchOrder">Try again</button>
    </div>

    <template v-else-if="order">
      <div v-if="errorMsg" class="error-banner banner-gap">{{ errorMsg }}</div>

      <div class="detail-grid">
        <div class="main-column">
          <section class="card order-card">
            <div class="order-top">
              <div>
                <p class="card-label">Order</p>
                <div class="order-title-row">
                  <h2 class="order-title mono">{{ order.order_id }}</h2>
                  <span class="status-pill" :class="order.order_status.toLowerCase()">
                    {{ order.order_status }}
                  </span>
                </div>
                <p class="order-meta">
                  Placed on {{ formatDate(order.order_date) }} for
                  <strong>{{ order.customer?.cust_name || order.customer_id }}</strong>
                  <span class="customer-id">({{ order.customer_id }})</span>
                </p>
              </div>
            </div>

            <div v-if="progressIndex >= 0" class="progress">
              <div class="progress-track">
                <span
                  v-for="(step, index) in PROGRESS"
                  :key="step"
                  class="progress-seg"
                  :class="{ filled: index <= progressIndex }"
                ></span>
              </div>
              <div class="progress-labels">
                <span
                  v-for="(step, index) in PROGRESS"
                  :key="step"
                  :class="{ reached: index <= progressIndex }"
                >
                  {{ step }}
                </span>
              </div>
            </div>
            <div v-else class="terminal-note">
              This order is {{ order.order_status.toLowerCase() }}. No further transitions are
              available.
            </div>

            <div v-if="auth.isAdmin && nextStatuses.length" class="status-actions">
              <span class="move-label">Move to</span>
              <button
                v-for="status in nextStatuses"
                :key="status"
                class="btn"
                :class="status === 'Cancelled' || status === 'Returned' ? 'btn-outline-red' : 'btn-dark'"
                :disabled="!!updating"
                @click="updateStatus(status)"
              >
                {{ updating === status ? 'Saving…' : `Mark ${status}` }}
              </button>
            </div>
            <p v-if="auth.isAdmin" class="helper">Only valid next steps are offered.</p>
          </section>

          <section class="card items-card">
            <h3>Line items</h3>
            <div class="scroll-x">
              <table class="table">
                <thead>
                  <tr>
                    <th>Product</th>
                    <th class="right">Quantity</th>
                    <th class="right">Unit price</th>
                    <th class="right">Line total</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in order.items" :key="item.order_item_id">
                    <td>
                      <span class="product-name">
                        <i></i>
                        {{ item.product_name || `Product ${item.product_id}` }}
                        <small>product {{ item.product_id }}</small>
                      </span>
                    </td>
                    <td class="right mono">{{ item.quantity }}</td>
                    <td class="right mono">{{ money(item.unit_price) }}</td>
                    <td class="right mono strong">{{ money(item.line_total) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div class="total-row">
              <span>Total</span>
              <span class="mono total-value">{{ money(order.total) }}</span>
            </div>
            <p class="helper">Prices are locked by the server when the order is created.</p>
          </section>
        </div>

        <aside class="side-column">
          <section class="total-card">
            <p class="side-label">Order total</p>
            <p class="side-value mono">{{ money(order.total) }}</p>
            <p v-if="auth.isAdmin" class="side-foot">
              {{ revenueShare.toFixed(2) }}% of total revenue
            </p>
            <p v-else class="side-foot">{{ itemCount }} items in this order</p>
          </section>

          <section class="card customer-card">
            <p class="card-label">Customer</p>
            <h3 class="customer-name">{{ order.customer?.cust_name || order.customer_id }}</h3>
            <p class="customer-meta">
              {{ order.customer?.user_id ? 'Linked to a registered user' : 'No login linked yet' }}
            </p>
            <p v-if="order.customer?.email" class="customer-meta">{{ order.customer.email }}</p>
          </section>
        </aside>
      </div>
    </template>
  </div>
</template>

<style scoped>
.detail-page {
  max-width: 1400px;
}
.back-link {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 600;
  padding: 6px 0;
  margin-bottom: 8px;
}
.back-link:hover {
  color: var(--text-primary);
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
.detail-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 330px;
  gap: 16px;
  align-items: start;
}
.main-column {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}
.side-column {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.card {
  padding: 26px;
  border-radius: 26px;
}
.card-label {
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 500;
}
.order-top {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}
.order-title-row {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
  margin: 6px 0 8px;
}
.order-title {
  font-family: 'Inter Tight', sans-serif;
  font-size: clamp(30px, 3vw, 40px);
  font-weight: 700;
  letter-spacing: -0.045em;
}
.order-meta {
  font-size: 13.5px;
  color: var(--text-secondary);
}
.order-meta strong {
  color: var(--text-primary);
}
.customer-id {
  color: #9aa4b7;
}
.progress {
  margin-top: 28px;
}
.progress-track {
  display: flex;
  gap: 8px;
}
.progress-seg {
  flex: 1;
  height: 7px;
  border-radius: 999px;
  background: #eceff4;
}
.progress-seg.filled {
  background: var(--ink);
}
.progress-labels {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}
.progress-labels span {
  flex: 1;
  font-size: 12px;
  color: #9aa4b7;
}
.progress-labels span.reached {
  color: var(--text-primary);
  font-weight: 600;
}
.terminal-note {
  margin-top: 22px;
  font-size: 13px;
  color: var(--text-secondary);
  background: #f7f8fb;
  border-radius: 14px;
  padding: 14px 16px;
}
.status-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 26px;
  padding-top: 22px;
  border-top: 1px solid var(--line);
}
.move-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-right: 4px;
}
.helper {
  margin-top: 12px;
  font-size: 12px;
  color: #9aa4b7;
}
.items-card h3 {
  font-size: 19px;
  font-weight: 700;
  letter-spacing: -0.03em;
  margin-bottom: 10px;
}
.product-name {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  font-weight: 600;
}
.product-name i {
  width: 10px;
  height: 10px;
  border-radius: 3px;
  background: var(--orange);
  flex: none;
}
.product-name small {
  font-weight: 500;
  color: #9aa4b7;
  font-size: 11.5px;
}
.right {
  text-align: right;
}
.strong {
  font-weight: 600;
}
.total-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 18px;
  padding-top: 18px;
  border-top: 1px solid var(--line);
  font-weight: 700;
  font-size: 17px;
}
.total-value {
  font-family: 'Inter Tight', sans-serif;
  font-size: 24px;
  letter-spacing: -0.03em;
}
.total-card {
  background: var(--ink);
  color: #fff;
  border-radius: 26px;
  padding: 26px;
}
.side-label {
  font-size: 13px;
  color: #9aa4b7;
}
.side-value {
  font-family: 'Inter Tight', sans-serif;
  font-size: 42px;
  font-weight: 700;
  letter-spacing: -0.05em;
  color: var(--lime);
  margin: 10px 0 14px;
  word-break: break-word;
}
.side-foot {
  font-size: 12px;
  color: #9aa4b7;
}
.customer-card {
  background: var(--cream);
}
.customer-name {
  font-size: 24px;
  font-weight: 700;
  letter-spacing: -0.03em;
  margin: 8px 0 6px;
  color: var(--ink);
}
.customer-meta {
  font-size: 12.5px;
  color: #6f5a25;
  line-height: 1.6;
}
.error-card {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 14px;
  padding: 32px;
}
.banner-gap {
  margin-bottom: 16px;
}
@media (max-width: 1050px) {
  .detail-grid {
    grid-template-columns: 1fr;
  }
  .side-column {
    flex-direction: row;
    flex-wrap: wrap;
  }
  .side-column > * {
    flex: 1;
    min-width: 240px;
  }
}
@media (max-width: 640px) {
  .card,
  .total-card {
    padding: 20px;
  }
  .progress-labels span {
    font-size: 10.5px;
  }
}
</style>
