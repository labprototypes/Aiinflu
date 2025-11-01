"""Blogger API endpoints."""
from flask import request, jsonify
from app.api import bp
from app import db
from app.models import Blogger
from app.utils.s3_helper import s3_helper


@bp.route('/bloggers', methods=['GET'])
def get_bloggers():
    """Get all bloggers."""
    bloggers = Blogger.query.order_by(Blogger.created_at.desc()).all()
    return jsonify([blogger.to_dict() for blogger in bloggers])


@bp.route('/bloggers/<blogger_id>', methods=['GET'])
def get_blogger(blogger_id):
    """Get single blogger by ID."""
    blogger = Blogger.query.get_or_404(blogger_id)
    return jsonify(blogger.to_dict())


@bp.route('/bloggers', methods=['POST'])
def create_blogger():
    """Create new blogger."""
    data = request.form
    
    # Create blogger
    blogger = Blogger(
        name=data.get('name'),
        type=data.get('type', 'podcaster'),
        tone_of_voice=data.get('tone_of_voice'),
        elevenlabs_voice_id=data.get('elevenlabs_voice_id')
    )
    
    # Handle file uploads
    if 'frontal_image' in request.files:
        file = request.files['frontal_image']
        blogger.frontal_image_url = s3_helper.upload_file(file, folder='bloggers/frontal')
    
    if 'location_image' in request.files:
        file = request.files['location_image']
        blogger.location_image_url = s3_helper.upload_file(file, folder='bloggers/location')
    
    db.session.add(blogger)
    db.session.commit()
    
    return jsonify(blogger.to_dict()), 201


@bp.route('/bloggers/<blogger_id>', methods=['PUT'])
def update_blogger(blogger_id):
    """Update existing blogger."""
    blogger = Blogger.query.get_or_404(blogger_id)
    data = request.form
    
    # Update fields
    if 'name' in data:
        blogger.name = data['name']
    if 'type' in data:
        blogger.type = data['type']
    if 'tone_of_voice' in data:
        blogger.tone_of_voice = data['tone_of_voice']
    if 'elevenlabs_voice_id' in data:
        blogger.elevenlabs_voice_id = data['elevenlabs_voice_id']
    if 'is_active' in data:
        blogger.is_active = data['is_active'].lower() == 'true'
    
    # Handle file uploads
    if 'frontal_image' in request.files:
        file = request.files['frontal_image']
        # Delete old image if exists
        if blogger.frontal_image_url:
            s3_helper.delete_file(blogger.frontal_image_url)
        blogger.frontal_image_url = s3_helper.upload_file(file, folder='bloggers/frontal')
    
    if 'location_image' in request.files:
        file = request.files['location_image']
        if blogger.location_image_url:
            s3_helper.delete_file(blogger.location_image_url)
        blogger.location_image_url = s3_helper.upload_file(file, folder='bloggers/location')
    
    db.session.commit()
    
    return jsonify(blogger.to_dict())


@bp.route('/bloggers/<blogger_id>', methods=['DELETE'])
def delete_blogger(blogger_id):
    """Delete blogger."""
    blogger = Blogger.query.get_or_404(blogger_id)
    
    # Delete S3 files
    if blogger.frontal_image_url:
        s3_helper.delete_file(blogger.frontal_image_url)
    if blogger.location_image_url:
        s3_helper.delete_file(blogger.location_image_url)
    
    db.session.delete(blogger)
    db.session.commit()
    
    return '', 204
