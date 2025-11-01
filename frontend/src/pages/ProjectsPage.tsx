export default function ProjectsPage() {
  return (
    <div className="animate-fade-in">
      <div className="mb-8">
        <h2 className="text-3xl font-bold mb-2">Проекты</h2>
        <p className="text-white/60">История всех созданных видео</p>
      </div>

      {/* Project list будет добавлен в следующих коммитах */}
      <div className="glass-card p-12 text-center">
        <div className="text-white/40">
          <FolderIcon size={64} className="mx-auto mb-4 opacity-20" />
          <p className="text-lg">Проекты появятся здесь</p>
          <p className="text-sm mt-2">Создайте первый проект во вкладке "Создание"</p>
        </div>
      </div>
    </div>
  )
}

function FolderIcon({ size, className }: { size: number; className?: string }) {
  return (
    <svg width={size} height={size} className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
    </svg>
  )
}
