"""Project API endpoints."""
from flask import request, jsonify, current_app
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
    from flask import current_app
    project = Project.query.get_or_404(project_id)
    
    print("=" * 80)
    print("=== GENERATE AVATAR VIDEO CALLED ===")
    print(f"Project ID: {project_id}")
    print(f"Audio URL: {project.audio_url}")
    print(f"Blogger Image URL: {project.blogger.frontal_image_url if project.blogger else 'NO BLOGGER'}")
    print("=" * 80)
    
    current_app.logger.info(f"=== GENERATE AVATAR VIDEO CALLED ===")
    current_app.logger.info(f"Project ID: {project_id}")
    current_app.logger.info(f"Audio URL: {project.audio_url}")
    current_app.logger.info(f"Blogger Image URL: {project.blogger.frontal_image_url if project.blogger else 'NO BLOGGER'}")
    
    if not project.audio_url:
        return jsonify({'error': 'Audio must be generated first'}), 400
    
    if not project.blogger.frontal_image_url:
        return jsonify({'error': 'Blogger has no frontal image'}), 400
    
    try:
        data = request.get_json() or {}
        expression_scale = data.get('expression_scale', 1.0)
        face_enhance = data.get('face_enhance', True)
        
        # Generate prompt using GPT based on video scenario
        print(f">>> Generating video prompt from scenario...")
        video_prompt = None
        audio_duration = None
        
        if project.scenario_text:
            try:
                # Ask GPT to create a short prompt describing how the person should move and express
                prompt_request = f"""Based on this video scenario:
{project.scenario_text}

Create a SHORT prompt (max 100 characters) describing how the person should look and move on camera. Focus on:
- Camera position (e.g., "looking at camera", "slightly turned")
- Expression/emotion (e.g., "enthusiastic", "serious", "friendly")
- Natural movements (e.g., "natural gestures", "expressive hands")

Example: "Professional influencer speaking to camera with enthusiasm and natural hand gestures"

Prompt:"""
                
                video_prompt = gpt_helper.ask_gpt(prompt_request, max_tokens=50)
                print(f">>> Generated prompt: {video_prompt}")
            except Exception as e:
                print(f">>> Warning: Could not generate prompt via GPT: {e}")
                video_prompt = "A professional influencer speaking to camera with natural expressions and gestures"
        else:
            video_prompt = "A professional influencer speaking to camera with natural expressions and gestures"
        
        # Calculate audio duration from audio file (for num_frames calculation)
        if project.audio_url:
            try:
                import requests
                from mutagen.mp3 import MP3
                from io import BytesIO
                from app.utils.s3_helper import s3_helper
                
                print(f">>> Downloading audio to get duration...")
                # Generate fresh presigned URL for audio download
                fresh_audio_url_for_download = s3_helper.get_presigned_url(project.audio_url, expiration=300)
                audio_response = requests.get(fresh_audio_url_for_download, timeout=10)
                audio_bytes = BytesIO(audio_response.content)
                audio = MP3(audio_bytes)
                audio_duration = audio.info.length
                print(f">>> Audio duration: {audio_duration:.2f}s")
            except Exception as e:
                print(f">>> Warning: Could not get audio duration: {e}")
                audio_duration = None
        
        print(f">>> Calling falai_helper.start_avatar_generation...")
        current_app.logger.info(f"Calling falai_helper.start_avatar_generation...")
        
        # Generate fresh presigned URLs for fal.ai (old ones may have expired)
        from app.utils.s3_helper import s3_helper
        fresh_audio_url = s3_helper.get_presigned_url(project.audio_url, expiration=3600)
        fresh_image_url = s3_helper.get_presigned_url(project.blogger.frontal_image_url, expiration=3600)
        
        print(f">>> Fresh audio URL: {fresh_audio_url[:100]}...")
        print(f">>> Fresh image URL: {fresh_image_url[:100]}...")
        
        # Start async generation (returns immediately with request_id)
        try:
            result = falai_helper.start_avatar_generation(
                audio_url=fresh_audio_url,
                image_url=fresh_image_url,
                prompt=video_prompt,
                audio_duration=audio_duration,
                expression_scale=expression_scale,
                face_enhance=face_enhance
            )
        except RuntimeError as re:
            # fal.ai responded with an error - log and return readable message
            current_app.logger.error(f"Error in fal.ai start_avatar_generation: {str(re)}")
            return jsonify({'error': 'fal.ai error', 'detail': str(re)}), 502
        
        print(f">>> fal.ai returned: {result}")
        current_app.logger.info(f"fal.ai returned: {result}")
        
        # Save request_id for status polling
        project.avatar_generation_params = {
            'expression_scale': expression_scale,
            'face_enhance': face_enhance,
            'fal_request_id': result['request_id'],
            'status': 'processing'
        }
        db.session.commit()
        
        print(f">>> Saved request_id to DB: {result['request_id']}")
        current_app.logger.info(f"Saved request_id to DB: {result['request_id']}")
        
        return jsonify({
            'request_id': result['request_id'],
            'status': 'processing',
            'message': 'Avatar video generation started. Use check-avatar-status to poll for completion.',
            'project': project.to_dict()
        })
    except Exception as e:
        print(f"!!! ERROR in generate_avatar_video: {str(e)}")
        print(f"!!! Error type: {type(e).__name__}")
        current_app.logger.error(f"Error in generate_avatar_video: {str(e)}")
        current_app.logger.error(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        current_app.logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@bp.route('/projects/<project_id>/check-avatar-status/<request_id>', methods=['GET'])
def check_avatar_status(project_id, request_id):
    """Check the status of avatar video generation"""
    print(f"=== CHECK AVATAR STATUS CALLED ===")
    print(f"Request ID: {request_id}")
    current_app.logger.info(f"=== CHECK AVATAR STATUS CALLED ===")
    current_app.logger.info(f"Request ID: {request_id}")
    
    try:
        status = falai_helper.check_status(request_id)
        print(f"Status result: {status}")
        current_app.logger.info(f"Status result: {status}")
        
        # If completed, save video URL
        if status.get('status') == 'completed':
            project = Project.query.get_or_404(project_id)
            project.avatar_video_url = status['video_url']
            
            # Update status in avatar_generation_params
            if project.avatar_generation_params:
                params = project.avatar_generation_params.copy()
                params['status'] = 'completed'
                params['video_url'] = status['video_url']
                project.avatar_generation_params = params
            
            project.current_step = 5  # Ready for final composition
            db.session.commit()
            
            print(f"Video completed! URL: {status['video_url']}")
            current_app.logger.info(f"Video completed! URL: {status['video_url']}")
        
        return jsonify(status)
    
    except Exception as e:
        print(f"!!! ERROR in check_avatar_status: {str(e)}")
        current_app.logger.error(f"check_avatar_status error: {str(e)}")
        return jsonify({'status': 'error', 'error': str(e)}), 500


@bp.route('/projects/<project_id>/compose-final-video', methods=['POST'])
def compose_final_video(project_id):
    """Compose final video with FFmpeg"""
    current_app.logger.info(f"=== Starting compose_final_video for project {project_id} ===")
    
    project = Project.query.get_or_404(project_id)
    current_app.logger.info(f"Project loaded, status: {project.status}, step: {project.current_step}")
    
    if not project.avatar_video_url:
        return jsonify({'error': 'Avatar video must be generated first'}), 400
    
    if not project.audio_url:
        return jsonify({'error': 'Audio is required'}), 400
    
    try:
        data = request.get_json() or {}
        add_subtitles = data.get('add_subtitles', False)
        advanced_composition = data.get('advanced_composition', False)
        
        current_app.logger.info(f"Options: add_subtitles={add_subtitles}, advanced_composition={advanced_composition}")
        current_app.logger.info(f"Timeline segments: {len(project.timeline) if project.timeline else 0}")
        current_app.logger.info(f"Materials count: {len(project.materials) if project.materials else 0}")
        
        output_filename = f"final_{project_id}.mp4"
        
        # Create composition
        if advanced_composition and project.timeline:
            current_app.logger.info("Using advanced composition with timeline")
            video_path = ffmpeg_helper.create_advanced_composition(
                avatar_video_url=project.avatar_video_url,
                audio_url=project.audio_url,
                timeline=project.timeline,
                materials=project.materials or [],
                output_filename=output_filename
            )
        else:
            current_app.logger.info("Using simple composition (no timeline overlays)")
            video_path = ffmpeg_helper.create_video_composition(
                avatar_video_url=project.avatar_video_url,
                audio_url=project.audio_url,
                timeline=project.timeline or [],
                materials=project.materials or [],
                output_filename=output_filename
            )
        
        current_app.logger.info(f"Video composition completed: {video_path}")
        
        # Add subtitles if requested
        if add_subtitles and project.voiceover_text and project.audio_alignment:
            current_app.logger.info("Adding subtitles to video")
            video_path = ffmpeg_helper.add_subtitles(
                video_path=video_path,
                voiceover_text=project.voiceover_text,
                audio_alignment=project.audio_alignment,
                output_filename=f"final_subs_{project_id}.mp4"
            )
        
        # Upload to S3
        current_app.logger.info("Uploading final video to S3")
        with open(video_path, 'rb') as f:
            final_video_url = s3_helper.upload_file(f, 'final_videos')
        
        current_app.logger.info(f"Final video uploaded: {final_video_url}")
        
        project.final_video_url = final_video_url
        project.status = 'completed'
        project.current_step = 6
        db.session.commit()
        
        current_app.logger.info("=== compose_final_video completed successfully ===")
        
        return jsonify({
            'final_video_url': final_video_url,
            'project': project.to_dict()
        })
    except Exception as e:
        current_app.logger.error(f"=== compose_final_video ERROR: {str(e)} ===")
        current_app.logger.exception("Full traceback:")
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
