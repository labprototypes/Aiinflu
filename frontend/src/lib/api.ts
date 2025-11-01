import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Blogger API
export const bloggersApi = {
  getAll: () => api.get('/bloggers'),
  getById: (id: string) => api.get(`/bloggers/${id}`),
  create: (formData: FormData) => api.post('/bloggers', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  update: (id: string, formData: FormData) => api.put(`/bloggers/${id}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  delete: (id: string) => api.delete(`/bloggers/${id}`),
}

// Projects API
export const projectsApi = {
  getAll: () => api.get('/projects'),
  getById: (id: string) => api.get(`/projects/${id}`),
  create: (data: { blogger_id: string }) => api.post('/projects', data),
  update: (id: string, data: any) => api.put(`/projects/${id}`, data),
  delete: (id: string) => api.delete(`/projects/${id}`),
  extractText: (id: string) => api.post(`/projects/${id}/extract-text`),
  generateAudio: (id: string) => api.post(`/projects/${id}/generate-audio`),
  uploadMaterial: (id: string, file: File, type: string) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('type', type)
    return api.post(`/projects/${id}/upload-material`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  analyzeMaterials: (id: string) => api.post(`/projects/${id}/analyze-materials`),
  searchTMDB: (id: string, title: string, titleSecondary?: string) =>
    api.post(`/projects/${id}/search-tmdb`, { title, title_secondary: titleSecondary }),
  generateTimeline: (id: string) => api.post(`/projects/${id}/generate-timeline`),
}

// ElevenLabs API
export const elevenLabsApi = {
  listVoices: () => api.get('/elevenlabs/voices'),
}

export default api
