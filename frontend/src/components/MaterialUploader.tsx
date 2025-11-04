import { useState, useRef } from 'react'
import type { DragEvent } from 'react'
import { Upload, X, CheckCircle, Loader2, AlertCircle } from 'lucide-react'

export interface UploadingFile {
  id: string
  file: File
  preview: string
  status: 'uploading' | 'success' | 'error'
  progress: number
  error?: string
}

interface MaterialUploaderProps {
  onFilesSelected: (files: File[]) => void
  maxFiles?: number
  accept?: string
  disabled?: boolean
}

export default function MaterialUploader({
  onFilesSelected,
  maxFiles = 10,
  accept = 'image/*,video/*',
  disabled = false,
}: MaterialUploaderProps) {
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    if (!disabled) {
      setIsDragging(true)
    }
  }

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)

    if (disabled) return

    const files = Array.from(e.dataTransfer.files).slice(0, maxFiles)
    if (files.length > 0) {
      onFilesSelected(files)
    }
  }

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      const fileArray = Array.from(files).slice(0, maxFiles)
      onFilesSelected(fileArray)
    }
    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const handleClick = () => {
    if (!disabled) {
      fileInputRef.current?.click()
    }
  }

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={handleClick}
      className={`
        border-2 border-dashed rounded-lg p-8 text-center 
        transition-all duration-300 cursor-pointer
        ${isDragging 
          ? 'border-blue-500 bg-blue-500/10 scale-105' 
          : 'border-white/20 hover:border-blue-500/50 hover:bg-white/5'
        }
        ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
      `}
    >
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept={accept}
        onChange={handleFileInput}
        className="hidden"
        disabled={disabled}
      />
      
      <Upload 
        size={48} 
        className={`mx-auto mb-4 transition-colors ${
          isDragging ? 'text-blue-400' : 'text-white/40'
        }`} 
      />
      
      <p className="text-white/80 mb-2 font-medium">
        {isDragging ? 'Отпустите файлы здесь' : 'Перетащите файлы или нажмите для выбора'}
      </p>
      
      <p className="text-sm text-white/40">
        Поддержка изображений и видео (до {maxFiles} файлов)
      </p>
    </div>
  )
}

interface UploadPreviewProps {
  uploadingFiles: UploadingFile[]
  onRemove?: (id: string) => void
}

export function UploadPreview({ uploadingFiles, onRemove }: UploadPreviewProps) {
  if (uploadingFiles.length === 0) return null

  return (
    <div className="space-y-3">
      <h4 className="font-bold text-sm text-white/80">Загрузка файлов</h4>
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {uploadingFiles.map((upload) => (
          <div key={upload.id} className="glass-card p-2 relative group">
            {/* Preview Image */}
            <div className="relative w-full h-32 mb-2 rounded overflow-hidden bg-white/5">
              <img
                src={upload.preview}
                alt={upload.file.name}
                className="w-full h-full object-cover"
              />
              
              {/* Status Overlay */}
              {upload.status === 'uploading' && (
                <div className="absolute inset-0 bg-black/60 flex items-center justify-center">
                  <div className="text-center">
                    <Loader2 size={24} className="animate-spin mx-auto mb-2 text-blue-400" />
                    <div className="text-xs text-white/80">{upload.progress}%</div>
                  </div>
                </div>
              )}
              
              {upload.status === 'success' && (
                <div className="absolute top-2 right-2 bg-green-600 rounded-full p-1">
                  <CheckCircle size={16} className="text-white" />
                </div>
              )}
              
              {upload.status === 'error' && (
                <div className="absolute inset-0 bg-black/60 flex items-center justify-center">
                  <div className="text-center px-2">
                    <AlertCircle size={24} className="mx-auto mb-2 text-red-400" />
                    <div className="text-xs text-white/80">Ошибка</div>
                  </div>
                </div>
              )}
            </div>
            
            {/* File Info */}
            <div className="text-xs text-white/60 truncate mb-1">
              {upload.file.name}
            </div>
            
            <div className="text-xs text-white/40">
              {(upload.file.size / 1024 / 1024).toFixed(2)} MB
            </div>
            
            {/* Remove Button */}
            {onRemove && upload.status === 'error' && (
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  onRemove(upload.id)
                }}
                className="absolute top-1 right-1 p-1 bg-red-600 hover:bg-red-700 rounded-full 
                         opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <X size={14} />
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
