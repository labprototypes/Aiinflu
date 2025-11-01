"""Database models."""
import uuid
from datetime import datetime
from app import db
from sqlalchemy.dialects.postgresql import UUID, JSON


class Blogger(db.Model):
    """Blogger/Podcaster model."""
    
    __tablename__ = 'bloggers'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(50), nullable=False, default='podcaster')  # podcaster, youtuber, etc.
    
    # Images stored in S3
    frontal_image_url = db.Column(db.String(512))  # Фронтальное фото
    location_image_url = db.Column(db.String(512))  # Блогер в локации
    
    # Voice settings
    tone_of_voice = db.Column(db.Text)  # Описание стиля и тона
    elevenlabs_voice_id = db.Column(db.String(255))  # Voice ID from ElevenLabs
    
    # Metadata
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    projects = db.relationship('Project', backref='blogger', lazy='dynamic')
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            'id': str(self.id),
            'name': self.name,
            'type': self.type,
            'frontal_image_url': self.frontal_image_url,
            'location_image_url': self.location_image_url,
            'tone_of_voice': self.tone_of_voice,
            'elevenlabs_voice_id': self.elevenlabs_voice_id,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class Project(db.Model):
    """Content creation project model."""
    
    __tablename__ = 'projects'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    blogger_id = db.Column(UUID(as_uuid=True), db.ForeignKey('bloggers.id'), nullable=False)
    
    # Status and progress
    status = db.Column(db.String(20), default='draft')  # draft, in_progress, completed
    current_step = db.Column(db.Integer, default=1)  # 1-6 steps
    
    # Step 1: Scenario
    scenario_text = db.Column(db.Text)
    
    # Step 2: Voiceover
    voiceover_text = db.Column(db.Text)  # Extracted text for TTS
    audio_url = db.Column(db.String(512))  # Generated audio from ElevenLabs
    audio_alignment = db.Column(JSON)  # Timestamps from ElevenLabs
    
    # Step 3: Materials
    materials = db.Column(JSON)  # List of uploaded files with metadata
    
    # Step 4: Timeline
    timeline = db.Column(JSON)  # Montage timeline with timecodes
    
    # Step 5: Avatar video
    avatar_video_url = db.Column(db.String(512))  # From fal.ai InfiniTalk
    avatar_generation_params = db.Column(JSON)  # Parameters used for generation
    
    # Step 6: Final video
    final_video_url = db.Column(db.String(512))  # Final composed video with subtitles
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            'id': str(self.id),
            'blogger_id': str(self.blogger_id),
            'blogger': self.blogger.to_dict() if self.blogger else None,
            'status': self.status,
            'current_step': self.current_step,
            'scenario_text': self.scenario_text,
            'voiceover_text': self.voiceover_text,
            'audio_url': self.audio_url,
            'audio_alignment': self.audio_alignment,
            'materials': self.materials,
            'timeline': self.timeline,
            'avatar_video_url': self.avatar_video_url,
            'avatar_generation_params': self.avatar_generation_params,
            'final_video_url': self.final_video_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
