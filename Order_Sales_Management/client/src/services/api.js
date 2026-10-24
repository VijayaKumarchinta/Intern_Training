import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

const ROLE_GUARDED = [/^\/customers/, /^\/users/, /^\/reports/]

const isRoleGuarded = (url) => ROLE_GUARDED.some((re) => re.test(url || ''))

const forceLogout = (reason) => {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  if (reason) localStorage.setItem('logout_reason', reason)
  if (window.location.pathname !== '/login' && window.location.pathname !== '/') {
    window.location.href = '/login'
  }
}

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const status = err.response?.status
    const url = err.config?.url || ''

    if (status === 401) {
      forceLogout('session_expired')
    } else if (status === 403 && isRoleGuarded(url)) {
      forceLogout('role_changed')
    }

    return Promise.reject(err)
  }
)

export default api
