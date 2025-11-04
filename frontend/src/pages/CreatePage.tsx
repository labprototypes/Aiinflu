import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useLocation } from 'react-router-dom'
import { Loader2, Play, Pause, Check, Sparkles, Video, Download } from 'lucide-react'
import { bloggersApi, projectsApi } from '@/lib/api'
import type { Blogger, Project } from '@/types'
import Stepper from '@/components/Stepper'
import MaterialUploader, { UploadPreview } from '@/components/MaterialUploader'
import type { UploadingFile } from '@/components/MaterialUploader'

const STEPS = [
  { number: 1, title: 'Подготовка' },
  { number: 2, title: 'Озвучка' },
  { number: 3, title: 'Материалы' },
  { number: 4, title: 'Тайминги' },
  { number: 5, title: 'Генерация' },
  { number: 6, title: 'Монтаж' },
]

export default function CreatePage() {
  const location = useLocation()
  const [currentProject, setCurrentProject] = useState<Project | null>(null)
  const [selectedBlogger, setSelectedBlogger] = useState<string>('')
  const [scenario, setScenario] = useState('')
  const [voiceoverText, setVoiceoverText] = useState('')
  const [isPlaying, setIsPlaying] = useState(false)
  const [expressionScale, setExpressionScale] = useState(1.0)
  const [addSubtitles, setAddSubtitles] = useState(true)
  const [uploadingFiles, setUploadingFiles] = useState<UploadingFile[]>([])
  const [analyzeStatus, setAnalyzeStatus] = useState<'idle' | 'pending' | 'done' | 'error'>('idle')
  const [avatarGenStatus, setAvatarGenStatus] = useState<'idle' | 'pending' | 'done' | 'error'>('idle')
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
    },
  })

  const generateAvatarMutation = useMutation({
    mutationFn: ({ id, params }: { id: string; params?: any }) =>
      projectsApi.generateAvatarVideo(id, params),
    onMutate: () => {
      setAvatarGenStatus('pending')
    },
    onSuccess: (response) => {
      setCurrentProject(response.data.project)
      setAvatarGenStatus('done')
    },
    onError: () => {
      setAvatarGenStatus('error')
    },
  })

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
      composeFinalMutation.mutate({
        id: currentProject.id,
        options: { add_subtitles: addSubtitles, advanced_composition: true },
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
      {currentProject && currentStep === 2 && voiceoverText && (
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

            {/* Upload area with drag & drop */}
            <div className="mb-6">
              <MaterialUploader
                onFilesSelected={handleFilesSelected}
                maxFiles={10}
                accept="image/*,video/*"
                disabled={uploadMaterialMutation.isPending}
              />
            </div>

            {/* Upload Preview */}
            <UploadPreview
              uploadingFiles={uploadingFiles}
              onRemove={handleRemoveUpload}
            />

            {/* Analysis status banner */}
            {analyzeStatus === 'pending' && (
              <div className="p-3 mb-4 bg-yellow-600/20 rounded">Анализ изображений в процессе...</div>
            )}
            {analyzeStatus === 'done' && (
              <div className="p-3 mb-4 bg-green-600/10 rounded">Анализ завершён — результаты отображены под превью.</div>
            )}
            {analyzeStatus === 'error' && (
              <div className="p-3 mb-4 bg-red-600/10 rounded">Ошибка анализа — проверьте логи.</div>
            )}

            {/* Materials Grid */}
            {currentProject.materials && currentProject.materials.length > 0 && (
              <div className="mt-6">
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
                    <div key={material.id} className="glass-card p-2 relative group">
                      <img
                        src={material.url}
                        alt="Material"
                        className="w-full h-32 object-cover rounded mb-2"
                      />
                      {material.analysis && (
                        <p className="text-xs text-white/60 line-clamp-3">{material.analysis}</p>
                      )}
                      
                      {/* Delete Button */}
                      <button
                        onClick={() => handleDeleteMaterial(material.id)}
                        disabled={deleteMaterialMutation.isPending}
                        className="absolute top-1 right-1 p-2 bg-red-600 hover:bg-red-700 
                                 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity
                                 disabled:opacity-50"
                        title="Удалить материал"
                      >
                        <Loader2 size={16} className={deleteMaterialMutation.isPending ? 'animate-spin' : 'hidden'} />
                        <span className={deleteMaterialMutation.isPending ? 'hidden' : 'block'}>✕</span>
                      </button>
                    </div>
                  ))}
                </div>

                {/* Next Step Button - Show after successful analysis */}
                {analyzeStatus === 'done' && currentStep === 3 && (
                  <div className="mt-6">
                    <button
                      onClick={() => {
                        if (currentProject) {
                          projectsApi
                            .updateStep(currentProject.id, 4)
                            .then(() => {
                              queryClient.invalidateQueries({ queryKey: ['projects'] })
                              setCurrentProject({ ...currentProject, current_step: 4 })
                            })
                        }
                      }}
                      className="btn-primary w-full flex items-center justify-center gap-2"
                    >
                      <Check size={20} />
                      Далее: Тайминги
                    </button>
                  </div>
                )}
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
                  {currentProject.timeline.map((segment: any, index: number) => {
                    // Find material by ID
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
                        ) : segment.material_id !== 'MISSING' ? (
                          <div className="w-32 shrink-0">
                            <div className="w-full h-20 bg-red-600/20 rounded flex items-center justify-center text-xs text-red-400">
                              Материал не найден
                            </div>
                          </div>
                        ) : (
                          <div className="w-32 shrink-0">
                            <div className="w-full h-20 bg-white/5 rounded flex items-center justify-center text-xs text-white/40">
                              Нет материала
                            </div>
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              )}

              {/* Next Step Button - Show after timeline is generated */}
              {currentProject.timeline && currentProject.timeline.length > 0 && currentStep === 4 && (
                <div className="mt-6">
                  <button
                    onClick={() => {
                      if (currentProject) {
                        projectsApi
                          .updateStep(currentProject.id, 5)
                          .then(() => {
                            queryClient.invalidateQueries({ queryKey: ['projects'] })
                            setCurrentProject({ ...currentProject, current_step: 5 })
                          })
                      }
                    }}
                    className="btn-primary w-full flex items-center justify-center gap-2"
                  >
                    <Check size={20} />
                    Далее: Генерация видео с аватаром
                  </button>
                </div>
              )}
            </div>
          )}
        </>
      )}

      {/* Future steps */}
      {currentProject && currentStep >= 5 && (
        <>
          {/* Step 5: Avatar Video Generation */}
          <div className="glass-card p-8 mb-6">
            <h3 className="text-xl font-bold mb-4">Этап 5: Генерация видео с аватаром</h3>

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
                  Сгенерировать видео (fal.ai InfiniTalk)
                </button>
                
                {generateAvatarMutation.isPending && (
                  <p className="text-center text-white/60 text-sm mt-3">
                    Генерация может занять 1-3 минуты...
                  </p>
                )}
              </div>
            ) : (
              <div>
                <video
                  src={currentProject.avatar_video_url}
                  controls
                  className="w-full rounded-lg mb-4"
                />
                <button
                  onClick={handleGenerateAvatar}
                  disabled={generateAvatarMutation.isPending}
                  className="btn-secondary w-full"
                >
                  Перегенерировать
                </button>
              </div>
            )}
          </div>

          {/* Step 6: Final Composition */}
          {currentStep >= 6 && currentProject.avatar_video_url && (
            <div className="glass-card p-8">
              <h3 className="text-xl font-bold mb-4">Этап 6: Финальный монтаж</h3>

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
                <div className="text-center">
                  <div className="mb-6">
                    <div className="inline-block p-4 bg-green-600/20 rounded-full mb-4">
                      <Check size={48} className="text-green-500" />
                    </div>
                    <h4 className="text-xl font-bold mb-2">Видео готово! 🎉</h4>
                    <p className="text-white/60">Проект успешно завершён</p>
                  </div>

                  <video
                    src={currentProject.final_video_url}
                    controls
                    className="w-full rounded-lg mb-4"
                  />

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
                      className="btn-secondary"
                    >
                      Пересобрать
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}
