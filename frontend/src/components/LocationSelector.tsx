import { useState } from 'react'
import { MapPin, Check } from 'lucide-react'
import type { Blogger } from '@/types'

interface LocationSelectorProps {
  blogger: Blogger
  selectedLocationId: number | null
  onSelect: (locationId: number | null) => void
}

export default function LocationSelector({ blogger, selectedLocationId, onSelect }: LocationSelectorProps) {
  const locations = blogger.locations || []
  const hasLocations = locations.length > 0

  return (
    <div className="glass-card p-8">
      <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
        <MapPin size={24} />
        Выберите локацию для блогера
      </h3>

      {!hasLocations ? (
        <div className="text-center py-8">
          <p className="text-white/60 mb-4">
            У блогера "{blogger.name}" нет добавленных локаций.
          </p>
          <p className="text-sm text-white/40">
            Можно использовать основное фронтальное фото или добавить локации в настройках блогера.
          </p>
          <button
            onClick={() => onSelect(null)}
            className="btn-primary mt-6"
          >
            Использовать основное фото
          </button>
        </div>
      ) : (
        <>
          <p className="text-white/60 mb-6">
            Выберите изображение блогера в локации, которое будет использовано для генерации видео.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            {/* Default frontal image option */}
            <button
              onClick={() => onSelect(null)}
              className={`glass-card p-4 text-left transition-smooth relative ${
                selectedLocationId === null
                  ? 'ring-2 ring-blue-500 bg-blue-600/20'
                  : 'hover:bg-white/10'
              }`}
            >
              {selectedLocationId === null && (
                <div className="absolute top-2 right-2 bg-blue-500 rounded-full p-1">
                  <Check size={16} />
                </div>
              )}
              {blogger.frontal_image_url && (
                <img
                  src={blogger.frontal_image_url}
                  alt="Основное фото"
                  className="w-full h-40 object-cover rounded-lg mb-3"
                />
              )}
              <h4 className="font-bold">Основное фото</h4>
              <p className="text-xs text-white/60 mt-1">
                HeyGen ID: {blogger.heygen_avatar_id || '00000'}
              </p>
              {(!blogger.heygen_avatar_id || blogger.heygen_avatar_id === '00000') && (
                <p className="text-xs text-red-400 mt-1">⚠️ Avatar ID не настроен</p>
              )}
            </button>

            {/* Location options */}
            {locations.map((location) => (
              <button
                key={location.id}
                onClick={() => onSelect(location.id)}
                className={`glass-card p-4 text-left transition-smooth relative ${
                  selectedLocationId === location.id
                    ? 'ring-2 ring-blue-500 bg-blue-600/20'
                    : 'hover:bg-white/10'
                }`}
              >
                {selectedLocationId === location.id && (
                  <div className="absolute top-2 right-2 bg-blue-500 rounded-full p-1">
                    <Check size={16} />
                  </div>
                )}
                {location.image_url && (
                  <img
                    src={location.image_url}
                    alt={location.name}
                    className="w-full h-40 object-cover rounded-lg mb-3"
                  />
                )}
                <h4 className="font-bold">{location.name}</h4>
                <p className="text-xs text-white/60 mt-1">
                  HeyGen ID: {location.heygen_avatar_id || '00000'}
                </p>
                {(!location.heygen_avatar_id || location.heygen_avatar_id === '00000') && (
                  <p className="text-xs text-red-400 mt-1">⚠️ Avatar ID не настроен</p>
                )}
              </button>
            ))}
          </div>

          {selectedLocationId !== undefined && (
            <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4 mb-4">
              <p className="text-sm text-yellow-200">
                💡 Убедитесь, что для выбранной локации настроен HeyGen Avatar ID. 
                Без него генерация видео будет невозможна.
              </p>
            </div>
          )}
        </>
      )}
    </div>
  )
}
