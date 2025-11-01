export default function CreatePage() {
  return (
    <div className="animate-fade-in">
      <div className="mb-8">
        <h2 className="text-3xl font-bold mb-2">Создание контента</h2>
        <p className="text-white/60">6-этапный процесс создания видео с AI</p>
      </div>

      {/* Stepper будет добавлен в следующих коммитах */}
      <div className="glass-card p-12 text-center">
        <div className="text-white/40">
          <PlusCircleIcon size={64} className="mx-auto mb-4 opacity-20" />
          <p className="text-lg">Выберите блогера для начала работы</p>
          <p className="text-sm mt-2">Этапы: Подготовка → Озвучка → Материалы → Тайминги → Генерация → Монтаж</p>
        </div>
      </div>
    </div>
  )
}

function PlusCircleIcon({ size, className }: { size: number; className?: string }) {
  return (
    <svg width={size} height={size} className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="10" />
      <path d="M12 8v8M8 12h8" />
    </svg>
  )
}
