import { Plus } from 'lucide-react'

export default function BloggersPage() {
  return (
    <div className="animate-fade-in">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-3xl font-bold mb-2">Блогеры</h2>
          <p className="text-white/60">Управление подкастерами и создателями контента</p>
        </div>
        
        <button className="btn-primary flex items-center gap-2">
          <Plus size={20} />
          Создать блогера
        </button>
      </div>

      {/* Blogger cards grid - будет добавлено в следующих коммитах */}
      <div className="glass-card p-12 text-center">
        <div className="text-white/40 mb-4">
          <Users size={64} className="mx-auto mb-4 opacity-20" />
          <p className="text-lg">Блогеры появятся здесь</p>
          <p className="text-sm mt-2">Создайте первого блогера, чтобы начать</p>
        </div>
      </div>
    </div>
  )
}

function Users({ size, className }: { size: number; className?: string }) {
  return (
    <svg width={size} height={size} className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  )
}
