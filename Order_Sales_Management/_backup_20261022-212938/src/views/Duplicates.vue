<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import { useSummaryStore } from '@/stores/summary'
import { formatDate, money, number, percent } from '@/utils/format'
import Icon from '@/components/Icon.vue'

const router = useRouter()
const summaryStore = useSummaryStore()

const duplicates = ref([])
const loading = ref(true)
const errorMsg = ref('')
const successMsg = ref('')
const cancelling = ref('')

const totalOrders = computed(() => summaryStore.data?.total_orders || 0)
const involvedOrders = computed(() =>
  duplicates.value.reduce((total, group) => total + (group.order_ids?.length || 0), 0),
)
const duplicateShare = computed(() => percent(involvedOrders.value, totalOrders.value))
const valueAtRisk = computed(() =>
  duplicates.value.reduce((total, group) => total + Number(group.unit_price || 0), 0),
)
const uniqueOrders = computed(() => Math.max(totalOrders.value - involvedOrders.value, 0))

const orderStatus = (orderId) => {
  const order = (summaryStore.data?.latest_orders || []).find(
    (row) => row.order_id === orderId,
  )
  return order?.order_status || null
}

const cancelCopy = async (group) => {
  const target = group.order_ids[0]
  if (
    !window.confirm(
      `Cancel ${target}? This keeps both records but moves the copy to Cancelled.`,
    )
  ) {
    return
  }
  try {
    errorMsg.value = ''
    cancelling.value = target
    await api.patch(`/orders/${target}/status`, { order_status: 'Cancelled' })
    successMsg.value = `${target} cancelled. The other copy is untouched.`
    await load()
  } catch (err) {
    errorMsg.value =
      err.response?.data?.error || 'Only Pending orders can be cancelled directly.'
  } finally {
    cancelling.value = ''
  }
}

