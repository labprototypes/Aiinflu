"""Project API endpoints."""
from flask import request, jsonify, current_app
from app import db
from app.models import Project, Blogger
from app.utils.gpt_helper import gpt_helper
from app.utils.elevenlabs_helper import elevenlabs_helper
from app.utils.s3_helper import s3_helper
from app.utils.heygen_helper import heygen_helper
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
    if 'location_id' in data:
        project.location_id = data['location_id']
        current_app.logger.info(f"Updated location_id: {data['location_id']}")
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
        # Extract text using GPT (with audio tags for Eleven v3)
        current_app.logger.info("Calling GPT-4 for text extraction with audio tags")
        voiceover_text = gpt_helper.extract_voiceover_text(project.scenario_text)
        
        # Log result for verification
        current_app.logger.info(f"Text extracted with audio tags (length: {len(voiceover_text)} chars)")
        current_app.logger.debug(f"Voiceover preview: {voiceover_text[:200]}...")
        
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


@bp.route('/projects/<project_id>/generate-hook', methods=['POST'])
def generate_hook(project_id):
    """Generate catchy hook for video intro"""
    project = Project.query.get_or_404(project_id)
    
    if not project.scenario_text:
        return jsonify({'error': 'No scenario text available'}), 400
    
    try:
        hook = gpt_helper.generate_hook(project.scenario_text)
        
        current_app.logger.info(f"Generated hook: {hook}")
        
        return jsonify({
            'hook': hook
        })
    
    except Exception as e:
        current_app.logger.error(f"Hook generation failed: {str(e)}")
        return jsonify({'error': str(e)}), 500


@bp.route('/projects/<project_id>/extract-and-analyze', methods=['POST'])
def extract_and_analyze(project_id):
    """Extract voiceover text AND analyze materials in parallel"""
    project = Project.query.get_or_404(project_id)
    
    if not project.scenario_text:
        return jsonify({'error': 'No scenario text available'}), 400
    
    try:
        # Extract voiceover text
        voiceover_text = gpt_helper.extract_voiceover_text(project.scenario_text)
        current_app.logger.info(f"Extracted voiceover text: {len(voiceover_text)} chars")
        current_app.logger.info(f"Preview: {voiceover_text[:200]}...")
        
        project.voiceover_text = voiceover_text
        project.current_step = max(project.current_step, 2)
        
        # Analyze materials if available
        analysis_results = []
        if project.materials and len(project.materials) > 0:
            current_app.logger.info(f"Analyzing {len(project.materials)} materials")
            
            image_urls = [mat.get('url') for mat in project.materials if mat.get('url')]
            
            if image_urls:
                analysis_results = gpt_helper.analyze_images(image_urls)
                
                # Update materials with analysis results
                for i, material in enumerate(project.materials):
                    if i < len(analysis_results):
                        material['analysis'] = analysis_results[i].get('analysis')
                
                project.materials = project.materials.copy()  # Trigger SQLAlchemy update
                current_app.logger.info(f"Analysis complete for {len(analysis_results)} materials")
        
        db.session.commit()
        
        return jsonify({
            'voiceover_text': voiceover_text,
            'analysis_results': analysis_results,
            'project': project.to_dict()
        })
    
    except Exception as e:
        current_app.logger.error(f"Extract and analyze failed: {str(e)}")
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
        
        current_app.logger.info(f"ElevenLabs result keys: {list(result.keys())}")
        current_app.logger.info(f"Audio duration: {result.get('audio_duration')}")
        if result.get('alignment'):
            current_app.logger.info(f"Alignment keys: {list(result['alignment'].keys())}")
            current_app.logger.info(f"Alignment characters count: {len(result['alignment'].get('characters', []))}")
        
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


