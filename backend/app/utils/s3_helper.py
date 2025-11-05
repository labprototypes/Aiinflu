"""AWS S3 upload helper."""
import boto3
import uuid
from werkzeug.utils import secure_filename
from flask import current_app


class S3Helper:
    """Helper class for S3 uploads."""
    
    def __init__(self):
        """Initialize S3 client."""
        self.s3_client = None
    
    def _get_client(self):
        """Get or create S3 client."""
        if not self.s3_client:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'],
                aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY'],
                region_name=current_app.config['AWS_REGION']
            )
        return self.s3_client
    
    def upload_file(self, file, folder='uploads', filename=None, content_type=None):
        """
        Upload file to S3 and return public URL.
        
        Args:
            file: FileStorage object from Flask or BytesIO object
            folder: S3 folder path (default: 'uploads')
            filename: Optional filename (required for BytesIO objects)
            content_type: Optional content type (e.g., 'audio/mpeg', 'image/jpeg')
            
        Returns:
            str: Public URL of uploaded file
        """
        if not file:
            return None
        
        # Check if AWS is configured
        bucket = current_app.config.get('AWS_S3_BUCKET')
        if not bucket:
            raise ValueError("AWS_S3_BUCKET is not configured. Please set AWS environment variables in Render Dashboard.")
        
        # Generate unique filename
        # Handle both FileStorage (has .filename) and BytesIO (needs filename param)
        if hasattr(file, 'filename'):
            base_filename = secure_filename(file.filename)
        elif filename:
            base_filename = secure_filename(filename)
        else:
            # Generate a default filename with timestamp
            base_filename = f"file_{uuid.uuid4().hex[:8]}"
        
        unique_filename = f"{uuid.uuid4()}_{base_filename}"
        s3_key = f"{folder}/{unique_filename}"
        
        # Determine content type
        if hasattr(file, 'content_type'):
            content_type = file.content_type
        elif not content_type:
            content_type = 'application/octet-stream'
        
        # Upload to S3
        client = self._get_client()
        
        try:
            # Upload with public-read ACL for fal.ai access
            # Note: Bucket must have ACLs enabled in S3 settings
            try:
                client.upload_fileobj(
                    file,
                    bucket,
                    s3_key,
                    ExtraArgs={
                        'ContentType': content_type,
                        'ACL': 'public-read'  # Make publicly accessible
                    }
                )
                
                # Return direct public URL (no expiration)
                region = current_app.config.get('AWS_REGION', 'us-east-1')
                url = f"https://{bucket}.s3.{region}.amazonaws.com/{s3_key}"
                
            except Exception as acl_error:
                # Fallback: upload without ACL if ACLs are disabled
                current_app.logger.warning(f"ACL upload failed, using presigned URL: {acl_error}")
                
                client.upload_fileobj(
                    file,
                    bucket,
                    s3_key,
                    ExtraArgs={
                        'ContentType': content_type
                    }
                )
                
                # Generate pre-signed URL (valid for 7 days)
                url = client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': bucket,
                        'Key': s3_key
                    },
                    ExpiresIn=604800  # 7 days in seconds
                )
            
            return url
            
        except Exception as e:
            current_app.logger.error(f"S3 upload failed: {str(e)}")
            raise
    
    def delete_file(self, file_url):
        """
        Delete file from S3 by URL.
        
        Args:
            file_url: Full S3 URL of the file
        """
        if not file_url:
            return
        
        try:
            # Extract S3 key from URL
            bucket = current_app.config['AWS_S3_BUCKET']
            region = current_app.config['AWS_REGION']
            prefix = f"https://{bucket}.s3.{region}.amazonaws.com/"
            
            if not file_url.startswith(prefix):
                return
            
            s3_key = file_url.replace(prefix, '')
            
            # Delete from S3
            client = self._get_client()
            client.delete_object(Bucket=bucket, Key=s3_key)
            
        except Exception as e:
            current_app.logger.error(f"S3 delete failed: {str(e)}")
    
    def get_presigned_url(self, s3_url, expiration=3600):
        """
        Generate presigned URL for private S3 objects.
        
        Args:
            s3_url: Full S3 URL (public or direct)
            expiration: URL validity in seconds (default: 1 hour)
            
        Returns:
            str: Presigned URL that works regardless of bucket ACL settings
        """
        if not s3_url:
            return None
        
        try:
            bucket = current_app.config['AWS_S3_BUCKET']
            region = current_app.config['AWS_REGION']
            
            # Extract S3 key from URL
            # Handle both formats: https://bucket.s3.region.amazonaws.com/key and presigned URLs
            if '?' in s3_url:
                # Already a presigned URL, return as-is
                return s3_url
            
            prefix = f"https://{bucket}.s3.{region}.amazonaws.com/"
            if not s3_url.startswith(prefix):
                # Not our S3 URL, return as-is
                return s3_url
            
            s3_key = s3_url.replace(prefix, '')
            
            # Generate presigned URL
            client = self._get_client()
            presigned_url = client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': bucket,
                    'Key': s3_key
                },
                ExpiresIn=expiration
            )
            
            return presigned_url
            
        except Exception as e:
            current_app.logger.error(f"Failed to generate presigned URL: {str(e)}")
            return s3_url  # Return original URL as fallback


# Global instance
s3_helper = S3Helper()
