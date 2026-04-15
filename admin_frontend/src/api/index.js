import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api',
  timeout: 60000
})

export default {
  createClue: (data) => api.post('/clues', data),
  getClue: (id) => api.get(`/clues/${id}`),
  listClues: (params) => api.get('/clues', { params }),
  judgeClue: (id) => api.post(`/clues/${id}/judge`),
  pushClue: (id, department) => api.post(`/clues/${id}/push`, { department }),
  resolveClue: (id, feedback) => api.post(`/clues/${id}/resolve`, { feedback }),
  getStats: () => api.get('/stats'),
  chat: (question, context, history) => api.post('/chat', { question, context, history })
}
