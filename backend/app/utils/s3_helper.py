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
    
    def upload_file(self, file, folder='uploads'):
        """
        Upload file to S3 and return public URL.
        
        Args:
            file: FileStorage object from Flask
            folder: S3 folder path (default: 'uploads')
            
        Returns:
            str: Public URL of uploaded file
        """
        if not file:
            return None
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        s3_key = f"{folder}/{unique_filename}"
        
        # Upload to S3
        bucket = current_app.config['AWS_S3_BUCKET']
        client = self._get_client()
        
        try:
            client.upload_fileobj(
                file,
                bucket,
                s3_key,
                ExtraArgs={
                    'ContentType': file.content_type,
                    'ACL': 'public-read'  # Make file publicly accessible
                }
            )
            
            # Generate public URL
            region = current_app.config['AWS_REGION']
            url = f"https://{bucket}.s3.{region}.amazonaws.com/{s3_key}"
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


# Global instance
s3_helper = S3Helper()
