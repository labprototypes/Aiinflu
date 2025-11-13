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
  // Location management
  addLocation: (bloggerId: string, formData: FormData) => 
    api.post(`/bloggers/${bloggerId}/locations`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }),
  updateLocation: (bloggerId: string, locationId: number, data: { name?: string; heygen_avatar_id?: string }) =>
    api.put(`/bloggers/${bloggerId}/locations/${locationId}`, data),
  deleteLocation: (bloggerId: string, locationId: number) =>
    api.delete(`/bloggers/${bloggerId}/locations/${locationId}`),
}

// Projects API
export const projectsApi = {
  getAll: () => api.get('/projects'),
  getById: (id: string) => api.get(`/projects/${id}`),
  create: (data: { blogger_id: string }) => api.post('/projects', data),
  update: (id: string, data: any) => api.put(`/projects/${id}`, data),
  updateStep: (id: string, step: number) => api.put(`/projects/${id}`, { current_step: step }),
  delete: (id: string) => api.delete(`/projects/${id}`),
  extractText: (id: string) => api.post(`/projects/${id}/extract-text`),
  extractAndAnalyze: (id: string) => api.post(`/projects/${id}/extract-and-analyze`),
  generateAudio: (id: string) => api.post(`/projects/${id}/generate-audio`),
  uploadMaterial: (id: string, file: File, type: string) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('type', type)
    return api.post(`/projects/${id}/upload-material`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  deleteMaterial: (projectId: string, materialId: string) =>
    api.delete(`/projects/${projectId}/materials/${materialId}`),
  analyzeMaterials: (id: string) => api.post(`/projects/${id}/analyze-materials`),
  generateTimeline: (id: string) => api.post(`/projects/${id}/generate-timeline`),
  generateAvatarVideo: (id: string, params?: { expression_scale?: number; face_enhance?: boolean }) =>
    api.post(`/projects/${id}/generate-avatar-video`, params),
  checkAvatarStatus: (id: string, requestId: string) =>
    api.get(`/projects/${id}/check-avatar-status/${requestId}`),
  composeFinalVideo: (id: string, options?: { add_subtitles?: boolean; advanced_composition?: boolean }) =>
    api.post(`/projects/${id}/compose-final-video`, options),
}

// ElevenLabs API
export const elevenLabsApi = {
  listVoices: () => api.get('/elevenlabs/voices'),
}

export default api
