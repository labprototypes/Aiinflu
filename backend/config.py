"""Application configuration."""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration."""
    
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///aiinflu.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # SQLAlchemy connection pool settings (fix SSL errors)
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,  # Test connection before using
        'pool_recycle': 300,    # Recycle connections after 5 minutes
        'pool_size': 10,        # Max connections in pool
        'max_overflow': 20,     # Max overflow connections
        'connect_args': {
            'connect_timeout': 10,  # Connection timeout
            'options': '-c statement_timeout=30000'  # 30s query timeout
        }
    }
    
    # AWS S3
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_S3_BUCKET = os.environ.get('AWS_S3_BUCKET')
    AWS_REGION = os.environ.get('AWS_REGION', 'us-east-2')
    
    # External APIs
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    ELEVENLABS_API_KEY = os.environ.get('ELEVENLABS_API_KEY')
    FAL_KEY = os.environ.get('FAL_KEY')
    TMDB_API_KEY = os.environ.get('TMDB_API_KEY')
    
    # Celery (for future async tasks)
    CELERY_BROKER_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
