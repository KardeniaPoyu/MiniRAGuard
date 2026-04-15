import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api',
  timeout: 60000
})

export default {
  ingestClue: (data) => api.post('/ingest', data),
  getClue: (id) => api.get(`/clues/${id}`),
  listClues: (params) => api.get('/clues', { params }),
  judgeClue: (id) => api.post(`/clues/${id}/judge`),
  pushTask: (id, payload) => api.post(`/clues/${id}/push_task`, payload),
  feedbackTask: (taskId, payload) => api.post(`/tasks/${taskId}/feedback`, payload),
  resolveClue: (id) => api.post(`/clues/${id}/resolve`),
  getStats: () => api.get('/stats'),
}
