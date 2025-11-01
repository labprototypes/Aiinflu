# Aiinflu - AI Content Automation Platform

Автоматизация создания видео-контента с помощью AI: голосовая озвучка, аватары, монтаж.

## 🚀 Основные возможности

- **Управление блогерами**: Создание профилей подкастеров с фото, голосами, стилем
- **6-этапный workflow**: От сценария до финального видео
- **AI-генерация**:
  - GPT-4 для извлечения текста и анализа материалов
  - ElevenLabs для синтеза речи с таймкодами
  - fal.ai InfiniTalk для создания говорящих аватаров
  - TMDB API для кросс-языкового поиска фильмов
- **Автоматический монтаж**: FFmpeg композитинг с субтитрами
- **Glassmorphism UI**: Дизайн в стиле Apple

## 📁 Структура проекта

```
Aiinflu/
├── backend/              # Flask API
│   ├── app/
│   │   ├── api/         # REST endpoints (blueprints)
│   │   ├── models.py    # SQLAlchemy models
│   │   └── utils/       # S3, AI helpers
│   ├── migrations/      # Alembic DB migrations
│   ├── config.py
│   ├── run.py
│   └── requirements.txt
├── frontend/            # React + TypeScript
│   ├── src/
│   │   ├── components/  # UI components
│   │   ├── pages/       # Route pages
│   │   ├── lib/         # API client
│   │   └── types/       # TypeScript types
│   ├── package.json
│   └── vite.config.ts
└── render.yaml          # Render deployment blueprint
```

## 🛠️ Технологический стек

### Backend
- **Flask 3.0** - Web framework
- **SQLAlchemy** + **PostgreSQL** - ORM и база данных
- **Flask-Migrate** - Database migrations
- **boto3** - AWS S3 для хранения медиафайлов
- **OpenAI GPT-4** - Анализ текста и материалов
- **ElevenLabs** - Text-to-Speech с таймкодами
- **fal.ai** - Генерация говорящих аватаров
- **FFmpeg** - Видеомонтаж

### Frontend
- **React 18** + **TypeScript**
- **Vite** - Build tool
- **TailwindCSS** - Glassmorphism стили
- **React Query** - Server state
- **React Router** - Routing
- **Framer Motion** - Animations
- **axios** - HTTP client

## 📦 Установка и запуск

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Настройка переменных окружения
cp .env.example .env
# Отредактируйте .env с вашими API ключами

# База данных
export FLASK_APP=run.py
flask db upgrade

# Запуск
python run.py
# API: http://localhost:5000
```

### Frontend

```bash
cd frontend
npm install

# Настройка
cp .env.example .env

# Запуск dev сервера
npm run dev
# UI: http://localhost:3000
```

## 🌐 Deployment на Render

1. **Подключите GitHub репозиторий** к Render
2. **Blueprint deployment**: Render автоматически обнаружит `render.yaml`
3. **Настройте environment variables**:
   - AWS credentials (S3)
   - OpenAI API key
   - ElevenLabs API key
   - fal.ai API key
   - TMDB API key
4. **Deploy** - Render создаст:
   - PostgreSQL database
   - Backend web service (Flask)
   - Frontend static site (React)

## 🔑 Необходимые API ключи

- **AWS S3**: Access Key ID, Secret Access Key, Bucket name
- **OpenAI**: API key для GPT-4
- **ElevenLabs**: API key для TTS
- **fal.ai**: API key для InfiniTalk
- **TMDB**: API key для поиска фильмов (опционально)

## 📝 API Endpoints

### Bloggers
- `GET /api/bloggers` - Список блогеров
- `POST /api/bloggers` - Создать блогера (multipart/form-data)
- `GET /api/bloggers/:id` - Получить блогера
- `PUT /api/bloggers/:id` - Обновить блогера
- `DELETE /api/bloggers/:id` - Удалить блогера

### Projects
- `GET /api/projects` - Список проектов
- `GET /api/projects/:id` - Получить проект
- `POST /api/projects` - Создать проект
- `PUT /api/projects/:id` - Обновить проект
- *Больше endpoints в разработке...*

## 🎨 Дизайн система

- **Glassmorphism**: Эффект frosted glass с backdrop-blur
- **Цвета**: Dark gradient (slate-950 → slate-900), Blue-600, Purple-400
- **Шрифты**: -apple-system, SF Pro Display стиль
- **Анимации**: Smooth transitions 300ms
- **Компоненты**: glass-card, btn-primary, btn-secondary, input-glass

## 🔄 Workflow создания контента

1. **Подготовка**: Выбор блогера, ввод сценария
2. **Озвучка**: GPT извлекает текст → ElevenLabs генерирует аудио
3. **Материалы**: Загрузка изображений/видео
4. **Тайминги**: GPT анализирует и создает timeline
5. **Генерация**: fal.ai создает говорящий аватар
6. **Монтаж**: FFmpeg композитинг + субтитры

## 📄 License

MIT

## 👥 Команда

labprototypes © 2025