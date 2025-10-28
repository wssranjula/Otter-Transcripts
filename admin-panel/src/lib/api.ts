import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add request interceptor to include auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('admin_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Add response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('admin_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authApi = {
  login: async (username: string, password: string) => {
    const response = await api.post('/admin/login', { username, password })
    return response.data
  },
}

// Config API
export const configApi = {
  getSybilPrompt: async () => {
    const response = await api.get('/admin/config/sybil-prompt')
    return response.data
  },
  
  updateSybilPrompt: async (section: string, content: string) => {
    const response = await api.put('/admin/config/sybil-prompt', { section, content })
    return response.data
  },
}

// Whitelist API
export const whitelistApi = {
  getWhitelist: async () => {
    const response = await api.get('/admin/whitelist')
    return response.data
  },
  
  addToWhitelist: async (phoneNumber: string, name?: string) => {
    const response = await api.post('/admin/whitelist', { phone_number: phoneNumber, name })
    return response.data
  },
  
  removeFromWhitelist: async (phoneNumber: string) => {
    const response = await api.delete(`/admin/whitelist/${phoneNumber}`)
    return response.data
  },
  
  toggleWhitelist: async (enabled: boolean) => {
    const response = await api.put('/admin/whitelist/enable', null, { params: { enabled } })
    return response.data
  },
}

// Stats API
export const statsApi = {
  getStats: async () => {
    const response = await api.get('/admin/stats')
    return response.data
  },
}

export default api
