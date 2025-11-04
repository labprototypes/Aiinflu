import { useState, useRef } from 'react'
import type { DragEvent, ChangeEvent } from 'react'
import { Upload, X } from 'lucide-react'

interface ImageDropzoneProps {
  value?: string // Preview URL
  onChange: (file: File) => void
  onClear?: () => void
  label?: string
  height?: string
  disabled?: boolean
}

export default function ImageDropzone({
  value,
  onChange,
  onClear,
  label = 'Изображение',
  height = 'h-48',
  disabled = false,
}: ImageDropzoneProps) {
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

    const files = Array.from(e.dataTransfer.files)
    const imageFile = files.find((file) => file.type.startsWith('image/'))
    
    if (imageFile) {
      onChange(imageFile)
    }
  }

  const handleFileInput = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file && file.type.startsWith('image/')) {
      onChange(file)
    }
    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const handleClick = () => {
    if (!disabled && !value) {
      fileInputRef.current?.click()
    }
  }

  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (onClear) {
      onClear()
    }
  }

  return (
    <div>
      {label && (
        <label className="block text-sm font-medium mb-2">{label}</label>
      )}
      
      <div className="glass-card p-4">
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleFileInput}
          className="hidden"
          disabled={disabled}
        />

        {value ? (
          // Preview with image
          <div className="relative">
            <img 
              src={value} 
              alt="Preview" 
              className={`w-full ${height} object-cover rounded-lg`} 
            />
            {!disabled && onClear && (
              <button
                type="button"
                onClick={handleClear}
                className="absolute top-2 right-2 bg-red-500 hover:bg-red-600 text-white p-2 
                         rounded-lg transition-smooth shadow-lg"
              >
                <X size={16} />
              </button>
            )}
            {!disabled && (
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="absolute bottom-2 right-2 bg-blue-600 hover:bg-blue-700 text-white 
                         px-3 py-1 text-sm rounded-lg transition-smooth shadow-lg"
              >
                Изменить
              </button>
            )}
          </div>
        ) : (
          // Upload area
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={handleClick}
            className={`
              cursor-pointer flex flex-col items-center justify-center ${height}
              border-2 border-dashed rounded-lg transition-all duration-300
              ${isDragging 
                ? 'border-blue-500 bg-blue-500/10 scale-105' 
                : 'border-white/20 hover:border-blue-500/50 hover:bg-white/5'
              }
              ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
            `}
          >
            <Upload 
              size={32} 
              className={`mb-2 transition-colors ${
                isDragging ? 'text-blue-400' : 'text-white/40'
              }`} 
            />
            <span className="text-white/60 text-sm">
              {isDragging ? 'Отпустите изображение' : 'Нажмите или перетащите'}
            </span>
            <span className="text-white/40 text-xs mt-1">
              PNG, JPG, WebP до 10MB
            </span>
          </div>
        )}
      </div>
    </div>
  )
}
