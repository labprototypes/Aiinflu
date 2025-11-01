export interface Blogger {
  id: string
  name: string
  type: string
  frontal_image_url?: string
  location_image_url?: string
  tone_of_voice?: string
  elevenlabs_voice_id: string
  is_active: boolean
  created_at: string
}

export interface Project {
  id: string
  blogger_id: string
  blogger?: Blogger
  status: 'draft' | 'in_progress' | 'completed'
  current_step: number
  scenario_text?: string
  voiceover_text?: string
  audio_url?: string
  audio_alignment?: any
  materials?: any[]
  timeline?: any[]
  avatar_video_url?: string
  avatar_generation_params?: any
  final_video_url?: string
  created_at: string
  updated_at: string
}
