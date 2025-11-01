import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Loader2, Play, Pause, Check, Upload, Film, Sparkles, Trash2 } from 'lucide-react'
import { bloggersApi, projectsApi } from '@/lib/api'
import { Blogger, Project } from '@/types'
import Stepper from '@/components/Stepper'

const STEPS = [
  { number: 1, title: 'Подготовка' },
  { number: 2, title: 'Озвучка' },
  { number: 3, title: 'Материалы' },
  { number: 4, title: 'Тайминги' },
  { number: 5, title: 'Генерация' },
  { number: 6, title: 'Монтаж' },
]

export default function CreatePage() {
  const [currentProject, setCurrentProject] = useState<Project | null>(null)
  const [selectedBlogger, setSelectedBlogger] = useState<string>('')
  const [scenario, setScenario] = useState('')
  const [voiceoverText, setVoiceoverText] = useState('')
  const [isPlaying, setIsPlaying] = useState(false)
  const [tmdbTitle, setTmdbTitle] = useState('')
  const [tmdbTitleSecondary, setTmdbTitleSecondary] = useState('')
  const queryClient = useQueryClient()

  const { data: bloggers } = useQuery({
    queryKey: ['bloggers'],
    queryFn: async () => {
      const response = await bloggersApi.getAll()
      return response.data as Blogger[]
    },
  })

  const createProjectMutation = useMutation({
    mutationFn: (blogger_id: string) => projectsApi.create({ blogger_id }),
    onSuccess: (response) => {
      setCurrentProject(response.data as Project)
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })

  const updateScenarioMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => projectsApi.update(id, data),
    onSuccess: (response) => {
      setCurrentProject(response.data as Project)
    },
  })

  const extractTextMutation = useMutation({
    mutationFn: (id: string) => projectsApi.extractText(id),
    onSuccess: (response) => {
      setVoiceoverText(response.data.voiceover_text)
      setCurrentProject(response.data.project)
    },
  })

  const generateAudioMutation = useMutation({
    mutationFn: (id: string) => projectsApi.generateAudio(id),
    onSuccess: (response) => {
      setCurrentProject(response.data.project)
    },
  })

  const uploadMaterialMutation = useMutation({
    mutationFn: ({ id, file, type }: { id: string; file: File; type: string }) =>
      projectsApi.uploadMaterial(id, file, type),
    onSuccess: (response) => {
      setCurrentProject(response.data.project)
    },
  })

  const analyzeMaterialsMutation = useMutation({
    mutationFn: (id: string) => projectsApi.analyzeMaterials(id),
    onSuccess: (response) => {
      setCurrentProject(response.data.project)
    },
  })

  const searchTMDBMutation = useMutation({
    mutationFn: ({ id, title, titleSecondary }: { id: string; title: string; titleSecondary?: string }) =>
      projectsApi.searchTMDB(id, title, titleSecondary),
    onSuccess: (response) => {
      setCurrentProject(response.data.project)
      setTmdbTitle('')
      setTmdbTitleSecondary('')
    },
  })

  const generateTimelineMutation = useMutation({
    mutationFn: (id: string) => projectsApi.generateTimeline(id),
    onSuccess: (response) => {
      setCurrentProject(response.data.project)
    },
  })

  const handleStartProject = () => {
    if (selectedBlogger) {
      createProjectMutation.mutate(selectedBlogger)
    }
  }

  const handleSaveScenario = () => {
    if (currentProject) {
      updateScenarioMutation.mutate({
        id: currentProject.id,
        data: { scenario_text: scenario, current_step: 1 },
      })
    }
  }

  const handleExtractText = () => {
    if (currentProject) {
      extractTextMutation.mutate(currentProject.id)
    }
  }

  const handleGenerateAudio = () => {
    if (currentProject) {
      generateAudioMutation.mutate(currentProject.id)
    }
  }

  const handleApproveVoiceover = () => {
    if (currentProject) {
      updateScenarioMutation.mutate({
        id: currentProject.id,
        data: { voiceover_text: voiceoverText, current_step: 2 },
      })
    }
  }

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0 && currentProject) {
      Array.from(files).forEach((file) => {
        const type = file.type.startsWith('image/') ? 'image' : 'video'
        uploadMaterialMutation.mutate({ id: currentProject.id, file, type })
      })
    }
  }

  const handleAnalyzeMaterials = () => {
    if (currentProject) {
      analyzeMaterialsMutation.mutate(currentProject.id)
    }
  }

  const handleSearchTMDB = () => {
    if (currentProject && tmdbTitle) {
      searchTMDBMutation.mutate({
        id: currentProject.id,
        title: tmdbTitle,
        titleSecondary: tmdbTitleSecondary || undefined,
      })
    }
  }

  const handleGenerateTimeline = () => {
    if (currentProject) {
      generateTimelineMutation.mutate(currentProject.id)
    }
  }

  const currentStep = currentProject?.current_step || 0

  return (
    <div className="animate-fade-in">
      <div className="mb-8">
        <h2 className="text-3xl font-bold mb-2">Создание контента</h2>
        <p className="text-white/60">6-этапный процесс создания видео с AI</p>
      </div>

      {/* Stepper */}
      {currentProject && <Stepper currentStep={currentStep} steps={STEPS} />}

      {/* Step 0: Select Blogger */}
      {!currentProject && (
        <div className="glass-card p-8">
          <h3 className="text-xl font-bold mb-4">Выберите блогера</h3>
          
          {!bloggers || bloggers.length === 0 ? (
            <p className="text-white/60">Сначала создайте блогера во вкладке "Блогеры"</p>
          ) : (
            <>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                {bloggers.map((blogger) => (
                  <button
                    key={blogger.id}
                    onClick={() => setSelectedBlogger(blogger.id)}
                    className={`glass-card p-4 text-left transition-smooth ${
                      selectedBlogger === blogger.id
                        ? 'ring-2 ring-blue-500 bg-blue-600/20'
                        : 'hover:bg-white/10'
                    }`}
                  >
                    {blogger.frontal_image_url && (
                      <img
                        src={blogger.frontal_image_url}
                        alt={blogger.name}
                        className="w-full h-32 object-cover rounded-lg mb-3"
                      />
                    )}
                    <h4 className="font-bold">{blogger.name}</h4>
                    <p className="text-xs text-white/60">{blogger.type}</p>
                  </button>
                ))}
              </div>
              
              <button
                onClick={handleStartProject}
                disabled={!selectedBlogger || createProjectMutation.isPending}
                className="btn-primary w-full"
              >
                {createProjectMutation.isPending ? 'Создание...' : 'Начать проект'}
              </button>
            </>
          )}
        </div>
      )}

      {/* Step 1: Scenario Input */}
      {currentProject && currentStep === 1 && (
        <div className="glass-card p-8">
          <h3 className="text-xl font-bold mb-4">Этап 1: Введите сценарий</h3>
          
          <textarea
            value={scenario}
            onChange={(e) => setScenario(e.target.value)}
            className="input-glass min-h-[300px] resize-none mb-4"
            placeholder="Введите сценарий для видео..."
          />
          
          <div className="flex gap-3">
            <button
              onClick={handleSaveScenario}
              disabled={!scenario || updateScenarioMutation.isPending}
              className="btn-secondary"
            >
              Сохранить
            </button>
            
            <button
              onClick={handleExtractText}
              disabled={!scenario || extractTextMutation.isPending}
              className="btn-primary flex-1 flex items-center justify-center gap-2"
            >
              {extractTextMutation.isPending && <Loader2 size={20} className="animate-spin" />}
              Извлечь текст для озвучки
            </button>
          </div>
        </div>
      )}

      {/* Step 2: Voiceover Text & Audio */}
      {currentProject && currentStep >= 2 && voiceoverText && (
        <div className="glass-card p-8 mb-6">
          <h3 className="text-xl font-bold mb-4">Этап 2: Текст для озвучки</h3>
          
          <textarea
            value={voiceoverText}
            onChange={(e) => setVoiceoverText(e.target.value)}
            className="input-glass min-h-[200px] resize-none mb-4"
          />
          
          {!currentProject.audio_url ? (
            <button
              onClick={handleGenerateAudio}
              disabled={generateAudioMutation.isPending}
              className="btn-primary w-full flex items-center justify-center gap-2"
            >
              {generateAudioMutation.isPending && <Loader2 size={20} className="animate-spin" />}
              Сгенерировать аудио
            </button>
          ) : (
            <>
              <div className="glass-card p-4 mb-4">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm text-white/60">Аудиодорожка готова</span>
                  <button
                    onClick={() => setIsPlaying(!isPlaying)}
                    className="p-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-smooth"
                  >
                    {isPlaying ? <Pause size={20} /> : <Play size={20} />}
                  </button>
                </div>
                
                <audio
                  src={currentProject.audio_url}
                  controls
                  className="w-full"
                  onPlay={() => setIsPlaying(true)}
                  onPause={() => setIsPlaying(false)}
                />
              </div>
              
              <div className="flex gap-3">
                <button
                  onClick={handleGenerateAudio}
                  disabled={generateAudioMutation.isPending}
                  className="btn-secondary"
                >
                  Перегенерировать
                </button>
                
                <button
                  onClick={handleApproveVoiceover}
                  className="btn-primary flex-1 flex items-center justify-center gap-2"
                >
                  <Check size={20} />
                  Принять и продолжить
                </button>
              </div>
            </>
          )}
        </div>
      )}

      {/* Next steps placeholder */}
      {currentProject && currentStep >= 3 && (
        <>
          {/* Step 3: Materials Upload */}
          <div className="glass-card p-8 mb-6">
            <h3 className="text-xl font-bold mb-4">Этап 3: Загрузка материалов</h3>

            {/* Upload area */}
            <div className="border-2 border-dashed border-white/20 rounded-lg p-8 mb-6 text-center hover:border-blue-500/50 transition-smooth">
              <input
                type="file"
                multiple
                accept="image/*,video/*"
                onChange={handleFileUpload}
                className="hidden"
                id="file-upload"
              />
              <label htmlFor="file-upload" className="cursor-pointer">
                <Upload size={48} className="mx-auto mb-4 text-white/40" />
                <p className="text-white/60 mb-2">Загрузите изображения или видео</p>
                <p className="text-sm text-white/40">Поддержка drag & drop в разработке</p>
              </label>
            </div>

            {/* TMDB Search */}
            <div className="glass-card p-6 mb-6">
              <h4 className="font-bold mb-3 flex items-center gap-2">
                <Film size={20} />
                Поиск материалов из TMDB
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
                <input
                  type="text"
                  value={tmdbTitle}
                  onChange={(e) => setTmdbTitle(e.target.value)}
                  placeholder="Название на английском (Tenet)"
                  className="input-glass"
                />
                <input
                  type="text"
                  value={tmdbTitleSecondary}
                  onChange={(e) => setTmdbTitleSecondary(e.target.value)}
                  placeholder="Название на русском (Довод)"
                  className="input-glass"
                />
              </div>
              <button
                onClick={handleSearchTMDB}
                disabled={!tmdbTitle || searchTMDBMutation.isPending}
                className="btn-secondary w-full flex items-center justify-center gap-2"
              >
                {searchTMDBMutation.isPending && <Loader2 size={20} className="animate-spin" />}
                Найти в TMDB
              </button>
            </div>

            {/* Materials Grid */}
            {currentProject.materials && currentProject.materials.length > 0 && (
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h4 className="font-bold">Загруженные материалы ({currentProject.materials.length})</h4>
                  <button
                    onClick={handleAnalyzeMaterials}
                    disabled={analyzeMaterialsMutation.isPending}
                    className="btn-secondary flex items-center gap-2"
                  >
                    {analyzeMaterialsMutation.isPending ? (
                      <Loader2 size={16} className="animate-spin" />
                    ) : (
                      <Sparkles size={16} />
                    )}
                    Анализировать AI
                  </button>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {currentProject.materials.map((material: any) => (
                    <div key={material.id} className="glass-card p-2">
                      <img
                        src={material.url}
                        alt="Material"
                        className="w-full h-32 object-cover rounded mb-2"
                      />
                      {material.analysis && (
                        <p className="text-xs text-white/60 line-clamp-2">{material.analysis}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Step 4: Timeline */}
          {currentStep >= 4 && (
            <div className="glass-card p-8">
              <h3 className="text-xl font-bold mb-4">Этап 4: Тайминги и монтаж</h3>

              {!currentProject.timeline || currentProject.timeline.length === 0 ? (
                <button
                  onClick={handleGenerateTimeline}
                  disabled={generateTimelineMutation.isPending}
                  className="btn-primary w-full flex items-center justify-center gap-2"
                >
                  {generateTimelineMutation.isPending && <Loader2 size={20} className="animate-spin" />}
                  Сгенерировать тайминги
                </button>
              ) : (
                <div className="space-y-3">
                  {currentProject.timeline.map((segment: any, index: number) => (
                    <div key={index} className="glass-card p-4 flex gap-4">
                      <div className="w-20 text-center">
                        <div className="text-sm text-white/60">
                          {segment.start_time.toFixed(1)}s - {segment.end_time.toFixed(1)}s
                        </div>
                      </div>
                      <div className="flex-1">
                        <p className="text-sm mb-1">{segment.text_snippet}</p>
                        <p className="text-xs text-white/60">{segment.rationale}</p>
                      </div>
                      {segment.material_id !== 'MISSING' && (
                        <div className="w-24">
                          <div className="w-full h-16 bg-white/5 rounded flex items-center justify-center text-xs text-white/40">
                            Материал
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </>
      )}

      {/* Future steps */}
      {currentProject && currentStep >= 5 && (
        <div className="glass-card p-8 text-center mt-6">
          <p className="text-white/60">Этапы 5-6 (Генерация видео и Монтаж) в разработке...</p>
        </div>
      )}
    </div>
  )
}
