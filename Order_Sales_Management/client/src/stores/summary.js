import { defineStore } from 'pinia'
import api from '@/services/api'

export const useSummaryStore = defineStore('summary', {
  state: () => ({
    data: null,
    loading: false,
    error: '',
  }),
  actions: {
    async fetch(force = false) {
      if (this.data && !force) return
      if (this.loading) return
      this.loading = true
      this.error = ''
      try {
        const res = await api.get('/reports/summary')
        this.data = res.data
      } catch (err) {
        this.error = 'Failed to load totals.'
      } finally {
        this.loading = false
      }
    },
  },
})