const load = async () => {
  loading.value = true
  try {
    const [dupRes] = await Promise.all([
      api.get('/orders/duplicates'),
      summaryStore.fetch(true),
    ])
    duplicates.value = dupRes.data.duplicates
  } catch (err) {
    errorMsg.value = 'Failed to load duplicates.'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="duplicates-page">
    <header class="page-head">
      <div>
        <p class="eyebrow">OrderSync · Admin</p>
        <h1>Duplicates</h1>
        <p class="page-sub">Orders sharing the same customer, product, quantity, price and date.</p>
      </div>
      
    </header>

    <div v-if="errorMsg" class="error-banner banner-gap">{{ errorMsg }}</div>
    <div v-if="successMsg" class="success-banner banner-gap">{{ successMsg }}</div>

    <section class="stats">
      <div class="stat cream-stat">
        <p class="stat-title">
          <Icon name="alert" :size="16" /> Groups flagged
        </p>
        <p class="stat-big">{{ number(duplicates.length) }}</p>
        <p class="stat-foot">{{ involvedOrders }} orders involved</p>
      </div>
      <div class="stat light-stat">
        <p class="stat-label">Share of all orders</p>
        <p class="stat-big">{{ duplicateShare.toFixed(1) }}%</p>
        <p class="stat-foot">{{ involvedOrders }} of {{ number(totalOrders) }} orders</p>
      </div>
      <div class="stat dark-stat">
        <p class="stat-label">Value at risk</p>
        <p class="stat-big">{{ money(valueAtRisk) }}</p>
        <p class="stat-foot">one copy of each group</p>
      </div>
    </section>

    <div v-if="loading" class="spinner-state">Loading duplicates…</div>

    <template v-else>
      <section v-if="duplicates.length" class="card groups-card">
        <div class="groups-head">
          <h2>Duplicate groups</h2>
          <span class="review-pill">Review before acting</span>
        </div>

        <article v-for="(group, index) in duplicates" :key="index" class="dup-group">
          <div class="group-rows">
            <p class="group-meta">
              <span>Customer <strong>{{ group.customer_id }}</strong></span>
              <span>Product {{ group.product_id }} · <strong>{{ group.product_name || 'Unknown' }}</strong></span>
              <span>Qty <strong>{{ group.quantity }}</strong></span>
              <span>Price <strong>{{ money(group.unit_price) }}</strong></span>
              <span>Date <strong>{{ formatDate(group.order_date) }}</strong></span>
            </p>
            <div class="group-ids">
              <button
                v-for="orderId in group.order_ids"
                :key="orderId"
                class="code-chip"
                @click="router.push(`/app/orders/${orderId}`)"
              >
                {{ orderId }}
              </button>
            </div>
          </div>
          <div class="group-actions">
            <span class="group-note">
              {{ orderStatus(group.order_ids[0]) ? `Latest copy: ${orderStatus(group.order_ids[0])}` : 'Review each copy' }}
            </span>
            <span v-if="group.latest_status === 'Delivered' || group.latest_status === 'Shipped'" class="muted" style="font-size:12px;">
              Cannot cancel (already {{ group.latest_status }}). Return instead.
            </span>
            <button
              v-else
              class="btn btn-sm btn-outline-red"
              :disabled="!!cancelling"
              @click="cancelCopy(group)"
            >
              {{ cancelling ? 'Cancelling…' : 'Cancel one copy' }}
            </button>
          </div>
        </article>

        <div class="unique-note">
          <Icon name="check" :size="18" />
          The other {{ number(uniqueOrders) }} orders are unique on customer, product, quantity,
          price and date.
        </div>
      </section>

      <section v-else class="card clean-card">
        <Icon name="check" :size="22" />
        <div>
          <h2>No duplicates found</h2>
          <p>All {{ number(totalOrders) }} orders are unique on customer, product, quantity, price and date.</p>
        </div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.duplicates-page {
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
.page-sub {
  margin-top: 6px;
  font-size: 14px;
  color: var(--text-secondary);
}
.stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}
.stat {
  border-radius: 26px;
  padding: 24px;
  min-height: 152px;
  display: flex;
  flex-direction: column;
}
.cream-stat {
  background: var(--cream);
  color: #6f5a25;
}
.light-stat {
  background: #fff;
}
.dark-stat {
  background: var(--ink);
  color: #fff;
}
.stat-title {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-size: 13.5px;
  font-weight: 600;
}
.stat-label {
  font-size: 13.5px;
  color: var(--text-secondary);
}
.dark-stat .stat-label {
  color: #9aa4b7;
}
.stat-big {
  font-family: 'Inter Tight', sans-serif;
  font-size: clamp(34px, 3.4vw, 46px);
  font-weight: 800;
  letter-spacing: -0.05em;
  line-height: 1;
  margin: auto 0 10px;
}
.dark-stat .stat-big {
  color: var(--lime);
}
.stat-foot {
  font-size: 12.5px;
  opacity: 0.75;
}
.groups-card {
  padding: 24px;
  border-radius: 26px;
}
.groups-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 18px;
}
h2 {
  font-size: 20px;
  font-weight: 700;
  letter-spacing: -0.03em;
}
.review-pill {
  background: var(--cream);
  color: #8a5a00;
  border-radius: 999px;
  padding: 7px 14px;
  font-size: 12px;
  font-weight: 600;
}
.dup-group {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  flex-wrap: wrap;
  background: var(--cream);
  border-radius: 18px;
  padding: 18px 20px;
  margin-bottom: 12px;
}
.group-rows {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 0;
}
.group-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 20px;
  font-size: 12.5px;
  color: #6f5a25;
}
.group-meta strong {
  color: #3f3313;
}
.group-ids {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.code-chip {
  background: #fff;
  border-radius: 999px;
  padding: 7px 14px;
  font-size: 12px;
  font-weight: 700;
  font-family: 'Inter', sans-serif;
  color: var(--ink);
  cursor: pointer;
  transition: box-shadow 0.16s ease;
}
.code-chip:hover {
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.1);
}
.group-actions {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
}
.group-note {
  font-size: 12px;
  color: #8a7a4d;
}
.unique-note {
  display: flex;
  align-items: center;
  gap: 10px;
  background: var(--mint);
  color: #11653a;
  border-radius: 16px;
  padding: 16px 18px;
  font-size: 13.5px;
  margin-top: 6px;
}
.clean-card {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 28px;
  background: var(--mint);
  color: #11653a;
}
.clean-card h2 {
  color: #0f5132;
  margin-bottom: 6px;
}
.clean-card p {
  font-size: 13.5px;
}
.banner-gap {
  margin-bottom: 16px;
}
@media (max-width: 860px) {
  .stats {
    grid-template-columns: 1fr;
  }
  .dup-group {
    align-items: flex-start;
  }
  .group-actions {
    width: 100%;
    justify-content: space-between;
  }
}
</style>
