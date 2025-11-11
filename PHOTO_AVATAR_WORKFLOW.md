# Photo Avatar Workflow

## 🎯 Автоматическое создание HeyGen Photo Avatar

Когда `heygen_avatar_id` в локации = `"00000"`, система автоматически создает Photo Avatar через HeyGen API.

## 📋 Workflow

### 1. **Upload Asset**
```
POST /v1/asset
Body: { "url": "https://s3.../location-image.png" }
Response: { "data": { "image_key": "image/abc123/original" } }
```

### 2. **Create Avatar Group**
```
POST /v2/photo_avatar/avatar_group/create
Body: {
  "name": "Blogger Name - Location Name",
  "image_key": "image/abc123/original"
}
Response: {
  "data": {
    "group_id": "0711b7c97f844dda9fa8acab475beda0",
    "avatar_id": "c231e947600b428e92d540ca9c48596a"
  }
}
```

### 3. **Add Motion**
```
POST /v1/photo_avatar.add_motion
Body: {
  "avatar_id": "c231e947600b428e92d540ca9c48596a",
  "type": "veo2"
}
Response: { "data": { "status": "processing" } }
```

### 4. **Save avatar_id**
Сохраняем `avatar_id` в `blogger.settings.locations[].heygen_avatar_id` для переиспользования.

## 🔧 Конфигурация

### Motion Types
- `veo2` - Google Veo 2 (рекомендуется)
- `seedance` - SeeKing Dance
- `runway_gen3` - Runway Gen-3
- `runway_gen4` - Runway Gen-4
- `minimax_hailuo_v1` - Minimax Hailuo 1
- `minimax_hailuo_v2` - Minimax Hailuo 2
- `kling` - Kling AI

**Note:** Legacy `avatar_iv` не поддерживается и вернет ошибку.

## ⚙️ Код

### Backend: `heygen_helper.py`
```python
# 1. Upload asset
image_key = HeyGenHelper.upload_asset(image_url)

# 2. Create avatar group
result = HeyGenHelper.create_photo_avatar_group("Avatar Name", image_key)
avatar_id = result['avatar_id']
group_id = result['group_id']

# 3. Add motion
HeyGenHelper.add_motion_to_avatar(avatar_id, motion_type='veo2')
```

### Backend: `projects.py`
При генерации видео:
1. Проверяет `heygen_avatar_id` в выбранной локации
2. Если `"00000"` → автоматически создает Photo Avatar
3. Сохраняет `avatar_id` обратно в локацию
4. Использует `avatar_id` для генерации видео

## 💰 API Credits Cost

| Operation | Credits | Note |
|-----------|---------|------|
| Upload Asset | Free | - |
| Create Group | Free | Только создание |
| Add Motion | **1 credit** | За каждый вызов |
| Train Group | **4 credits** | НЕ используем |
| Generate Video | **0.2 credits/min** | Photo Avatar тариф |

**Наш расход:** 1 credit на motion + 0.2 credits/min за видео

## 📊 Free Plan Limits

- **3 Avatar Groups** максимум
- **1 минута видео** в месяц бесплатно
- **720p качество**
- **С watermark** (логотип HeyGen)

## 🎥 Использование

### Первая генерация (avatar_id = "00000"):
1. Система загружает фото локации
2. Создает Avatar Group
3. Добавляет motion (жестикуляция)
4. Сохраняет `avatar_id` в БД
5. Генерирует видео

**Время:** ~30-60 секунд на создание avatar

### Последующие генерации:
1. Использует сохраненный `avatar_id`
2. Сразу генерирует видео

**Время:** ~10-30 секунд на видео

## 🔍 Проверка статуса

### Проверить детали avatar:
```
GET /v2/photo_avatar/{avatar_id}
Response: {
  "data": {
    "avatar_id": "...",
    "group_id": "...",
    "status": "completed",
    "motion_status": "completed"
  }
}
```

## ⚠️ Важные ограничения

1. **БЕЗ тренировки** - мы не используем `/v2/photo_avatar/train`
2. **Один look на avatar** - не генерируем дополнительные looks
3. **Простая жестикуляция** - только базовый motion через `veo2`
4. **Free plan** - максимум 3 Avatar Groups

## 🚀 Roadmap

### Если нужно больше функций:

**Вариант 1: Множественные looks**
```python
# Добавить дополнительные фото в группу
HeyGenHelper.add_looks_to_group(group_id, [image_key1, image_key2])
```

**Вариант 2: Тренировка для консистентности**
```python
# Тренировать группу для лучшего качества
HeyGenHelper.train_avatar_group(group_id)
# Стоит 4 credits
```

**Вариант 3: Генерация AI looks**
```python
# Создать AI-сгенерированные варианты
HeyGenHelper.generate_avatar_looks(
    group_id=group_id,
    prompt="White shirt, professional setting",
    pose="half_body",
    style="Realistic"
)
# Стоит 1 credit за look
```

## 📝 Логи

### Успешное создание:
```
>>> Avatar ID not configured, creating Photo Avatar automatically...
>>> Step 1: Uploading asset to HeyGen...
>>> Asset uploaded, image_key: image/abc123/original
>>> Step 2: Creating Photo Avatar Group...
>>> Avatar created: avatar_id=c231e947600b428e92d540ca9c48596a, group_id=0711b7c97f844dda
>>> Step 3: Adding motion to avatar...
>>> Motion added successfully
>>> Saved avatar_id to location for future use
>>> Photo Avatar created successfully: c231e947600b428e92d540ca9c48596a
```

### Ошибки:
- `Asset upload failed` - проблема с URL изображения
- `Avatar group creation failed` - превышен лимит групп (3 на Free)
- `Add motion failed` - неверный motion_type или лимит credits

## 🎓 Дополнительные ресурсы

- [HeyGen Photo Avatars Docs](https://docs.heygen.com/docs/photo-avatars-api)
- [API Reference](https://docs.heygen.com/reference/create-photo-avatar-group)
- [Motion Types](https://docs.heygen.com/reference/add-motion)
