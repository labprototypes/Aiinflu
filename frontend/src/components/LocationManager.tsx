import { useState } from 'react'
import { Plus, Trash2, Edit2, Save, X } from 'lucide-react'
import type { Location } from '@/types'
import ImageDropzone from './ImageDropzone'

interface LocationManagerProps {
  bloggerId: string
  locations: Location[]
  onAdd: (file: File, name: string, heygenAvatarId: string) => Promise<void>
  onUpdate: (locationId: number, data: { name?: string; heygen_avatar_id?: string }) => Promise<void>
  onDelete: (locationId: number) => Promise<void>
}

export default function LocationManager({ 
  bloggerId,
  locations, 
  onAdd, 
  onUpdate, 
  onDelete 
}: LocationManagerProps) {
  const [isAdding, setIsAdding] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  
  // New location form
  const [newLocationFile, setNewLocationFile] = useState<File | null>(null)
  const [newLocationPreview, setNewLocationPreview] = useState<string>('')
  const [newLocationName, setNewLocationName] = useState('')
  const [newLocationAvatarId, setNewLocationAvatarId] = useState('00000')
  
  // Edit form
  const [editName, setEditName] = useState('')
  const [editAvatarId, setEditAvatarId] = useState('')

  const handleStartAdd = () => {
    setIsAdding(true)
    setNewLocationFile(null)
    setNewLocationPreview('')
    setNewLocationName(`Локация ${locations.length + 1}`)
    setNewLocationAvatarId('00000')
  }

  const handleCancelAdd = () => {
    setIsAdding(false)
    setNewLocationFile(null)
    setNewLocationPreview('')
    setNewLocationName('')
    setNewLocationAvatarId('00000')
  }

  const handleImageChange = (file: File) => {
    setNewLocationFile(file)
    setNewLocationPreview(URL.createObjectURL(file))
  }

  const handleAddSubmit = async () => {
    if (!newLocationFile || !newLocationName || !newLocationAvatarId) return
    
    try {
      await onAdd(newLocationFile, newLocationName, newLocationAvatarId)
      handleCancelAdd()
    } catch (error) {
      console.error('Failed to add location:', error)
    }
  }

  const handleStartEdit = (location: Location) => {
    setEditingId(location.id)
    setEditName(location.name)
    setEditAvatarId(location.heygen_avatar_id)
  }

  const handleCancelEdit = () => {
    setEditingId(null)
    setEditName('')
    setEditAvatarId('')
  }

  const handleEditSubmit = async (locationId: number) => {
    try {
      await onUpdate(locationId, {
        name: editName,
        heygen_avatar_id: editAvatarId,
      })
      handleCancelEdit()
    } catch (error) {
      console.error('Failed to update location:', error)
    }
  }

  const handleDelete = async (locationId: number) => {
    if (!confirm('Удалить эту локацию? Это действие нельзя отменить.')) return
    
    try {
      await onDelete(locationId)
    } catch (error) {
      console.error('Failed to delete location:', error)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <label className="block text-sm font-medium">Блогер в локации</label>
        {!isAdding && (
          <button
            type="button"
            onClick={handleStartAdd}
            className="btn-secondary text-sm flex items-center gap-2"
          >
            <Plus size={16} />
            Добавить локацию
          </button>
        )}
      </div>

      {/* Existing locations */}
      <div className="space-y-3">
        {locations.map((location) => (
          <div
            key={location.id}
            className="glass-card p-4 flex gap-4"
          >
            {/* Image preview */}
            <div className="flex-shrink-0">
              <img
                src={location.image_url}
                alt={location.name}
                className="w-24 h-24 object-cover rounded-lg"
              />
            </div>

            {/* Location details */}
            <div className="flex-1 space-y-2">
              {editingId === location.id ? (
                <>
                  <input
                    type="text"
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    className="input-glass text-sm"
                    placeholder="Название локации"
                  />
                  <input
                    type="text"
                    value={editAvatarId}
                    onChange={(e) => setEditAvatarId(e.target.value)}
                    className="input-glass text-sm font-mono"
                    placeholder="HeyGen Avatar ID"
                  />
                </>
              ) : (
                <>
                  <h4 className="font-bold">{location.name}</h4>
                  <div className="text-xs space-y-1">
                    <div className="text-white/60">
                      HeyGen Avatar ID:
                    </div>
                    <div className="font-mono bg-white/5 px-2 py-1 rounded inline-block">
                      {location.heygen_avatar_id || '00000'}
                    </div>
                    {(!location.heygen_avatar_id || location.heygen_avatar_id === '00000') && (
                      <div className="text-red-400 text-xs mt-1">
                        ⚠️ Avatar ID не настроен
                      </div>
                    )}
                  </div>
                </>
              )}
            </div>

            {/* Actions */}
            <div className="flex-shrink-0 flex flex-col gap-2">
              {editingId === location.id ? (
                <>
                  <button
                    type="button"
                    onClick={() => handleEditSubmit(location.id)}
                    className="p-2 bg-green-600/20 hover:bg-green-600/30 rounded transition-smooth"
                    title="Сохранить"
                  >
                    <Save size={16} />
                  </button>
                  <button
                    type="button"
                    onClick={handleCancelEdit}
                    className="p-2 bg-white/10 hover:bg-white/20 rounded transition-smooth"
                    title="Отмена"
                  >
                    <X size={16} />
                  </button>
                </>
              ) : (
                <>
                  <button
                    type="button"
                    onClick={() => handleStartEdit(location)}
                    className="p-2 bg-blue-600/20 hover:bg-blue-600/30 rounded transition-smooth"
                    title="Редактировать"
                  >
                    <Edit2 size={16} />
                  </button>
                  <button
                    type="button"
                    onClick={() => handleDelete(location.id)}
                    className="p-2 bg-red-600/20 hover:bg-red-600/30 rounded transition-smooth"
                    title="Удалить"
                  >
                    <Trash2 size={16} />
                  </button>
                </>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Add new location form */}
      {isAdding && (
        <div className="glass-card p-4 space-y-4 border-2 border-blue-500/30">
          <h4 className="font-bold text-sm">Новая локация</h4>
          
          <ImageDropzone
            label="Изображение локации"
            value={newLocationPreview}
            onChange={handleImageChange}
            onClear={() => {
              setNewLocationFile(null)
              setNewLocationPreview('')
            }}
          />

          <div>
            <label className="block text-xs font-medium mb-1">Название</label>
            <input
              type="text"
              value={newLocationName}
              onChange={(e) => setNewLocationName(e.target.value)}
              className="input-glass text-sm"
              placeholder="Например: Офис, Студия, Улица..."
            />
          </div>

          <div>
            <label className="block text-xs font-medium mb-1">HeyGen Avatar ID</label>
            <input
              type="text"
              value={newLocationAvatarId}
              onChange={(e) => setNewLocationAvatarId(e.target.value)}
              className="input-glass text-sm font-mono"
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

          <div className="flex gap-2">
            <button
              type="button"
              onClick={handleAddSubmit}
              disabled={!newLocationFile || !newLocationName}
              className="btn-primary flex-1 text-sm"
            >
              Добавить
            </button>
            <button
              type="button"
              onClick={handleCancelAdd}
              className="btn-secondary text-sm"
            >
              Отмена
            </button>
          </div>
        </div>
      )}

      {locations.length === 0 && !isAdding && (
        <div className="text-center py-6 text-white/40 text-sm">
          Локации не добавлены. Нажмите "Добавить локацию" чтобы начать.
        </div>
      )}
    </div>
  )
}
