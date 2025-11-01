import type { Blogger } from '@/types'
import { Pencil, Trash2, User } from 'lucide-react'

interface BloggerCardProps {
  blogger: Blogger
  onEdit: (blogger: Blogger) => void
  onDelete: (id: string) => void
}

export default function BloggerCard({ blogger, onEdit, onDelete }: BloggerCardProps) {
  return (
    <div className="glass-card p-4 hover:bg-white/15 transition-smooth group">
      {/* Image */}
      <div className="relative mb-4 rounded-xl overflow-hidden">
        {blogger.frontal_image_url ? (
          <img
            src={blogger.frontal_image_url}
            alt={blogger.name}
            className="w-full h-48 object-cover"
          />
        ) : (
          <div className="w-full h-48 bg-white/5 flex items-center justify-center">
            <User size={48} className="text-white/20" />
          </div>
        )}
        
        {/* Type badge */}
        <div className="absolute top-2 right-2 px-3 py-1 bg-blue-600/90 backdrop-blur-sm rounded-lg text-xs font-medium">
          {blogger.type === 'podcaster' ? 'Подкастер' : blogger.type}
        </div>
      </div>

      {/* Info */}
      <div className="mb-4">
        <h3 className="text-lg font-bold mb-1">{blogger.name}</h3>
        {blogger.tone_of_voice && (
          <p className="text-sm text-white/60 line-clamp-2">{blogger.tone_of_voice}</p>
        )}
        {blogger.elevenlabs_voice_id && (
          <p className="text-xs text-white/40 mt-2">Voice: {blogger.elevenlabs_voice_id}</p>
        )}
      </div>

      {/* Actions */}
      <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-smooth">
        <button
          onClick={() => onEdit(blogger)}
          className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium transition-smooth flex items-center justify-center gap-2"
        >
          <Pencil size={16} />
          Редактировать
        </button>
        <button
          onClick={() => onDelete(blogger.id)}
          className="px-4 py-2 bg-red-600/80 hover:bg-red-600 rounded-lg text-sm font-medium transition-smooth"
        >
          <Trash2 size={16} />
        </button>
      </div>
    </div>
  )
}

function UserIcon({ size, className }: { size: number; className?: string }) {
  return (
    <svg width={size} height={size} className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
      <circle cx="12" cy="7" r="4" />
    </svg>
  )
}
