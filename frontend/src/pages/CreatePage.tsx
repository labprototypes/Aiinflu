import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useLocation } from 'react-router-dom'
import { Loader2, Play, Pause, Check, Sparkles, Video, Download } from 'lucide-react'
import { bloggersApi, projectsApi } from '@/lib/api'
import type { Blogger, Project } from '@/types'
import Stepper from '@/components/Stepper'
import MaterialUploader, { UploadPreview } from '@/components/MaterialUploader'
import type { UploadingFile } from '@/components/MaterialUploader'
import LocationSelector from '@/components/LocationSelector'

const STEPS = [
  { number: 1, title: 'Подготовка' },
  { number: 2, title: 'Озвучка и тайминги' },
  { number: 3, title: 'Генерация и монтаж' },
]

// Map old backend steps (1-6) to new UI steps (1-3)
const mapBackendStepToUI = (backendStep: number): number => {
  if (backendStep <= 1) return 1 // Preparation
  if (backendStep <= 4) return 2 // Voiceover + Timeline (steps 2,3,4)
  return 3 // Generation + Composition (steps 5,6)
}

export default function CreatePage() {
  const location = useLocation()
  const [currentProject, setCurrentProject] = useState<Project | null>(null)
  const [selectedBlogger, setSelectedBlogger] = useState<string>('')
  const [selectedLocationId, setSelectedLocationId] = useState<number | null | undefined>(undefined)
  const [locationSelected, setLocationSelected] = useState(false) // Track if location was confirmed
  const [scenario, setScenario] = useState('')
  const [voiceoverText, setVoiceoverText] = useState('')
  const [isPlaying, setIsPlaying] = useState(false)
  const [expressionScale, setExpressionScale] = useState(1.0)
  const [addSubtitles, setAddSubtitles] = useState(true)
  const [uploadingFiles, setUploadingFiles] = useState<UploadingFile[]>([])
  const [analyzeStatus, setAnalyzeStatus] = useState<'idle' | 'pending' | 'done' | 'error'>('idle')
  const [avatarGenStatus, setAvatarGenStatus] = useState<'idle' | 'pending' | 'done' | 'error'>('idle')
  const [avatarRequestId, setAvatarRequestId] = useState<string | null>(null)
  const [viewStep, setViewStep] = useState<number | null>(null) // Which step to display (null = use current_step)
  
  // Auto-build pipeline stages
  const [autoBuildStage, setAutoBuildStage] = useState<string>('')
  const [autoBuildProgress, setAutoBuildProgress] = useState<{
    extractText: 'pending' | 'done' | 'error' | '',
    analyzeMaterials: 'pending' | 'done' | 'error' | '',
    generateAudio: 'pending' | 'done' | 'error' | '',
    generateTimeline: 'pending' | 'done' | 'error' | '',
    generateAvatar: 'pending' | 'done' | 'error' | '',
    complete: boolean
  }>({
    extractText: '',
    analyzeMaterials: '',
    generateAudio: '',
    generateTimeline: '',
    generateAvatar: '',
    complete: false
  })
  
  const queryClient = useQueryClient()

  // Load project from navigation state (when continuing from Projects page)
  useEffect(() => {
    const projectId = location.state?.projectId
    if (projectId && !currentProject) {
      projectsApi.getById(projectId).then((response) => {
        const project = response.data as Project
        setCurrentProject(project)
        if (project.scenario_text) setScenario(project.scenario_text)
        if (project.voiceover_text) setVoiceoverText(project.voiceover_text)
        // If location was already selected, mark it as selected
        if (project.location_id !== undefined) {
          setSelectedLocationId(project.location_id)
          setLocationSelected(true)
        }
      })
    }
  }, [location.state, currentProject])

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

  const changeStepMutation = useMutation({
    mutationFn: ({ id, step }: { id: string; step: number }) =>
      projectsApi.updateStep(id, step),
    onSuccess: (response) => {
      setCurrentProject(response.data as Project)
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })

  const extractTextMutation = useMutation({
    mutationFn: (id: string) => projectsApi.extractText(id),
    onSuccess: (response) => {
      setVoiceoverText(response.data.voiceover_text)
      setCurrentProject(response.data.project)
    },
  })

  const extractAndAnalyzeMutation = useMutation({
    mutationFn: (id: string) => projectsApi.extractAndAnalyze(id),
    onSuccess: (response) => {
      setVoiceoverText(response.data.voiceover_text)
      setCurrentProject(response.data.project)
      setAnalyzeStatus('done')
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      // Auto-advance to Step 2
      setTimeout(() => {
        changeStepMutation.mutate({ id: response.data.project.id, step: 2 })
      }, 1000)
    },
  })

  const autoBuildMutation = useMutation({
    mutationFn: async (id: string) => {
      // Switch to Step 7 (Auto mode) immediately and show progress
      setViewStep(7)
      setAutoBuildProgress({
        extractText: 'pending',
        analyzeMaterials: '',
        generateAudio: '',
        generateTimeline: '',
        generateAvatar: '',
        complete: false
      })
      setAutoBuildStage('Извлечение текста из сценария...')
      
      // Simulate progress updates + refresh project data
      setTimeout(async () => {
        setAutoBuildProgress(prev => ({ ...prev, extractText: 'done', analyzeMaterials: 'pending' }))
        setAutoBuildStage('Анализ материалов с помощью GPT Vision...')
        // Refresh project data
        const proj = await projectsApi.getById(id)
        setCurrentProject(proj.data)
      }, 2000)
      
      setTimeout(async () => {
        setAutoBuildProgress(prev => ({ ...prev, analyzeMaterials: 'done', generateAudio: 'pending' }))
        setAutoBuildStage('Генерация аудио с ElevenLabs...')
        // Refresh project data
        const proj = await projectsApi.getById(id)
        setCurrentProject(proj.data)
      }, 4000)
      
      setTimeout(async () => {
        setAutoBuildProgress(prev => ({ ...prev, generateAudio: 'done', generateTimeline: 'pending' }))
        setAutoBuildStage('Создание таймлайна видео...')
        // Refresh project data
        const proj = await projectsApi.getById(id)
        setCurrentProject(proj.data)
      }, 8000)
      
      setTimeout(async () => {
        setAutoBuildProgress(prev => ({ ...prev, generateTimeline: 'done', generateAvatar: 'pending' }))
        setAutoBuildStage('Генерация аватар видео с HeyGen...')
        // Refresh project data
        const proj = await projectsApi.getById(id)
        setCurrentProject(proj.data)
      }, 12000)
      
      return projectsApi.autoBuild(id)
    },
    onSuccess: (response) => {
      const videoId = response.data.video_id
      setAvatarRequestId(videoId)
      setAvatarGenStatus('pending')
      setCurrentProject(response.data.project)
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      
      // Start polling for avatar video completion
      if (videoId) {
        const pollInterval = setInterval(async () => {
          const statusResp = await projectsApi.checkAvatarStatus(response.data.project.id, videoId)
          if (statusResp.data.status === 'completed') {
            clearInterval(pollInterval)
            setAutoBuildProgress(prev => ({ ...prev, generateAvatar: 'done', complete: true }))
            setAutoBuildStage('✓ Готово! Видео успешно создано')
            setAvatarGenStatus('done')
            queryClient.invalidateQueries({ queryKey: ['projects'] })
          } else if (statusResp.data.status === 'error') {
            clearInterval(pollInterval)
            setAutoBuildProgress(prev => ({ ...prev, generateAvatar: 'error' }))
            setAutoBuildStage('Ошибка при генерации видео')
            setAvatarGenStatus('error')
          }
        }, 5000)
      }
    },
    onError: (error) => {
      setAutoBuildStage(`Ошибка: ${error.message}`)
      setAutoBuildProgress(prev => ({ ...prev, complete: true }))
    }
  })

  const generateAudioMutation = useMutation({
    mutationFn: (id: string) => projectsApi.generateAudio(id),
    onSuccess: (response) => {
      setCurrentProject(response.data.project)
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      // Auto-advance to Step 3
      setTimeout(() => {
        changeStepMutation.mutate({ id: response.data.project.id, step: 3 })
      }, 1000)
    },
    onError: (error) => {
      console.error('Audio generation failed:', error)
    },
  })

  const uploadMaterialMutation = useMutation({
    mutationFn: ({ id, file, type }: { id: string; file: File; type: string }) =>
      projectsApi.uploadMaterial(id, file, type),
    onSuccess: (response) => {
      setCurrentProject(response.data.project)
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })

  const deleteMaterialMutation = useMutation({
    mutationFn: ({ projectId, materialId }: { projectId: string; materialId: string }) =>
      projectsApi.deleteMaterial(projectId, materialId),
    onSuccess: (response) => {
      setCurrentProject(response.data.project)
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })

  const analyzeMaterialsMutation = useMutation({
    mutationFn: (id: string) => projectsApi.analyzeMaterials(id),
    onMutate: () => {
      setAnalyzeStatus('pending')
    },
    onSuccess: (response) => {
      setCurrentProject(response.data.project)
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      setAnalyzeStatus('done')
    },
    onError: () => {
      setAnalyzeStatus('error')
    },
  })

  const generateTimelineMutation = useMutation({
    mutationFn: (id: string) => projectsApi.generateTimeline(id),
    onSuccess: (response) => {
      setCurrentProject(response.data.project)
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      // Auto-advance to Step 5
      setTimeout(() => {
        changeStepMutation.mutate({ id: response.data.project.id, step: 5 })
      }, 1000)
    },
  })

  const generateAvatarMutation = useMutation({
    mutationFn: ({ id, params }: { id: string; params?: any }) =>
      projectsApi.generateAvatarVideo(id, params),
    onMutate: () => {
      setAvatarGenStatus('pending')
    },
    onSuccess: (response) => {
      // Response now contains request_id, not video_url
      const requestId = response.data.request_id
      setAvatarRequestId(requestId)
      // Status will be updated by polling useEffect
    },
    onError: () => {
      setAvatarGenStatus('error')
      setAvatarRequestId(null)
    },
  })

  // Poll avatar generation status
  useEffect(() => {
    if (!avatarRequestId || !currentProject) return

    const pollInterval = setInterval(async () => {
      try {
        const response = await projectsApi.checkAvatarStatus(currentProject.id, avatarRequestId)
        const data = response.data

        if (data.status === 'completed' && data.video_url) {
          setAvatarGenStatus('done')
          setAvatarRequestId(null)
          // Refresh project to get updated video_url
          const projectResponse = await projectsApi.getById(currentProject.id)
          setCurrentProject(projectResponse.data)
          queryClient.invalidateQueries({ queryKey: ['projects'] })
          clearInterval(pollInterval)
        } else if (data.status === 'error') {
          setAvatarGenStatus('error')
          setAvatarRequestId(null)
          clearInterval(pollInterval)
        }
        // else: still processing, continue polling
      } catch (error) {
        console.error('Avatar status check failed:', error)
      }
    }, 5000) // Check every 5 seconds

    return () => clearInterval(pollInterval)
  }, [avatarRequestId, currentProject, queryClient])

  const composeFinalMutation = useMutation({
    mutationFn: ({ id, options }: { id: string; options?: any }) =>
      projectsApi.composeFinalVideo(id, options),
    onSuccess: (response) => {
      setCurrentProject(response.data.project)
    },
  })

  const handleStartProject = () => {
    if (selectedBlogger) {
      createProjectMutation.mutate(selectedBlogger)
    }
  }

  const handleLocationConfirm = async () => {
    if (currentProject) {
      // Save selected location to project
      await updateScenarioMutation.mutateAsync({
        id: currentProject.id,
        data: { location_id: selectedLocationId },
      })
      setLocationSelected(true)
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

  const handleExtractAndAnalyze = () => {
    if (currentProject) {
      setAnalyzeStatus('pending')
      extractAndAnalyzeMutation.mutate(currentProject.id)
    }
  }

  const handleAutoBuild = () => {
    if (currentProject) {
      if (confirm('Запустить полную автоматическую сборку видео?\n\nБудут выполнены все шаги: озвучка, тайминги, генерация видео, монтаж.\n\nЭто может занять 3-5 минут.')) {
        setAnalyzeStatus('pending')
        autoBuildMutation.mutate(currentProject.id)
      }
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
        data: { voiceover_text: voiceoverText, current_step: 3 },
      })
    }
  }

  const handleFilesSelected = async (files: File[]) => {
    if (!currentProject) return

    // Create upload tracking objects
    const newUploads: UploadingFile[] = files.map((file) => ({
      id: `${Date.now()}-${Math.random()}`,
      file,
      preview: URL.createObjectURL(file),
      status: 'uploading' as const,
      progress: 0,
    }))

    setUploadingFiles((prev) => [...prev, ...newUploads])

    // Upload files one by one
    for (const upload of newUploads) {
      try {
        // Simulate progress
        const progressInterval = setInterval(() => {
          setUploadingFiles((prev) =>
            prev.map((u) =>
              u.id === upload.id && u.progress < 90
                ? { ...u, progress: u.progress + 10 }
                : u
            )
          )
        }, 200)

        const type = upload.file.type.startsWith('image/') ? 'image' : 'video'
        await uploadMaterialMutation.mutateAsync({
          id: currentProject.id,
          file: upload.file,
          type,
        })

        clearInterval(progressInterval)

        // Mark as success
        setUploadingFiles((prev) =>
          prev.map((u) =>
            u.id === upload.id
              ? { ...u, status: 'success' as const, progress: 100 }
              : u
          )
        )

        // Remove from uploading list after 2 seconds
        setTimeout(() => {
          setUploadingFiles((prev) => prev.filter((u) => u.id !== upload.id))
        }, 2000)
      } catch (error) {
        // Mark as error
        setUploadingFiles((prev) =>
          prev.map((u) =>
            u.id === upload.id
              ? {
                  ...u,
                  status: 'error' as const,
                  error: error instanceof Error ? error.message : 'Ошибка загрузки',
                }
              : u
          )
        )
      }
    }

    // After all uploads, refresh project from server to get authoritative materials list
    try {
      const resp = await projectsApi.getById(currentProject.id)
      setCurrentProject(resp.data)
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    } catch (e) {
      // ignore
    }
  }

  const handleRemoveUpload = (id: string) => {
    setUploadingFiles((prev) => prev.filter((u) => u.id !== id))
  }

  const handleDeleteMaterial = (materialId: string) => {
    if (currentProject && confirm('Удалить этот материал?')) {
      deleteMaterialMutation.mutate({
        projectId: currentProject.id,
        materialId,
      })
    }
  }

  const handleAnalyzeMaterials = () => {
    if (currentProject) {
      analyzeMaterialsMutation.mutate(currentProject.id)
    }
  }

  const handleGenerateTimeline = () => {
    if (currentProject) {
      generateTimelineMutation.mutate(currentProject.id)
    }
  }

  const handleGenerateAvatar = () => {
    if (currentProject) {
      generateAvatarMutation.mutate({
        id: currentProject.id,
        params: { expression_scale: expressionScale, face_enhance: true },
      })
    }
  }

  const handleComposeFinal = () => {
    if (currentProject) {
      // Clear final_video_url to show progress UI during regeneration
      if (currentProject.final_video_url) {
        setCurrentProject({ ...currentProject, final_video_url: null })
      }
      
      composeFinalMutation.mutate({
        id: currentProject.id,
        options: { add_subtitles: addSubtitles, advanced_composition: true },
      })
    }
  }

  const handleStepClick = (step: number) => {
    if (currentProject && step <= currentProject.current_step) {
      // Just change the view, don't update DB
      setViewStep(step)
    }
  }

  // Displayed step: use viewStep if set, otherwise map backend step to UI step
  const backendStep = currentProject?.current_step || 0
  const displayStep = viewStep !== null ? viewStep : (viewStep === 7 ? 7 : mapBackendStepToUI(backendStep))
  // Maximum reached step (in UI terms)
  const maxStep = mapBackendStepToUI(backendStep)

  return (
    <div className="animate-fade-in">
      <div className="mb-8">
        <h2 className="text-3xl font-bold mb-2">Создание контента</h2>
        <p className="text-white/60">3-этапный процесс создания видео с AI</p>
      </div>

      {/* Project Info Panel */}
      {currentProject && (
        <div className="glass-card p-6 mb-6">
          <div className="flex flex-wrap items-center gap-6 text-sm">
            <div className="flex items-center gap-2">
              <span className="text-white/60">👤 Блогер:</span>
              <span className="font-semibold">{currentProject.blogger?.name || 'Не выбран'}</span>
            </div>
            
            {currentProject.location_id !== null && currentProject.blogger?.locations && (
              <div className="flex items-center gap-2">
                <span className="text-white/60">📍 Локация:</span>
                <span className="font-semibold">
                  {currentProject.blogger.locations[currentProject.location_id]?.name || 'Frontal'}
                </span>
              </div>
            )}
            
            {currentProject.audio_alignment?.audio_duration && (
              <div className="flex items-center gap-2">
                <span className="text-white/60">⏱️ Длительность:</span>
                <span className="font-semibold">{currentProject.audio_alignment.audio_duration.toFixed(1)}с</span>
              </div>
            )}
            
            {currentProject.materials && (
              <div className="flex items-center gap-2">
                <span className="text-white/60">🎬 Материалов:</span>
                <span className="font-semibold">{currentProject.materials.length}</span>
              </div>
            )}
            
            <div className="flex items-center gap-2 ml-auto">
              <span className="text-white/60">Статус:</span>
              {currentProject.final_video_url ? (
                <span className="px-3 py-1 bg-green-600/20 text-green-400 rounded-full font-semibold">✓ Готово</span>
              ) : currentProject.avatar_video_url ? (
                <span className="px-3 py-1 bg-blue-600/20 text-blue-400 rounded-full font-semibold">🎥 Видео</span>
              ) : currentProject.timeline ? (
                <span className="px-3 py-1 bg-purple-600/20 text-purple-400 rounded-full font-semibold">📋 Тайминги</span>
              ) : currentProject.audio_url ? (
                <span className="px-3 py-1 bg-yellow-600/20 text-yellow-400 rounded-full font-semibold">🎵 Аудио</span>
              ) : (
                <span className="px-3 py-1 bg-gray-600/20 text-gray-400 rounded-full font-semibold">📝 Подготовка</span>
              )}
            </div>
          </div>
          
          {/* Auto-build progress bar (when running) */}
          {viewStep === 7 && !autoBuildProgress.complete && (
            <div className="mt-4 pt-4 border-t border-white/10">
              <div className="flex items-center gap-3 mb-2">
                <Loader2 size={16} className="animate-spin text-blue-400" />
                <span className="text-sm font-medium">{autoBuildStage}</span>
              </div>
              <div className="flex gap-2">
                {[
                  { key: 'extractText', label: 'Текст' },
                  { key: 'analyzeMaterials', label: 'Анализ' },
                  { key: 'generateAudio', label: 'Аудио' },
                  { key: 'generateTimeline', label: 'Таймлайн' },
                  { key: 'generateAvatar', label: 'Видео' }
                ].map((stage) => (
                  <div key={stage.key} className="flex-1">
                    <div className={`h-2 rounded-full transition-all ${
                      autoBuildProgress[stage.key as keyof typeof autoBuildProgress] === 'done'
                        ? 'bg-green-500'
                        : autoBuildProgress[stage.key as keyof typeof autoBuildProgress] === 'pending'
                        ? 'bg-yellow-500 animate-pulse'
                        : 'bg-white/10'
                    }`} />
                    <span className="text-xs text-white/60 mt-1 block text-center">{stage.label}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Stepper */}
      {currentProject && (
        <Stepper 
          currentStep={displayStep}
          maxStep={maxStep}
          steps={STEPS} 
          onStepClick={handleStepClick}
        />
      )}

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
                    className={`glass-card p-4 text-left transition-smooth relative ${
                      selectedBlogger === blogger.id
                        ? 'ring-2 ring-blue-500 bg-blue-600/20'
                        : 'hover:bg-white/10'
                    }`}
                  >
                    {selectedBlogger === blogger.id && (
                      <div className="absolute top-2 right-2 bg-blue-500 rounded-full p-1">
                        <Check size={16} />
                      </div>
                    )}
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

      {/* Step 0.5: Select Location (after project created, before scenario) */}
      {currentProject && !locationSelected && currentProject.blogger && (
        <>
          <LocationSelector
            blogger={currentProject.blogger}
            selectedLocationId={selectedLocationId}
            onSelect={setSelectedLocationId}
          />
          <div className="glass-card p-6 mt-4">
            <button
              onClick={handleLocationConfirm}
              disabled={updateScenarioMutation.isPending}
              className="btn-primary w-full"
            >
              {updateScenarioMutation.isPending ? 'Сохранение...' : 'Продолжить к сценарию'}
            </button>
          </div>
        </>
      )}

      {/* Step 1: Scenario Input + Materials */}
      {currentProject && locationSelected && displayStep === 1 && (
        <div className="space-y-6">
          {/* Scenario Input */}
          <div className="glass-card p-8">
            <h3 className="text-xl font-bold mb-4">Этап 1: Сценарий и материалы</h3>
            
            <div className="mb-6">
              <label className="block text-sm font-medium mb-2">Сценарий видео</label>
              <textarea
                value={scenario}
                onChange={(e) => setScenario(e.target.value)}
                className="input-glass min-h-[200px] resize-none"
                placeholder="Введите идею сценария для видео...&#10;&#10;Например: Расскажи о двух фильмах:&#10;1. Человек-паук 2 - история о супергерое&#10;2. Зеленая миля - драма о чуде"
              />
            </div>

            {/* Materials Upload */}
            <div className="mb-6">
              <label className="block text-sm font-medium mb-2">Материалы (постеры фильмов)</label>
              <MaterialUploader
                onFilesSelected={handleFilesSelected}
                maxFiles={10}
                accept="image/*,video/*"
                disabled={uploadMaterialMutation.isPending}
              />
            </div>

            {/* Upload Preview */}
            {uploadingFiles.length > 0 && (
              <div className="mb-6">
                <UploadPreview
                  uploadingFiles={uploadingFiles}
                  onRemove={handleRemoveUpload}
                />
              </div>
            )}

            {/* Uploaded Materials Grid */}
            {currentProject.materials && currentProject.materials.length > 0 && (
              <div className="mb-6">
                <h4 className="font-medium mb-3">Загруженные материалы ({currentProject.materials.length})</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {currentProject.materials.map((material: any) => (
                    <div key={material.id} className="glass-card p-2 relative group">
                      <img
                        src={material.url}
                        alt="Material"
                        className="w-full h-32 object-cover rounded mb-2"
                      />
                      {material.analysis && (
                        <p className="text-xs text-white/60 line-clamp-2">{material.analysis}</p>
                      )}
                      
                      <button
                        onClick={() => handleDeleteMaterial(material.id)}
                        disabled={deleteMaterialMutation.isPending}
                        className="absolute top-1 right-1 p-2 bg-red-600 hover:bg-red-700 
                                 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity
                                 disabled:opacity-50"
                        title="Удалить материал"
                      >
                        <span className={deleteMaterialMutation.isPending ? 'hidden' : 'block'}>✕</span>
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {/* Action Buttons */}
            <div className="space-y-3">
              {/* Status banner */}
              {analyzeStatus === 'pending' && (
                <div className="p-3 bg-yellow-600/20 rounded flex items-center gap-2">
                  <Loader2 size={16} className="animate-spin" />
                  Извлечение текста и анализ материалов...
                </div>
              )}
              {analyzeStatus === 'done' && (
                <div className="p-3 bg-green-600/20 rounded flex items-center gap-2">
                  <Check size={16} />
                  Готово! Текст извлечён и материалы проанализированы
                </div>
              )}
              
              <div className="flex gap-3">
                <button
                  onClick={handleExtractAndAnalyze}
                  disabled={!scenario || extractAndAnalyzeMutation.isPending}
                  className="btn-primary flex-1 flex items-center justify-center gap-2"
                >
                  {extractAndAnalyzeMutation.isPending && <Loader2 size={20} className="animate-spin" />}
                  <Sparkles size={20} />
                  Извлечь и проанализировать
                </button>
                
                {currentProject.materials && currentProject.materials.length > 0 && (
                  <button
                    onClick={handleAutoBuild}
                    disabled={!scenario || autoBuildMutation.isPending}
                    className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 
                             text-white px-6 py-3 rounded-lg font-semibold transition-smooth
                             disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    >
                      {autoBuildMutation.isPending && <Loader2 size={20} className="animate-spin" />}
                      <Sparkles size={20} />
                      Авто-сборка
                    </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Step 2: Voiceover, Audio & Timeline (Combined) */}
      {currentProject && locationSelected && displayStep === 2 && voiceoverText && (
        <div className="glass-card p-8 mb-6">
          <h3 className="text-xl font-bold mb-6">Этап 2: Озвучка и тайминги</h3>
          
          {/* Section 1: Voiceover Text */}
          <div className="mb-8 pb-8 border-b border-white/10">
            <h4 className="text-lg font-semibold mb-4">📝 Текст для озвучки</h4>
          
          {/* Helper text with audio tags info */}
          <div className="mb-3 p-3 bg-blue-600/10 rounded-lg text-sm">
            <p className="text-white/80 mb-2">💡 Доступные аудио-теги для выразительности:</p>
            <div className="flex flex-wrap gap-2 text-xs">
              <span className="px-2 py-1 bg-yellow-600/20 text-yellow-300 rounded">[excited]</span>
              <span className="px-2 py-1 bg-green-600/20 text-green-300 rounded">[happy]</span>
              <span className="px-2 py-1 bg-blue-600/20 text-blue-300 rounded">[thoughtful]</span>
              <span className="px-2 py-1 bg-purple-600/20 text-purple-300 rounded">[surprised]</span>
              <span className="px-2 py-1 bg-red-600/20 text-red-300 rounded">[fast]</span>
              <span className="px-2 py-1 bg-orange-600/20 text-orange-300 rounded">[slow]</span>
            </div>
          </div>
          
          {/* Preview with highlighted tags */}
          <div className="mb-4 p-4 bg-white/5 rounded-lg min-h-[150px] whitespace-pre-wrap">
            {voiceoverText.split(/(\[[\w\s]+\])/).map((part, i) => {
              if (part.match(/\[(excited|happy)\]/)) {
                return <span key={i} className="text-yellow-400 font-semibold">{part}</span>
              } else if (part.match(/\[(thoughtful|curious)\]/)) {
                return <span key={i} className="text-blue-400 font-semibold">{part}</span>
              } else if (part.match(/\[(surprised|annoyed)\]/)) {
                return <span key={i} className="text-purple-400 font-semibold">{part}</span>
              } else if (part.match(/\[(fast|quickly)\]/)) {
                return <span key={i} className="text-red-400 font-semibold">{part}</span>
              } else if (part.match(/\[(slow|measured)\]/)) {
                return <span key={i} className="text-orange-400 font-semibold">{part}</span>
              } else if (part.match(/\[[\w\s]+\]/)) {
                return <span key={i} className="text-green-400 font-semibold">{part}</span>
              }
              return <span key={i}>{part}</span>
            })}
          </div>
          
          {/* Editable textarea */}
          <textarea
            value={voiceoverText}
            onChange={(e) => setVoiceoverText(e.target.value)}
            className="input-glass min-h-[200px] resize-none mb-4"
            placeholder="Отредактируйте текст и добавьте audio-теги для выразительности..."
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
                  className="btn-secondary flex items-center justify-center gap-2"
                >
                  {generateAudioMutation.isPending && <Loader2 size={20} className="animate-spin" />}
                  Перегенерировать
                </button>
                
                <button
                  onClick={handleGenerateAudio}
                  disabled={generateAudioMutation.isPending}
                  className="btn-secondary flex-1"
                >
                  Перегенерировать аудио
                </button>
              </div>
            </>
          )}
          </div>

          {/* Section 2: Audio Player */}
          {currentProject.audio_url && (
            <div className="mb-8 pb-8 border-b border-white/10">
              <h4 className="text-lg font-semibold mb-4">🎵 Аудиодорожка</h4>
              <div className="glass-card p-4">
                <audio
                  src={currentProject.audio_url}
                  controls
                  className="w-full"
                  onPlay={() => setIsPlaying(true)}
                  onPause={() => setIsPlaying(false)}
                />
                <p className="text-sm text-white/60 mt-2">
                  {currentProject.audio_alignment?.audio_duration 
                    ? `Длительность: ${currentProject.audio_alignment.audio_duration.toFixed(1)}с`
                    : 'Аудио готово к использованию'}
                </p>
              </div>
            </div>
          )}

          {/* Section 3: Timeline */}
          {currentProject.audio_url && (
            <div className="mb-6">
              <h4 className="text-lg font-semibold mb-4">📋 Тайминги и раскладка</h4>
              
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
                <>
                  <div className="space-y-3 mb-4">
                    {currentProject.timeline.map((segment: any, index: number) => {
                      const material = segment.material_id !== 'MISSING' 
                        ? currentProject.materials?.find((m: any) => m.id === segment.material_id)
                        : null

                      return (
                        <div key={index} className="glass-card p-4 flex gap-4">
                          <div className="w-20 text-center shrink-0">
                            <div className="text-sm text-white/60">
                              {segment.start_time.toFixed(1)}s - {segment.end_time.toFixed(1)}s
                            </div>
                          </div>
                          <div className="flex-1">
                            <p className="text-sm mb-1">{segment.text_snippet}</p>
                            <p className="text-xs text-white/60">{segment.rationale}</p>
                          </div>
                          {material ? (
                            <div className="w-32 shrink-0">
                              <img
                                src={material.url}
                                alt={material.analysis || 'Material'}
                                className="w-full h-20 object-cover rounded"
                                title={material.analysis}
                              />
                              {material.analysis && (
                                <p className="text-xs text-white/60 mt-1 text-center line-clamp-1">
                                  {material.analysis}
                                </p>
                              )}
                            </div>
                          ) : (
                            <div className="w-32 shrink-0">
                              <div className="w-full h-20 bg-white/5 rounded flex items-center justify-center text-xs text-white/40">
                                {segment.material_id === 'MISSING' ? 'Нет материала' : 'Не найден'}
                              </div>
                            </div>
                          )}
                        </div>
                      )
                    })}
                  </div>

                  <div className="flex gap-3">
                    <button
                      onClick={handleGenerateTimeline}
                      disabled={generateTimelineMutation.isPending}
                      className="btn-secondary flex items-center gap-2"
                    >
                      {generateTimelineMutation.isPending && <Loader2 size={20} className="animate-spin" />}
                      Перегенерировать тайминги
                    </button>
                    
                    <button
                      onClick={() => {
                        if (currentProject) {
                          changeStepMutation.mutate({ id: currentProject.id, step: 5 })
                        }
                      }}
                      className="btn-primary flex-1"
                    >
                      Далее: Генерация видео
                    </button>
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      )}

      {/* Step 3: Avatar Generation + Video Composition */}
      {currentProject && locationSelected && displayStep >= 3 && (
        <div className="glass-card p-8 mb-6">
          <h3 className="text-xl font-bold mb-6">Этап 3: Генерация и монтаж</h3>
          
          {/* Section 1: Avatar Video Generation */}
          <div className="mb-8 pb-8 border-b border-white/10">
            <h4 className="text-lg font-semibold mb-4">🎬 Генерация видео с аватаром</h4>
            
            {/* Generation status banners */}
            {avatarGenStatus === 'pending' && (
              <div className="p-3 mb-4 bg-yellow-600/20 rounded flex items-center gap-2">
                <Loader2 size={16} className="animate-spin" />
                <span>Генерация видео в процессе... Это может занять 1-3 минуты.</span>
              </div>
            )}
            {avatarGenStatus === 'done' && (
              <div className="p-3 mb-4 bg-green-600/10 rounded">✅ Генерация завершена успешно!</div>
            )}
            {avatarGenStatus === 'error' && (
              <div className="p-3 mb-4 bg-red-600/10 rounded">❌ Ошибка генерации. Проверьте логи или попробуйте ещё раз.</div>
            )}

            {!currentProject.avatar_video_url ? (
              <div>
                <div className="mb-4">
                  <label className="block text-sm mb-2">Выразительность (0.0 - 2.0)</label>
                  <input
                    type="range"
                    min="0"
                    max="2"
                    step="0.1"
                    value={expressionScale}
                    onChange={(e) => setExpressionScale(parseFloat(e.target.value))}
                    className="w-full"
                  />
                  <span className="text-sm text-white/60">{expressionScale.toFixed(1)}</span>
                </div>

                <button
                  onClick={handleGenerateAvatar}
                  disabled={generateAvatarMutation.isPending}
                  className="btn-primary w-full flex items-center justify-center gap-2"
                >
                  {generateAvatarMutation.isPending && <Loader2 size={20} className="animate-spin" />}
                  <Video size={20} />
                  Сгенерировать
                </button>
                
                {generateAvatarMutation.isPending && (
                  <p className="text-center text-white/60 text-sm mt-3">
                    Генерация может занять 1-3 минуты...
                  </p>
                )}
              </div>
            ) : (
              <div>
                <div className="flex justify-center mb-4">
                  <video
                    src={currentProject.avatar_video_url}
                    controls
                    className="max-w-md rounded-lg"
                    style={{ maxHeight: '500px' }}
                  />
                </div>
                <button
                  onClick={handleGenerateAvatar}
                  disabled={generateAvatarMutation.isPending}
                  className="btn-secondary w-full"
                >
                  Перегенерировать видео с аватаром
                </button>
              </div>
            )}
          </div>

          {/* Section 2: Final Composition */}
          {currentProject.avatar_video_url && (
            <div className="mb-6">
              <h4 className="text-lg font-semibold mb-4">🎥 Финальный монтаж</h4>

              {!currentProject.final_video_url ? (
                <div>
                  <div className="mb-4">
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={addSubtitles}
                        onChange={(e) => setAddSubtitles(e.target.checked)}
                        className="w-4 h-4"
                      />
                      <span className="text-sm">Добавить субтитры</span>
                    </label>
                  </div>

                  <button
                    onClick={handleComposeFinal}
                    disabled={composeFinalMutation.isPending}
                    className="btn-primary w-full flex items-center justify-center gap-2"
                  >
                    {composeFinalMutation.isPending && <Loader2 size={20} className="animate-spin" />}
                    Создать финальное видео (FFmpeg)
                  </button>

                  {composeFinalMutation.isPending && (
                    <p className="text-center text-white/60 text-sm mt-3">
                      Монтаж видео в процессе...
                    </p>
                  )}
                </div>
              ) : (
                <div>
                  <div className="text-center mb-6">
                    <div className="inline-block p-4 bg-green-600/20 rounded-full mb-4">
                      <Check size={48} className="text-green-500" />
                    </div>
                    <h4 className="text-xl font-bold mb-2">Видео готово! 🎉</h4>
                    <p className="text-white/60">Проект успешно завершён</p>
                  </div>

                  <div className="flex justify-center mb-4">
                    <video
                      src={currentProject.final_video_url}
                      controls
                      className="max-w-md rounded-lg"
                      style={{ maxHeight: '500px' }}
                    />
                  </div>

                  <div className="mb-4">
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={addSubtitles}
                        onChange={(e) => setAddSubtitles(e.target.checked)}
                        className="w-4 h-4"
                      />
                      <span className="text-sm">Добавить субтитры</span>
                    </label>
                  </div>

                  <div className="flex gap-3">
                    <a
                      href={currentProject.final_video_url}
                      download
                      className="btn-primary flex-1 flex items-center justify-center gap-2"
                    >
                      <Download size={20} />
                      Скачать видео
                    </a>
                    <button
                      onClick={handleComposeFinal}
                      disabled={composeFinalMutation.isPending}
                      className="btn-secondary flex-1 flex items-center justify-center gap-2"
                    >
                      {composeFinalMutation.isPending && <Loader2 size={20} className="animate-spin" />}
                      Пересобрать
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
