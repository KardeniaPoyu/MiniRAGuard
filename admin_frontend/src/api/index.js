import axios from 'axios'
import router from '../router'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  timeout: 60000
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use((response) => response, (error) => {
  if (error.response && error.response.status === 401) {
    localStorage.removeItem('token')
    localStorage.removeItem('role')
    localStorage.removeItem('username')
    window.location.href = '/login'
  }
  return Promise.reject(error)
})

export default {
  login: (username, password) => {
    const formData = new URLSearchParams()
    formData.append('username', username)
    formData.append('password', password)
    return api.post('/auth/login', formData)
  },
  getMe: () => api.get('/auth/me'),
  ingestClue: (data) => api.post('/ingest', data),
  getClue: (id) => api.get(`/clues/${id}`),
  listClues: (params) => api.get('/clues', { params }),
  judgeClue: (id) => api.post(`/clues/${id}/judge`),
  pushTask: (id, payload) => api.post(`/clues/${id}/push_task`, payload),
  feedbackTask: (taskId, payload) => api.post(`/tasks/${taskId}/feedback`, payload), // Legacy, might still exist or we should use new synergy one
  synergyReply: (id, payload) => api.post(`/clues/${id}/synergy_reply`, payload),
  decision: (id, payload) => api.post(`/clues/${id}/decision`, payload),
  resolveClue: (id) => api.post(`/clues/${id}/resolve`),
  getStats: () => api.get('/stats'),
  getLogs: () => api.get('/logs'),
  uploadDoc: (formData) => api.post('/upload_doc', formData, {headers:{'Content-Type': 'multipart/form-data'}}),
  analyze: (data) => api.post('/analyze', data),
  getUnreadNotifications: () => api.get('/notifications/unread'),

  markNotificationsRead: () => api.post('/notifications/read'),
  
  getSettings: () => api.get('/settings'),
  updateSettings: (configs) => api.post('/settings', { configs }),
  changePassword: (old_password, new_password) => api.post('/auth/change_password', { old_password, new_password }),
  updateApiKey: (key) => api.post('/system/update_api_key', { key }),
  getConfigInfo: () => api.get('/system/config_info')
}
