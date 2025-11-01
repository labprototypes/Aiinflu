import { useState } from 'react'
import { X, Upload, Loader2 } from 'lucide-react'
import { Blogger } from '@/types'
import { bloggersApi } from '@/lib/api'
import { useMutation, useQueryClient } from '@tanstack/react-query'

interface BloggerModalProps {
  blogger?: Blogger | null
  isOpen: boolean
  onClose: () => void
}

export default function BloggerModal({ blogger, isOpen, onClose }: BloggerModalProps) {
  const queryClient = useQueryClient()
  const [formData, setFormData] = useState({
    name: blogger?.name || '',
    type: blogger?.type || 'podcaster',
    tone_of_voice: blogger?.tone_of_voice || '',
    elevenlabs_voice_id: blogger?.elevenlabs_voice_id || '',
  })
  const [frontalImage, setFrontalImage] = useState<File | null>(null)
  const [locationImage, setLocationImage] = useState<File | null>(null)
  const [frontalPreview, setFrontalPreview] = useState<string>(blogger?.frontal_image_url || '')
  const [locationPreview, setLocationPreview] = useState<string>(blogger?.location_image_url || '')

  const mutation = useMutation({
    mutationFn: async (data: FormData) => {
      if (blogger) {
        return bloggersApi.update(blogger.id, data)
      }
      return bloggersApi.create(data)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bloggers'] })
      onClose()
    },
  })

  const handleImageChange = (
    e: React.ChangeEvent<HTMLInputElement>,
    type: 'frontal' | 'location'
  ) => {
    const file = e.target.files?.[0]
    if (file) {
      if (type === 'frontal') {
        setFrontalImage(file)
        setFrontalPreview(URL.createObjectURL(file))
      } else {
        setLocationImage(file)
        setLocationPreview(URL.createObjectURL(file))
      }
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    const data = new FormData()
    data.append('name', formData.name)
    data.append('type', formData.type)
    data.append('tone_of_voice', formData.tone_of_voice)
    data.append('elevenlabs_voice_id', formData.elevenlabs_voice_id)
    
    if (frontalImage) data.append('frontal_image', frontalImage)
    if (locationImage) data.append('location_image', locationImage)
    
    mutation.mutate(data)
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="glass-card max-w-2xl w-full max-h-[90vh] overflow-y-auto animate-slide-up">
        <div className="sticky top-0 glass-card border-b border-white/10 px-6 py-4 flex justify-between items-center">
          <h2 className="text-2xl font-bold">
            {blogger ? 'Редактировать блогера' : 'Создать блогера'}
          </h2>
          <button onClick={onClose} className="text-white/60 hover:text-white transition-smooth">
            <X size={24} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Name */}
          <div>
            <label className="block text-sm font-medium mb-2">Имя блогера</label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="input-glass"
              placeholder="Введите имя..."
            />
          </div>

          {/* Type */}
          <div>
            <label className="block text-sm font-medium mb-2">Тип</label>
            <select
              value={formData.type}
              onChange={(e) => setFormData({ ...formData, type: e.target.value })}
              className="input-glass"
            >
              <option value="podcaster">Подкастер</option>
              <option value="youtuber">Ютубер</option>
              <option value="blogger">Блогер</option>
            </select>
          </div>

          {/* Frontal Image */}
          <div>
            <label className="block text-sm font-medium mb-2">Фронтальное изображение</label>
            <div className="glass-card p-4">
              {frontalPreview ? (
                <div className="relative">
                  <img src={frontalPreview} alt="Preview" className="w-full h-48 object-cover rounded-lg" />
                  <button
                    type="button"
                    onClick={() => {
                      setFrontalImage(null)
                      setFrontalPreview('')
                    }}
                    className="absolute top-2 right-2 bg-red-500 text-white p-2 rounded-lg hover:bg-red-600"
                  >
                    <X size={16} />
                  </button>
                </div>
              ) : (
                <label className="cursor-pointer flex flex-col items-center justify-center h-48 border-2 border-dashed border-white/20 rounded-lg hover:border-white/40 transition-smooth">
                  <Upload size={32} className="text-white/40 mb-2" />
                  <span className="text-white/60">Нажмите для загрузки</span>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={(e) => handleImageChange(e, 'frontal')}
                    className="hidden"
                  />
                </label>
              )}
            </div>
          </div>

          {/* Location Image */}
          <div>
            <label className="block text-sm font-medium mb-2">Блогер в локации</label>
            <div className="glass-card p-4">
              {locationPreview ? (
                <div className="relative">
                  <img src={locationPreview} alt="Preview" className="w-full h-48 object-cover rounded-lg" />
                  <button
                    type="button"
                    onClick={() => {
                      setLocationImage(null)
                      setLocationPreview('')
                    }}
                    className="absolute top-2 right-2 bg-red-500 text-white p-2 rounded-lg hover:bg-red-600"
                  >
                    <X size={16} />
                  </button>
                </div>
              ) : (
                <label className="cursor-pointer flex flex-col items-center justify-center h-48 border-2 border-dashed border-white/20 rounded-lg hover:border-white/40 transition-smooth">
                  <Upload size={32} className="text-white/40 mb-2" />
                  <span className="text-white/60">Нажмите для загрузки</span>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={(e) => handleImageChange(e, 'location')}
                    className="hidden"
                  />
                </label>
              )}
            </div>
          </div>

          {/* Tone of Voice */}
          <div>
            <label className="block text-sm font-medium mb-2">Tone of Voice</label>
            <textarea
              value={formData.tone_of_voice}
              onChange={(e) => setFormData({ ...formData, tone_of_voice: e.target.value })}
              className="input-glass min-h-[100px] resize-none"
              placeholder="Опишите стиль и тон блогера..."
            />
          </div>

          {/* ElevenLabs Voice ID */}
          <div>
            <label className="block text-sm font-medium mb-2">ElevenLabs Voice ID</label>
            <input
              type="text"
              value={formData.elevenlabs_voice_id}
              onChange={(e) => setFormData({ ...formData, elevenlabs_voice_id: e.target.value })}
              className="input-glass"
              placeholder="Введите Voice ID..."
            />
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-4">
            <button
              type="submit"
              disabled={mutation.isPending}
              className="btn-primary flex-1 flex items-center justify-center gap-2"
            >
              {mutation.isPending && <Loader2 size={20} className="animate-spin" />}
              {blogger ? 'Сохранить' : 'Создать'}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="btn-secondary"
            >
              Отмена
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
