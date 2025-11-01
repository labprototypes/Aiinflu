import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Loader2, Play, Pause, Check } from 'lucide-react'
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
        <div className="glass-card p-8 text-center">
          <p className="text-white/60">Следующие этапы в разработке...</p>
        </div>
      )}
    </div>
  )
}
