# Заменить функцию generate_avatar_video в backend/app/api/projects.py (строки 309-665)
# на этот упрощённый вариант с Avatar IV:

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
        audio_asset_id = HeyGenHelper.upload_audio_asset(fresh_audio_url)
        current_app.logger.info(f"Audio asset uploaded: {audio_asset_id}")
        
        # Step 3: Generate Avatar IV video
        video_title = f"{project.blogger.name} - {selected_location_name}"
        current_app.logger.info(f"Step 3: Generating Avatar IV video: {video_title}")
        
        video_id = HeyGenHelper.generate_avatar_iv_video(
            image_key=image_key,
            audio_asset_id=audio_asset_id,
            video_title=video_title
        )
        
        current_app.logger.info(f"Avatar IV video generation started: {video_id}")
        
        # Save generation parameters
        project.avatar_generation_params = {
            'video_id': video_id,
            'image_key': image_key,
            'audio_asset_id': audio_asset_id,
            'video_title': video_title,
            'location': selected_location_name,
            'mode': 'avatar_iv'
        }
        db.session.commit()
        
        return jsonify({
            'video_id': video_id,
            'status': 'processing',
            'message': 'Avatar IV video generation started'
        }), 202
        
    except Exception as e:
        import traceback
        current_app.logger.error(f"Avatar IV generation error: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500
