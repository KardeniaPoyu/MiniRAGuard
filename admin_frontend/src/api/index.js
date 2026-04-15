import axios from 'axios'
import router from '../router'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api',
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
  feedbackTask: (taskId, payload) => api.post(`/tasks/${taskId}/feedback`, payload),
  resolveClue: (id) => api.post(`/clues/${id}/resolve`),
  getStats: () => api.get('/stats'),
  getLogs: () => api.get('/logs')
}
