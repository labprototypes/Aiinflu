interface ProjectCardProps {
  project: {
    id: string
    blogger?: { name: string; frontal_image_url?: string }
    status: string
    current_step: number
    scenario_text?: string
    created_at: string
  }
  onContinue: () => void
  onDelete: (e: React.MouseEvent) => void
}

export default function ProjectCard({ project, onContinue, onDelete }: ProjectCardProps) {
  const getStatusColor = (status: string) => {
    const colors = {
      draft: 'bg-gray-600',
      in_progress: 'bg-blue-600',
      completed: 'bg-green-600',
    }
    return colors[status as keyof typeof colors] || 'bg-gray-600'
  }

  return (
    <div
      onClick={onContinue}
      className="glass-card p-6 hover:bg-white/10 transition-smooth cursor-pointer group"
    >
      <div className="flex items-center gap-4 mb-4">
        {project.blogger?.frontal_image_url && (
          <img
            src={project.blogger.frontal_image_url}
            alt={project.blogger.name}
            className="w-16 h-16 rounded-lg object-cover"
          />
        )}
        <div className="flex-1">
          <h3 className="font-bold text-lg">{project.blogger?.name || 'Без блогера'}</h3>
          <div className={`inline-block px-2 py-1 rounded text-xs mt-1 ${getStatusColor(project.status)}`}>
            Этап {project.current_step}/6
          </div>
        </div>
        <button
          onClick={onDelete}
          className="p-2 hover:bg-red-600/20 rounded-lg transition-smooth opacity-0 group-hover:opacity-100"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" />
          </svg>
        </button>
      </div>

      {project.scenario_text && (
        <p className="text-sm text-white/60 line-clamp-2 mb-3">{project.scenario_text}</p>
      )}

      <div className="w-full bg-white/5 rounded-full h-2">
        <div
          className="bg-blue-600 h-2 rounded-full transition-smooth"
          style={{ width: `${(project.current_step / 6) * 100}%` }}
        />
      </div>

      <p className="text-xs text-white/40 mt-3">
        {new Date(project.created_at).toLocaleDateString('ru-RU')}
      </p>
    </div>
  )
}
