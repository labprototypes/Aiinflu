import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Loader2, Trash2, Clock, CheckCircle, PlayCircle, Download } from 'lucide-react'
import { projectsApi } from '@/lib/api'
import { Project } from '@/types'

export default function ProjectsPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data: projects, isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: async () => {
      const response = await projectsApi.getAll()
      return response.data as Project[]
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => projectsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })

  const handleDelete = (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (confirm('Удалить проект? Это действие нельзя отменить.')) {
      deleteMutation.mutate(id)
    }
  }

  const handleContinue = (project: Project) => {
    navigate('/create', { state: { projectId: project.id } })
  }

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      draft: { label: 'Черновик', color: 'bg-gray-600' },
      in_progress: { label: 'В процессе', color: 'bg-blue-600' },
      completed: { label: 'Завершён', color: 'bg-green-600' },
    }
    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.draft
    return (
      <span className={`px-2 py-1 rounded text-xs font-medium ${config.color}`}>
        {config.label}
      </span>
    )
  }

  const getStepLabel = (step: number) => {
    const steps = [
      'Не начат',
      'Подготовка',
      'Озвучка',
      'Материалы',
      'Тайминги',
      'Генерация',
      'Монтаж',
    ]
    return steps[step] || 'Неизвестно'
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 size={48} className="animate-spin text-white/40" />
      </div>
    )
  }

  return (
    <div className="animate-fade-in">
      <div className="mb-8">
        <h2 className="text-3xl font-bold mb-2">Проекты</h2>
        <p className="text-white/60">История всех созданных видео</p>
      </div>

      {!projects || projects.length === 0 ? (
        <div className="glass-card p-12 text-center">
          <div className="text-white/40">
            <PlayCircle size={64} className="mx-auto mb-4 opacity-20" />
            <p className="text-lg">Нет проектов</p>
            <p className="text-sm mt-2">Создайте первый проект во вкладке "Создание контента"</p>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {projects.map((project) => (
            <div
              key={project.id}
              className="glass-card p-6 hover:bg-white/10 transition-smooth cursor-pointer group"
              onClick={() => handleContinue(project)}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-xl font-bold">
                      {project.blogger?.name || 'Без блогера'}
                    </h3>
                    {getStatusBadge(project.status)}
                  </div>
                  <p className="text-sm text-white/60">
                    Этап: {getStepLabel(project.current_step)} ({project.current_step}/6)
                  </p>
                </div>

                <button
                  onClick={(e) => handleDelete(project.id, e)}
                  className="p-2 hover:bg-red-600/20 rounded-lg transition-smooth opacity-0 group-hover:opacity-100"
                >
                  <Trash2 size={20} className="text-red-400" />
                </button>
              </div>

              {/* Progress bar */}
              <div className="w-full bg-white/5 rounded-full h-2 mb-4">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-smooth"
                  style={{ width: `${(project.current_step / 6) * 100}%` }}
                />
              </div>

              {/* Scenario preview */}
              {project.scenario_text && (
                <p className="text-sm text-white/60 line-clamp-2 mb-3">
                  {project.scenario_text}
                </p>
              )}

              {/* Media previews */}
              <div className="flex gap-3 items-center">
                {project.audio_url && (
                  <div className="flex items-center gap-2 text-xs text-white/60">
                    <div className="w-2 h-2 rounded-full bg-green-500" />
                    Аудио
                  </div>
                )}
                {project.materials && project.materials.length > 0 && (
                  <div className="flex items-center gap-2 text-xs text-white/60">
                    <div className="w-2 h-2 rounded-full bg-blue-500" />
                    Материалы: {project.materials.length}
                  </div>
                )}
                {project.avatar_video_url && (
                  <div className="flex items-center gap-2 text-xs text-white/60">
                    <div className="w-2 h-2 rounded-full bg-purple-500" />
                    Аватар
                  </div>
                )}
                {project.final_video_url && (
                  <div className="flex items-center gap-2 text-xs text-green-400">
                    <CheckCircle size={16} />
                    Готово
                  </div>
                )}
              </div>

              {/* Final video download */}
              {project.final_video_url && (
                <div className="mt-4 pt-4 border-t border-white/10">
                  <a
                    href={project.final_video_url}
                    download
                    onClick={(e) => e.stopPropagation()}
                    className="btn-primary w-full flex items-center justify-center gap-2"
                  >
                    <Download size={20} />
                    Скачать финальное видео
                  </a>
                </div>
              )}

              {/* Timestamps */}
              <div className="mt-4 pt-4 border-t border-white/10 flex items-center justify-between text-xs text-white/40">
                <div className="flex items-center gap-2">
                  <Clock size={14} />
                  Создан: {new Date(project.created_at).toLocaleDateString('ru-RU')}
                </div>
                <div>
                  Обновлён: {new Date(project.updated_at).toLocaleDateString('ru-RU')}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
