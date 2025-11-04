"""Project API endpoints."""
from flask import request, jsonify
from app import db
from app.models import Project, Blogger
from app.utils.gpt_helper import gpt_helper
from app.utils.elevenlabs_helper import elevenlabs_helper
from app.utils.s3_helper import s3_helper
from app.utils.falai_helper import falai_helper
from app.utils.ffmpeg_helper import ffmpeg_helper
from werkzeug.utils import secure_filename
import uuid
from app.api import bp


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
    from flask import current_app
    project = Project.query.get_or_404(project_id)
    data = request.get_json()
    
    current_app.logger.info(f"Updating project {project_id} with data: {data}")
    
    # Update allowed fields
    if 'scenario_text' in data:
        project.scenario_text = data['scenario_text']
        current_app.logger.info(f"Updated scenario_text: {data['scenario_text'][:100]}...")
    if 'voiceover_text' in data:
        project.voiceover_text = data['voiceover_text']
    if 'status' in data:
        project.status = data['status']
    if 'current_step' in data:
        project.current_step = data['current_step']
    
    try:
        db.session.commit()
        current_app.logger.info(f"Project {project_id} updated successfully")
    except Exception as e:
        current_app.logger.error(f"Failed to update project: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
    return jsonify(project.to_dict())


@bp.route('/projects/<project_id>/extract-text', methods=['POST'])
def extract_voiceover_text(project_id):
    """Extract voiceover text from scenario using GPT-4."""
    from flask import current_app
    project = Project.query.get_or_404(project_id)
    
    current_app.logger.info(f"Extracting text for project {project_id}")
    
    if not project.scenario_text:
        return jsonify({'error': 'Scenario text is required'}), 400
    
    try:
        # Extract text using GPT
        current_app.logger.info("Calling GPT-4 for text extraction")
        voiceover_text = gpt_helper.extract_voiceover_text(project.scenario_text)
        
        # Save to project
        project.voiceover_text = voiceover_text
        project.current_step = 2
        db.session.commit()
        
        current_app.logger.info(f"Text extracted successfully for project {project_id}")
        
        return jsonify({
            'voiceover_text': voiceover_text,
            'project': project.to_dict()
        })
    
    except Exception as e:
        current_app.logger.error(f"Text extraction failed: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@bp.route('/projects/<project_id>/generate-audio', methods=['POST'])
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
        # Don't auto-advance step - let user approve the audio first
        db.session.commit()
        
        return jsonify({
            'audio_url': result['audio_url'],
            'audio_duration': result.get('audio_duration'),
            'project': project.to_dict()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/projects/<project_id>/upload-material', methods=['POST'])
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
        
        # IMPORTANT: Create new list to trigger SQLAlchemy update for JSON field
        materials_list = list(project.materials) if project.materials else []
        materials_list.append(material)
        project.materials = materials_list
        
        db.session.commit()
        
        return jsonify({'material': material, 'project': project.to_dict()})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/projects/<project_id>/materials/<material_id>', methods=['DELETE'])
def delete_material(project_id, material_id):
    """Delete material from project"""
    project = Project.query.get_or_404(project_id)
    
    if not project.materials:
        return jsonify({'error': 'No materials found'}), 404
    
    try:
        # Find and remove material
        material_to_delete = None
        for mat in project.materials:
            if mat.get('id') == material_id:
                material_to_delete = mat
                break
        
        if not material_to_delete:
            return jsonify({'error': 'Material not found'}), 404
        
        # Delete from S3
        s3_helper.delete_file(material_to_delete['url'])
        
        # Remove from project
        project.materials = [mat for mat in project.materials if mat.get('id') != material_id]
        db.session.commit()
        
        return jsonify({'success': True, 'project': project.to_dict()})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/projects/<project_id>/analyze-materials', methods=['POST'])
def analyze_materials(project_id):
    """Analyze materials using GPT-4 Vision"""
    from flask import current_app
    project = Project.query.get_or_404(project_id)
    
    if not project.materials:
        return jsonify({'error': 'No materials to analyze'}), 400
    
    try:
        # Get image URLs
        image_urls = [mat['url'] for mat in project.materials if mat.get('type') == 'image']
        
        if not image_urls:
            return jsonify({'error': 'No images to analyze'}), 400
        
        current_app.logger.info(f"Analyzing {len(image_urls)} images")
        
        # Analyze with GPT Vision - returns list of dicts
        analysis_results = gpt_helper.analyze_materials_with_vision(image_urls)
        
        current_app.logger.info(f"Analysis complete: {len(analysis_results)} results")
        
        # Update materials with analysis
        url_to_analysis = {result['url']: result.get('analysis') for result in analysis_results}
        
        # IMPORTANT: Create new list to trigger SQLAlchemy update for JSON field
        updated_materials = []
        for mat in project.materials:
            mat_copy = dict(mat)
            if mat.get('type') == 'image' and mat['url'] in url_to_analysis:
                mat_copy['analysis'] = url_to_analysis[mat['url']]
            updated_materials.append(mat_copy)
        
        project.materials = updated_materials
        db.session.commit()
        
        return jsonify({
            'success': True,
            'analyzed_count': len(analysis_results),
            'project': project.to_dict()
        })
    except Exception as e:
        current_app.logger.error(f"Analysis failed: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@bp.route('/projects/<project_id>/generate-timeline', methods=['POST'])
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


@bp.route('/projects/<project_id>/generate-avatar-video', methods=['POST'])
def generate_avatar_video(project_id):
    """Generate talking avatar video using fal.ai InfiniTalk (async)"""
    project = Project.query.get_or_404(project_id)
    
    if not project.audio_url:
        return jsonify({'error': 'Audio must be generated first'}), 400
    
    if not project.blogger.frontal_image_url:
        return jsonify({'error': 'Blogger has no frontal image'}), 400
    
    try:
        data = request.get_json() or {}
        expression_scale = data.get('expression_scale', 1.0)
        face_enhance = data.get('face_enhance', True)
        
        # Start async generation (returns immediately with request_id)
        result = falai_helper.start_avatar_generation(
            audio_url=project.audio_url,
            image_url=project.blogger.frontal_image_url,
            expression_scale=expression_scale,
            face_enhance=face_enhance
        )
        
        # Save request_id for status polling
        project.avatar_generation_params = {
            'expression_scale': expression_scale,
            'face_enhance': face_enhance,
            'fal_request_id': result['request_id'],
            'status': 'processing'
        }
        db.session.commit()
        
        return jsonify({
            'request_id': result['request_id'],
            'status': 'processing',
            'message': 'Avatar video generation started. Use check-avatar-status to poll for completion.',
            'project': project.to_dict()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/projects/<project_id>/check-avatar-status/<request_id>', methods=['GET'])
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


@bp.route('/projects/<project_id>/compose-final-video', methods=['POST'])
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