@bp.route('/projects/<project_id>/auto-build', methods=['POST'])
def auto_build(project_id):
    """
    Auto-build: Full automation pipeline
    1. Extract voiceover + analyze materials
    2. Generate audio
    3. Generate timeline
    4. Generate avatar video
    5. Compose final video with subtitles
    
    Returns project and updates step to 6 when complete
    """
    project = Project.query.get_or_404(project_id)
    
    if not project.scenario_text:
        return jsonify({'error': 'No scenario text available'}), 400
    
    if not project.materials or len(project.materials) == 0:
        return jsonify({'error': 'No materials uploaded'}), 400
    
    try:
        current_app.logger.info(f"=== AUTO-BUILD START for project {project_id} ===")
        
        # Step 1: Extract voiceover text
        current_app.logger.info("Step 1/5: Extracting voiceover text...")
        voiceover_text = gpt_helper.extract_voiceover_text(project.scenario_text)
        project.voiceover_text = voiceover_text
        current_app.logger.info(f"Voiceover extracted: {len(voiceover_text)} chars")
        
        # Step 2: Analyze materials
        current_app.logger.info("Step 2/5: Analyzing materials...")
        image_urls = [mat.get('url') for mat in project.materials if mat.get('url')]
        analysis_results = gpt_helper.analyze_images(image_urls)
        for i, material in enumerate(project.materials):
            if i < len(analysis_results):
                material['analysis'] = analysis_results[i].get('analysis')
        project.materials = project.materials.copy()
        current_app.logger.info(f"Analysis complete for {len(analysis_results)} materials")
        
        # Step 3: Generate audio
        current_app.logger.info("Step 3/5: Generating audio...")
        audio_result = elevenlabs_helper.generate_speech_with_timestamps(
            text=project.voiceover_text,
            voice_id=project.blogger.elevenlabs_voice_id
        )
        project.audio_url = audio_result['audio_url']
        project.audio_alignment = {
            'alignment': audio_result.get('alignment'),
            'audio_duration': audio_result.get('audio_duration')
        }
        current_app.logger.info(f"Audio generated: {audio_result.get('audio_duration')}s")
        
        # Step 4: Generate timeline
        current_app.logger.info("Step 4/5: Generating timeline...")
        timeline = gpt_helper.generate_timeline(
            voiceover_text=project.voiceover_text,
            audio_alignment=project.audio_alignment,
            materials=project.materials
        )
        project.timeline = timeline
        current_app.logger.info(f"Timeline generated: {len(timeline)} segments")
        
        # Step 5: Generate avatar video
        current_app.logger.info("Step 5/5: Generating avatar video...")
        from app.utils.heygen_helper import HeyGenHelper
        from app.utils.s3_helper import s3_helper
        
        fresh_audio_url = s3_helper.get_presigned_url(project.audio_url, expiration=3600)
        fresh_image_url = s3_helper.get_presigned_url(project.blogger.frontal_image_url, expiration=3600)
        
        # Use location image if selected
        if project.location_id is not None and project.blogger.settings:
            locations = project.blogger.settings.get('locations', [])
            if project.location_id < len(locations):
                location = locations[project.location_id]
                location_image_s3 = location.get('image_url')
                if location_image_s3:
                    fresh_image_url = s3_helper.get_presigned_url(location_image_s3, expiration=3600)
        
        image_key = HeyGenHelper.upload_asset(fresh_image_url)
        audio_key = HeyGenHelper.upload_asset(fresh_audio_url)
        
        response = HeyGenHelper.create_infinitalk_video(
            image_key=image_key,
            audio_key=audio_key,
            expression_scale=1.0,
            face_enhance=True
        )
        
        video_id = response.get('data', {}).get('video_id')
        project.avatar_generation_params = {
            'video_id': video_id,
            'status': 'processing',
            'expression_scale': 1.0
        }
        
        current_app.logger.info(f"Avatar video generation started: {video_id}")
        
        # Update project to step 5 (will poll for completion)
        project.current_step = 5
        db.session.commit()
        
        current_app.logger.info("=== AUTO-BUILD INITIATED ===")
        current_app.logger.info("Avatar video is processing. User should poll for completion.")
        
        return jsonify({
            'message': 'Auto-build pipeline initiated',
            'video_id': video_id,
            'project': project.to_dict()
        })
        
    except Exception as e:
        current_app.logger.error(f"Auto-build failed: {str(e)}")
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
        current_app.logger.info(f"Generating timeline for project {project_id}")
        current_app.logger.info(f"Audio alignment type: {type(project.audio_alignment)}")
        current_app.logger.info(f"Audio alignment keys: {list(project.audio_alignment.keys()) if project.audio_alignment else 'None'}")
        current_app.logger.info(f"Audio duration: {project.audio_alignment.get('audio_duration')} seconds")
        
        alignment = project.audio_alignment.get('alignment')
        if alignment:
            current_app.logger.info(f"Alignment data keys: {list(alignment.keys())}")
            current_app.logger.info(f"Has character_start_times_seconds: {'character_start_times_seconds' in alignment}")
        else:
            current_app.logger.warning("No alignment data in project.audio_alignment!")
        
        current_app.logger.info(f"Materials count: {len(project.materials)}")
        
        timeline = gpt_helper.generate_timeline(
            voiceover_text=project.voiceover_text,
            audio_alignment=project.audio_alignment,
            materials=project.materials
        )
        
        current_app.logger.info(f"Generated {len(timeline)} timeline segments")
        if timeline:
            current_app.logger.info(f"First segment: {timeline[0]}")
            current_app.logger.info(f"Last segment: {timeline[-1]}")
        
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
    """Generate talking avatar video using HeyGen Avatar IV (image-to-video)"""
    from flask import current_app
    project = Project.query.get_or_404(project_id)
    
    current_app.logger.info(f"=== GENERATE AVATAR IV VIDEO ===")
    current_app.logger.info(f"Project ID: {project_id}")
    
    if not project.audio_url:
        return jsonify({'error': 'Audio must be generated first'}), 400
    
    if not project.blogger.frontal_image_url:
        return jsonify({'error': 'Blogger has no frontal image'}), 400
    
    try:
        from app.utils.heygen_helper import HeyGenHelper
        from app.utils.s3_helper import s3_helper
        
        # Generate fresh presigned URLs (HeyGen will download from them)
        fresh_audio_url = s3_helper.get_presigned_url(project.audio_url, expiration=3600)
        fresh_image_url = s3_helper.get_presigned_url(project.blogger.frontal_image_url, expiration=3600)
        
        # Determine which image to use based on location selection
        image_url_for_upload = fresh_image_url  # Default to frontal image
        selected_location_name = "Frontal image"
        
        if project.location_id is not None and project.blogger.settings:
            locations = project.blogger.settings.get('locations', [])
            if project.location_id < len(locations):
                location = locations[project.location_id]
                location_image_s3 = location.get('image_url')
                if location_image_s3:
                    image_url_for_upload = s3_helper.get_presigned_url(location_image_s3, expiration=3600)
                    selected_location_name = location.get('name', f'Location {project.location_id + 1}')
                    current_app.logger.info(f"Using location: {selected_location_name}")
        
        current_app.logger.info(f"Image URL: {image_url_for_upload[:100]}...")
        current_app.logger.info(f"Audio URL: {fresh_audio_url[:100]}...")
        
        # Step 1: Upload image asset (9:16 portrait format)
        current_app.logger.info("Step 1: Uploading image asset...")
        image_key = HeyGenHelper.upload_asset(image_url_for_upload)
        current_app.logger.info(f"Image asset uploaded: {image_key}")
        
        # Step 2: Upload audio asset
        current_app.logger.info("Step 2: Uploading audio asset...")
        audio_url = HeyGenHelper.upload_audio_asset(fresh_audio_url)
        current_app.logger.info(f"Audio asset uploaded: {audio_url}")
        
        # Step 3: Generate Avatar IV video
        video_title = f"{project.blogger.name} - {selected_location_name}"
        current_app.logger.info(f"Step 3: Generating Avatar IV video: {video_title}")
        
        video_id = HeyGenHelper.generate_avatar_iv_video(
            image_key=image_key,
            audio_url=audio_url,
            video_title=video_title
        )
        
        current_app.logger.info(f"Avatar IV video generation started: {video_id}")
        
        # Save generation parameters
        project.avatar_generation_params = {
            'video_id': video_id,
            'image_key': image_key,
            'audio_url': audio_url,
            'video_title': video_title,
            'location': selected_location_name,
            'mode': 'avatar_iv'
        }
        db.session.commit()
        
        return jsonify({
            'request_id': video_id,  # Frontend expects request_id
            'video_id': video_id,
            'status': 'processing',
            'message': 'Avatar IV video generation started'
        }), 202
        
    except Exception as e:
        import traceback
        current_app.logger.error(f"Avatar IV generation error: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500




@bp.route('/projects/<project_id>/check-avatar-status/<request_id>', methods=['GET'])
def check_avatar_status(project_id, request_id):
    """Check the status of Avatar IV video generation"""
    from flask import current_app
    current_app.logger.info(f"=== CHECK AVATAR IV STATUS ===")
    current_app.logger.info(f"Video ID: {request_id}")
    
    try:
        from app.utils.heygen_helper import HeyGenHelper
        
        status = HeyGenHelper.get_video_status(request_id)
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
            
            current_app.logger.info(f"Avatar IV video completed! URL: {status['video_url']}")
        
        return jsonify(status)
    
    except Exception as e:
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
        
        # Try to commit with retry on connection errors
        max_retries = 3
        for attempt in range(max_retries):
            try:
                db.session.commit()
                current_app.logger.info("Database updated successfully")
                break
            except Exception as db_err:
                current_app.logger.warning(f"DB commit attempt {attempt + 1}/{max_retries} failed: {str(db_err)}")
                db.session.rollback()
                if attempt < max_retries - 1:
                    import time
                    time.sleep(1)  # Wait 1 second before retry
                    # Refresh the project object
                    db.session.refresh(project)
                    project.final_video_url = final_video_url
                    project.status = 'completed'
                    project.current_step = 6
                else:
                    # Last attempt failed, but video is already uploaded
                    current_app.logger.error(f"Failed to save to DB after {max_retries} attempts, but video is uploaded: {final_video_url}")
                    # Return success anyway since video is ready
        
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
