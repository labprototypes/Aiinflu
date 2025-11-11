import { useState, useEffect } from 'react'
import { X, Loader2 } from 'lucide-react'
import type { Blogger, Location } from '@/types'
import { bloggersApi } from '@/lib/api'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import ImageDropzone from './ImageDropzone'
import LocationManager from './LocationManager'

interface BloggerModalProps {
  blogger?: Blogger | null
  isOpen: boolean
  onClose: () => void
}

export default function BloggerModal({ blogger, isOpen, onClose }: BloggerModalProps) {
  const queryClient = useQueryClient()
  const [formData, setFormData] = useState({
    name: '',
    type: 'podcaster',
    tone_of_voice: '',
    elevenlabs_voice_id: '',
    heygen_avatar_id: '00000',
  })
  const [frontalImage, setFrontalImage] = useState<File | null>(null)
  const [frontalPreview, setFrontalPreview] = useState<string>('')
  const [locations, setLocations] = useState<Location[]>([])
  const [isLoadingLocations, setIsLoadingLocations] = useState(false)

  // Track if modal was just opened to prevent overwriting local state
  const [modalJustOpened, setModalJustOpened] = useState(false)

  // Sync form data when modal opens (but not on every render)
  useEffect(() => {
    if (isOpen) {
      setModalJustOpened(true)
      if (blogger) {
        setFormData({
          name: blogger.name || '',
          type: blogger.type || 'podcaster',
          tone_of_voice: blogger.tone_of_voice || '',
          elevenlabs_voice_id: blogger.elevenlabs_voice_id || '',
          heygen_avatar_id: blogger.heygen_avatar_id || '00000',
        })
        setFrontalPreview(blogger.frontal_image_url || '')
        setLocations(blogger.locations || [])
        // Reset file inputs when editing
        setFrontalImage(null)
      } else {
        // Reset form for creating new blogger
        setFormData({
          name: '',
          type: 'podcaster',
          tone_of_voice: '',
          elevenlabs_voice_id: '',
          heygen_avatar_id: '00000',
        })
        setFrontalPreview('')
        setLocations([])
        setFrontalImage(null)
      }
    } else {
      setModalJustOpened(false)
    }
    // Only run when modal opens/closes, not when blogger changes
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen])

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

  const handleImageChange = (file: File) => {
    setFrontalImage(file)
    setFrontalPreview(URL.createObjectURL(file))
  }

  const handleImageClear = () => {
    setFrontalImage(null)
    setFrontalPreview('')
  }

  // Location management functions
  const handleAddLocation = async (file: File, name: string, heygenAvatarId: string) => {
    if (!blogger) return
    
    const formData = new FormData()
    formData.append('image', file)
    formData.append('name', name)
    formData.append('heygen_avatar_id', heygenAvatarId)
    
    const response = await bloggersApi.addLocation(blogger.id, formData)
    // Backend returns full blogger object with updated locations array
    setLocations(response.data.locations || [])
    queryClient.invalidateQueries({ queryKey: ['bloggers'] })
  }

  const handleUpdateLocation = async (locationId: number, data: { name?: string; heygen_avatar_id?: string }) => {
    if (!blogger) return
    
    const response = await bloggersApi.updateLocation(blogger.id, locationId, data)
    // Backend returns full blogger object with updated locations array
    setLocations(response.data.locations || [])
    queryClient.invalidateQueries({ queryKey: ['bloggers'] })
  }

  const handleDeleteLocation = async (locationId: number) => {
    if (!blogger) return
    
    const response = await bloggersApi.deleteLocation(blogger.id, locationId)
    // Backend returns full blogger object with updated locations array
    setLocations(response.data.locations || [])
    queryClient.invalidateQueries({ queryKey: ['bloggers'] })
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    const data = new FormData()
    data.append('name', formData.name)
    data.append('type', formData.type)
    data.append('tone_of_voice', formData.tone_of_voice)
    data.append('elevenlabs_voice_id', formData.elevenlabs_voice_id)
    data.append('heygen_avatar_id', formData.heygen_avatar_id)
    
    // If editing and image was cleared (preview is empty but blogger had image)
    if (blogger) {
      if (!frontalPreview && blogger.frontal_image_url) {
        data.append('clear_frontal_image', 'true')
      }
    }
    
    // Add new image if selected
    if (frontalImage) data.append('frontal_image', frontalImage)
    
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
          <ImageDropzone
            label="Фронтальное изображение"
            value={frontalPreview}
            onChange={handleImageChange}
            onClear={handleImageClear}
            disabled={mutation.isPending}
          />

          {/* HeyGen Avatar ID for frontal image */}
          <div>
            <label className="block text-sm font-medium mb-2">HeyGen Avatar ID (для фронтального фото)</label>
            <input
              type="text"
              value={formData.heygen_avatar_id}
              onChange={(e) => setFormData({ ...formData, heygen_avatar_id: e.target.value })}
              className="input-glass font-mono"
              placeholder="00000"
            />
            <p className="text-xs text-white/40 mt-1">
              Получите Avatar ID в{' '}
              <a
                href="https://app.heygen.com/avatars"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-400 hover:text-blue-300"
              >
                HeyGen Dashboard
              </a>
            </p>
          </div>

          {/* Location Manager - only show when editing existing blogger */}
          {blogger && (
            <LocationManager
              bloggerId={blogger.id}
              locations={locations}
              onAdd={handleAddLocation}
              onUpdate={handleUpdateLocation}
              onDelete={handleDeleteLocation}
            />
          )}

          {!blogger && (
            <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
              <p className="text-sm text-blue-200">
                💡 Сначала создайте блогера, затем вы сможете добавить множественные локации с индивидуальными HeyGen Avatar ID.
              </p>
            </div>
          )}

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
