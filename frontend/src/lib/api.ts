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
  // More endpoints will be added in future commits
}

export default api
