"""Blogger locations management API."""
from flask import request, jsonify
from sqlalchemy.orm.attributes import flag_modified
from app.api import bp
from app import db
from app.models import Blogger
from app.utils.s3_helper import s3_helper


@bp.route('/bloggers/<blogger_id>/locations', methods=['POST'])
def add_location(blogger_id):
    """Add new location image to blogger."""
    blogger = Blogger.query.get_or_404(blogger_id)
    
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    
    file = request.files['image']
    name = request.form.get('name', f'Location {len(blogger.settings.get("locations", [])) + 1}')
    heygen_avatar_id = request.form.get('heygen_avatar_id', '00000')
    
    # Upload image to S3
    image_url = s3_helper.upload_file(file, folder='bloggers/locations')
    
    # Add to locations array
    if not blogger.settings:
        blogger.settings = {"heygen_avatar_id": "00000", "locations": []}
    
    if 'locations' not in blogger.settings:
        blogger.settings['locations'] = []
    
    locations = blogger.settings.get('locations', [])
    locations.append({
        'image_url': image_url,
        'name': name,
        'heygen_avatar_id': heygen_avatar_id
    })
    
    blogger.settings['locations'] = locations
    flag_modified(blogger, 'settings')  # Tell SQLAlchemy that JSON field changed
    db.session.commit()
    
    return jsonify(blogger.to_dict()), 201


@bp.route('/bloggers/<blogger_id>/locations/<int:location_id>', methods=['PUT'])
def update_location(blogger_id, location_id):
    """Update location name or heygen_avatar_id."""
    blogger = Blogger.query.get_or_404(blogger_id)
    
    if not blogger.settings or 'locations' not in blogger.settings:
        return jsonify({'error': 'No locations found'}), 404
    
    locations = blogger.settings.get('locations', [])
    
    if location_id >= len(locations):
        return jsonify({'error': 'Location not found'}), 404
    
    # Update fields
    data = request.get_json() or {}
    if 'name' in data:
        locations[location_id]['name'] = data['name']
    if 'heygen_avatar_id' in data:
        locations[location_id]['heygen_avatar_id'] = data['heygen_avatar_id']
    
    blogger.settings['locations'] = locations
    flag_modified(blogger, 'settings')  # Tell SQLAlchemy that JSON field changed
    db.session.commit()
    
    return jsonify(blogger.to_dict())


@bp.route('/bloggers/<blogger_id>/locations/<int:location_id>', methods=['DELETE'])
def delete_location(blogger_id, location_id):
    """Delete location from blogger."""
    blogger = Blogger.query.get_or_404(blogger_id)
    
    if not blogger.settings or 'locations' not in blogger.settings:
        return jsonify({'error': 'No locations found'}), 404
    
    locations = blogger.settings.get('locations', [])
    
    if location_id >= len(locations):
        return jsonify({'error': 'Location not found'}), 404
    
    # Delete image from S3
    location = locations[location_id]
    if location.get('image_url'):
        s3_helper.delete_file(location['image_url'])
    
    # Remove from array
    locations.pop(location_id)
    blogger.settings['locations'] = locations
    flag_modified(blogger, 'settings')  # Tell SQLAlchemy that JSON field changed
    db.session.commit()
    
    return jsonify(blogger.to_dict())
