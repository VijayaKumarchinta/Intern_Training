import { defineStore } from 'pinia'
import api from '@/services/api'

const ME_CACHE_MS = 30_000

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || null,
    user: JSON.parse(localStorage.getItem('user')) || null,
    _meLastFetched: 0,
  }),
  getters: {
    isAuthenticated: (state) => !!state.token,
    isAdmin: (state) => state.user?.role === 'admin',
  },
  actions: {
    async login(email, password) {
      const res = await api.post('/auth/login', { email, password })
      this.token = res.data.access_token
      this.user = res.data.user
      this._meLastFetched = Date.now()
      localStorage.setItem('token', this.token)
      localStorage.setItem('user', JSON.stringify(this.user))
    },

    async fetchMe(force = false) {
      if (!this.token) return
      if (!force && Date.now() - this._meLastFetched < ME_CACHE_MS) return
      try {
        const res = await api.get('/auth/me')
        this.user = res.data
        this._meLastFetched = Date.now()
        localStorage.setItem('user', JSON.stringify(this.user))
      } catch (err) {
      }
    },

    logout() {
      this.token = null
      this.user = null
      this._meLastFetched = 0
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    },
  },
})
