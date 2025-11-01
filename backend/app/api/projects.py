"""Project API endpoints."""
from flask import Blueprint, request, jsonify
from app import db
from app.models import Project, Blogger
from app.utils import gpt_helper, elevenlabs_helper, s3_helper, falai_helper, ffmpeg_helper
from werkzeug.utils import secure_filename
import uuid

bp = Blueprint('projects', __name__, url_prefix='/projects')


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


@bp.route('/<project_id>/generate-audio', methods=['POST'])
def generate_audio(project_id):
    """Generate audio using ElevenLabs TTS"""
    project = Project.query.get_or_404(project_id)
    
    if not project.voiceover_text:
        return jsonify({'error': 'No voiceover text available'}), 400
    
    if not project.blogger.elevenlabs_voice_id:
        return jsonify({'error': 'Blogger has no ElevenLabs voice ID'}), 400
    
    try:
        result = elevenlabs_helper.generate_speech_with_timestamps(
            text=project.voiceover_text,
            voice_id=project.blogger.elevenlabs_voice_id
        )
        
        project.audio_url = result['audio_url']
        project.audio_alignment = {
            'alignment': result.get('alignment'),
            'audio_duration': result.get('audio_duration')
        }
        project.current_step = 3
        db.session.commit()
        
        return jsonify({
            'audio_url': result['audio_url'],
            'audio_duration': result.get('audio_duration'),
            'project': project.to_dict()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/<project_id>/upload-material', methods=['POST'])
def upload_material(project_id):
    """Upload material (image/video) for project"""
    project = Project.query.get_or_404(project_id)
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        # Upload to S3
        file_url = s3_helper.upload_file(file, 'materials')
        
        # Create material record
        material = {
            'id': str(uuid.uuid4()),
            'url': file_url,
            'type': request.form.get('type', 'image'),
            'filename': secure_filename(file.filename),
            'uploaded_at': str(db.func.now())
        }
        
        # Add to project materials
        if not project.materials:
            project.materials = []
        project.materials.append(material)
        db.session.commit()
        
        return jsonify({'material': material, 'project': project.to_dict()})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/<project_id>/analyze-materials', methods=['POST'])
def analyze_materials(project_id):
    """Analyze materials using GPT-4 Vision"""
    project = Project.query.get_or_404(project_id)
    
    if not project.materials:
        return jsonify({'error': 'No materials to analyze'}), 400
    
    try:
        # Get image URLs
        image_urls = [mat['url'] for mat in project.materials if mat.get('type') == 'image']
        
        # Analyze with GPT Vision
        analysis = gpt_helper.analyze_materials_with_vision(image_urls)
        
        # Update materials with analysis
        for i, mat in enumerate(project.materials):
            if mat.get('type') == 'image' and i < len(analysis.get('images', [])):
                mat.update(analysis['images'][i])
        
        db.session.commit()
        
        return jsonify({
            'analysis': analysis,
            'project': project.to_dict()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/<project_id>/generate-timeline', methods=['POST'])
def generate_timeline(project_id):
    """Generate video timeline using GPT"""
    project = Project.query.get_or_404(project_id)
    
    if not project.voiceover_text or not project.audio_alignment:
        return jsonify({'error': 'Audio must be generated first'}), 400
    
    if not project.materials:
        return jsonify({'error': 'Materials must be uploaded first'}), 400
    
    try:
        timeline = gpt_helper.generate_timeline(
            voiceover_text=project.voiceover_text,
            audio_alignment=project.audio_alignment,
            materials=project.materials
        )
        
        project.timeline = timeline
        project.current_step = 4
        db.session.commit()
        
        return jsonify({
            'timeline': timeline,
            'project': project.to_dict()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/<project_id>/generate-avatar-video', methods=['POST'])
def generate_avatar_video(project_id):
    """Generate talking avatar video using fal.ai InfiniTalk"""
    project = Project.query.get_or_404(project_id)
    
    if not project.audio_url:
        return jsonify({'error': 'Audio must be generated first'}), 400
    
    if not project.blogger.frontal_image_url:
        return jsonify({'error': 'Blogger has no frontal image'}), 400
    
    try:
        data = request.get_json() or {}
        expression_scale = data.get('expression_scale', 1.0)
        face_enhance = data.get('face_enhance', True)
        
        result = falai_helper.generate_avatar_video(
            audio_url=project.audio_url,
            image_url=project.blogger.frontal_image_url,
            expression_scale=expression_scale,
            face_enhance=face_enhance
        )
        
        project.avatar_video_url = result['video_url']
        project.avatar_generation_params = {
            'expression_scale': expression_scale,
            'face_enhance': face_enhance,
            'fal_request_id': result.get('request_id')
        }
        project.current_step = 5
        db.session.commit()
        
        return jsonify({
            'avatar_video_url': result['video_url'],
            'project': project.to_dict()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/<project_id>/check-avatar-status/<request_id>', methods=['GET'])
def check_avatar_status(project_id, request_id):
    """Check status of avatar video generation"""
    project = Project.query.get_or_404(project_id)
    
    try:
        status = falai_helper.check_status(request_id)
        
        if status.get('status') == 'completed' and status.get('video_url'):
            project.avatar_video_url = status['video_url']
            project.current_step = 5
            db.session.commit()
        
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/<project_id>/compose-final-video', methods=['POST'])
def compose_final_video(project_id):
    """Compose final video with FFmpeg"""
    project = Project.query.get_or_404(project_id)
    
    if not project.avatar_video_url:
        return jsonify({'error': 'Avatar video must be generated first'}), 400
    
    if not project.audio_url:
        return jsonify({'error': 'Audio is required'}), 400
    
    try:
        data = request.get_json() or {}
        add_subtitles = data.get('add_subtitles', False)
        advanced_composition = data.get('advanced_composition', False)
        
        output_filename = f"final_{project_id}.mp4"
        
        # Create composition
        if advanced_composition and project.timeline:
            video_path = ffmpeg_helper.create_advanced_composition(
                avatar_video_url=project.avatar_video_url,
                audio_url=project.audio_url,
                timeline=project.timeline,
                materials=project.materials or [],
                output_filename=output_filename
            )
        else:
            video_path = ffmpeg_helper.create_video_composition(
                avatar_video_url=project.avatar_video_url,
                audio_url=project.audio_url,
                timeline=project.timeline or [],
                materials=project.materials or [],
                output_filename=output_filename
            )
        
        # Add subtitles if requested
        if add_subtitles and project.voiceover_text and project.audio_alignment:
            video_path = ffmpeg_helper.add_subtitles(
                video_path=video_path,
                voiceover_text=project.voiceover_text,
                audio_alignment=project.audio_alignment,
                output_filename=f"final_subs_{project_id}.mp4"
            )
        
        # Upload to S3
        with open(video_path, 'rb') as f:
            final_video_url = s3_helper.upload_file(f, 'final_videos')
        
        project.final_video_url = final_video_url
        project.status = 'completed'
        project.current_step = 6
        db.session.commit()
        
        return jsonify({
            'final_video_url': final_video_url,
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
