"""Project API endpoints."""
from flask import request, jsonify
from app.api import bp
from app import db
from app.models import Project, Blogger
from app.utils.gpt_helper import gpt_helper
from app.utils.elevenlabs_helper import elevenlabs_helper


@bp.route('/projects', methods=['GET'])
def get_projects():
    """Get all projects."""
    projects = Project.query.order_by(Project.updated_at.desc()).all()
    return jsonify([project.to_dict() for project in projects])


@bp.route('/projects/<project_id>', methods=['GET'])
def get_project(project_id):
    """Get single project by ID."""
    project = Project.query.get_or_404(project_id)
    return jsonify(project.to_dict())


@bp.route('/projects', methods=['POST'])
def create_project():
    """Create new project."""
    data = request.get_json()
    
    blogger_id = data.get('blogger_id')
    if not blogger_id:
        return jsonify({'error': 'blogger_id is required'}), 400
    
    # Verify blogger exists
    blogger = Blogger.query.get(blogger_id)
    if not blogger:
        return jsonify({'error': 'Blogger not found'}), 404
    
    project = Project(
        blogger_id=blogger_id,
        status='draft',
        current_step=1
    )
    
    db.session.add(project)
    db.session.commit()
    
    return jsonify(project.to_dict()), 201


@bp.route('/projects/<project_id>', methods=['PUT'])
def update_project(project_id):
    """Update project."""
    project = Project.query.get_or_404(project_id)
    data = request.get_json()
    
    # Update allowed fields
    if 'scenario_text' in data:
        project.scenario_text = data['scenario_text']
    if 'voiceover_text' in data:
        project.voiceover_text = data['voiceover_text']
    if 'status' in data:
        project.status = data['status']
    if 'current_step' in data:
        project.current_step = data['current_step']
    
    db.session.commit()
    
    return jsonify(project.to_dict())


@bp.route('/projects/<project_id>/extract-text', methods=['POST'])
def extract_voiceover_text(project_id):
    """Extract voiceover text from scenario using GPT-4."""
    project = Project.query.get_or_404(project_id)
    
    if not project.scenario_text:
        return jsonify({'error': 'Scenario text is required'}), 400
    
    try:
        # Extract text using GPT
        voiceover_text = gpt_helper.extract_voiceover_text(project.scenario_text)
        
        # Save to project
        project.voiceover_text = voiceover_text
        project.current_step = 2
        db.session.commit()
        
        return jsonify({
            'voiceover_text': voiceover_text,
            'project': project.to_dict()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/projects/<project_id>/generate-audio', methods=['POST'])
def generate_audio(project_id):
    """Generate audio using ElevenLabs TTS."""
    project = Project.query.get_or_404(project_id)
    
    if not project.voiceover_text:
        return jsonify({'error': 'Voiceover text is required'}), 400
    
    if not project.blogger.elevenlabs_voice_id:
        return jsonify({'error': 'Blogger voice ID not configured'}), 400
    
    try:
        # Generate speech with timestamps
        result = elevenlabs_helper.generate_speech_with_timestamps(
            text=project.voiceover_text,
            voice_id=project.blogger.elevenlabs_voice_id
        )
        
        # Save to project
        project.audio_url = result['audio_url']
        project.audio_alignment = {
            'alignment': result.get('alignment'),
            'normalized_alignment': result.get('normalized_alignment')
        }
        project.current_step = 3
        db.session.commit()
        
        return jsonify({
            'audio_url': result['audio_url'],
            'alignment': result.get('alignment'),
            'project': project.to_dict()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/projects/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    """Delete project."""
    project = Project.query.get_or_404(project_id)
    
    # TODO: Delete associated files from S3
    
    db.session.delete(project)
    db.session.commit()
    
    return '', 204


@bp.route('/elevenlabs/voices', methods=['GET'])
def list_voices():
    """List available ElevenLabs voices."""
    try:
        voices = elevenlabs_helper.list_voices()
        return jsonify({'voices': voices})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
