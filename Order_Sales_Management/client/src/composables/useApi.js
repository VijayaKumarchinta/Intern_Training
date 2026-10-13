import { ref } from 'vue'

const API_BASE = '/api'

export function useApi() {
  const loading = ref(false)
  const error = ref(null)

  async function request(path, options = {}) {
    loading.value = true
    error.value = null

    try {
      const response = await fetch(`${API_BASE}${path}`, {
        headers: {
          'Content-Type': 'application/json',
        },
        ...options,
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.message || 'Request failed')
      }

      return data
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    loading,
    error,
    get: (path) => request(path),
    post: (path, body) => request(path, {
      method: 'POST',
      body: JSON.stringify(body)
    }),
    put: (path, body) => request(path, {
      method: 'PUT',
      body: JSON.stringify(body)
    }),
  }
}
