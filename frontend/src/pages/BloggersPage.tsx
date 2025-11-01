import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Loader2, Plus, UserPlus } from 'lucide-react'
import { bloggersApi } from '@/lib/api'
import type { Blogger } from '@/types'
import BloggerCard from '@/components/BloggerCard'
import BloggerModal from '@/components/BloggerModal'

export default function BloggersPage() {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [selectedBlogger, setSelectedBlogger] = useState<Blogger | null>(null)
  const queryClient = useQueryClient()

  const { data: bloggers, isLoading } = useQuery({
    queryKey: ['bloggers'],
    queryFn: async () => {
      const response = await bloggersApi.getAll()
      return response.data as Blogger[]
    },
  })

  const deleteMutation = useMutation({
    mutationFn: bloggersApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bloggers'] })
    },
  })

  const handleEdit = (blogger: Blogger) => {
    setSelectedBlogger(blogger)
    setIsModalOpen(true)
  }

  const handleDelete = (id: string) => {
    if (confirm('Удалить блогера?')) {
      deleteMutation.mutate(id)
    }
  }

  const handleCreate = () => {
    setSelectedBlogger(null)
    setIsModalOpen(true)
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
    setSelectedBlogger(null)
  }

  return (
    <div className="animate-fade-in">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-3xl font-bold mb-2">Блогеры</h2>
          <p className="text-white/60">Управление подкастерами и создателями контента</p>
        </div>
        
        <button onClick={handleCreate} className="btn-primary flex items-center gap-2">
          <Plus size={20} />
          Создать блогера
        </button>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="glass-card p-12 text-center">
          <Loader2 size={48} className="mx-auto mb-4 animate-spin text-blue-500" />
          <p className="text-white/60">Загрузка блогеров...</p>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && (!bloggers || bloggers.length === 0) && (
        <div className="glass-card p-12 text-center">
          <div className="text-white/40 mb-4">
            <Users size={64} className="mx-auto mb-4 opacity-20" />
            <p className="text-lg">Блогеры появятся здесь</p>
            <p className="text-sm mt-2">Создайте первого блогера, чтобы начать</p>
          </div>
        </div>
      )}

      {/* Blogger cards grid */}
      {!isLoading && bloggers && bloggers.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {bloggers.map((blogger) => (
            <BloggerCard
              key={blogger.id}
              blogger={blogger}
              onEdit={handleEdit}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}

      {/* Modal */}
      <BloggerModal
        blogger={selectedBlogger}
        isOpen={isModalOpen}
        onClose={handleCloseModal}
      />
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
