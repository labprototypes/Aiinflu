# Aiinflu - AI Content Automation Service

Backend for content creation automation service with blogger management and AI-powered video generation.

## Setup

1. Create virtual environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. Initialize database:
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

5. Run development server:
```bash
python run.py
```

## API Endpoints

### Bloggers
- `GET /api/bloggers` - List all bloggers
- `GET /api/bloggers/<id>` - Get blogger by ID
- `POST /api/bloggers` - Create new blogger
- `PUT /api/bloggers/<id>` - Update blogger
- `DELETE /api/bloggers/<id>` - Delete blogger

### Projects
- `GET /api/projects` - List all projects
- `GET /api/projects/<id>` - Get project by ID
- More endpoints coming soon...

## Stack

- Flask 3.0
- PostgreSQL
- SQLAlchemy ORM
- AWS S3 for media storage
- ElevenLabs for TTS
- OpenAI GPT-4 for content analysis
- fal.ai for video generation
