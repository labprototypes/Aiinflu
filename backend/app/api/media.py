"""Media proxy endpoints for serving S3 files."""
from flask import current_app, send_file, abort
from app.api import bp
from app.utils.s3_helper import s3_helper
import requests
from io import BytesIO


@bp.route('/media/proxy', methods=['GET'])
def proxy_media():
    """
    Proxy S3 media files through backend.
    Usage: /api/media/proxy?url=<s3_url>
    
    This allows serving private S3 objects without exposing presigned URLs.
    """
    from flask import request
    
    s3_url = request.args.get('url')
    if not s3_url:
        abort(400, 'Missing url parameter')
    
    # Validate it's our S3 bucket
    bucket = current_app.config['AWS_S3_BUCKET']
    if bucket not in s3_url:
        abort(403, 'Invalid S3 URL')
    
    try:
        # Generate presigned URL (server-side only)
        presigned_url = s3_helper.get_presigned_url(s3_url, expiration=300)  # 5 min
        
        # Download file from S3
        response = requests.get(presigned_url, timeout=10)
        response.raise_for_status()
        
        # Determine content type
        content_type = response.headers.get('Content-Type', 'application/octet-stream')
        
        # Return file
        return send_file(
            BytesIO(response.content),
            mimetype=content_type,
            as_attachment=False,
            download_name='media'
        )
        
    except Exception as e:
        current_app.logger.error(f"Media proxy error: {str(e)}")
        abort(500, 'Failed to load media')
