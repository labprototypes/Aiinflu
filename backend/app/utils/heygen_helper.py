import requests
from flask import current_app
from typing import Optional, Dict
import time


class HeyGenHelper:
    """Helper for HeyGen talking photo video generation"""
    
    BASE_URL = "https://api.heygen.com"
    
    def __init__(self):
        self.api_key = None
    
    def _get_headers(self):
        """Get authentication headers"""
        if not self.api_key:
            self.api_key = current_app.config.get('HEYGEN_API_KEY')
        if not self.api_key:
            raise ValueError("HEYGEN_API_KEY not configured")
        
        return {
            'X-Api-Key': self.api_key,
            'Content-Type': 'application/json'
        }
    
    @staticmethod
    def upload_talking_photo(image_url: str) -> str:
        """
        Upload a photo to HeyGen and get talking_photo_id
        
        Args:
            image_url: URL to the image file
            
        Returns:
            talking_photo_id for use in video generation
        """
        api_key = current_app.config.get('HEYGEN_API_KEY')
        if not api_key:
            raise ValueError("HEYGEN_API_KEY not configured")
        
        try:
            current_app.logger.info(f"Uploading talking photo to HeyGen: {image_url}")
            
            headers = {
                'X-Api-Key': api_key
            }
            
            # Download image from URL
            img_response = requests.get(image_url, timeout=30)
            img_response.raise_for_status()
            
            # Upload photo via multipart/form-data
            files = {
                'file': ('avatar.png', img_response.content, 'image/png')
            }
            
            response = requests.post(
                f"{HeyGenHelper.BASE_URL}/v1/talking_photo.upload",
                headers=headers,
                files=files,
                timeout=60
            )
            
            response.raise_for_status()
            result = response.json()
            
            current_app.logger.info(f"HeyGen upload response: {result}")
            
            if result.get('error'):
                error_msg = result.get('error', {}).get('message', 'Unknown error')
                raise RuntimeError(f"HeyGen upload error: {error_msg}")
            
            talking_photo_id = result.get('data', {}).get('talking_photo_id')
            
            if not talking_photo_id:
                raise ValueError("No talking_photo_id in HeyGen response")
            
            current_app.logger.info(f"Photo uploaded successfully: {talking_photo_id}")
            return talking_photo_id
            
        except Exception as e:
            current_app.logger.error(f"Failed to upload photo: {str(e)}")
            raise RuntimeError(f"Photo upload failed: {str(e)}")
    
    @staticmethod
    def start_avatar_generation(
        audio_url: str,
        image_url: str,
        avatar_id: str = None,
        prompt: str = None,
        audio_duration: float = None,
        expression_scale: float = 1.0,
        face_enhance: bool = True
    ) -> Dict:
        """
        Start async talking avatar video generation using HeyGen
        Returns immediately with video_id for status polling.
        
        Args:
            audio_url: URL to audio file (must be publicly accessible)
            image_url: URL to avatar image (frontal photo) - used as talking_photo
            avatar_id: Optional HeyGen avatar ID (if not using talking_photo)
            prompt: Not used in HeyGen (kept for API compatibility)
            audio_duration: Not used in HeyGen (kept for API compatibility)
            expression_scale: Not used in HeyGen (kept for API compatibility) 
            face_enhance: Not used in HeyGen (kept for API compatibility)
            
        Returns:
            Dict with video_id for polling
        """
        api_key = current_app.config.get('HEYGEN_API_KEY')
        if not api_key:
            raise ValueError("HEYGEN_API_KEY not configured")
        
        try:
            current_app.logger.info(f"Starting HeyGen video generation (async)...")
            current_app.logger.info(f"Audio URL: {audio_url}")
            current_app.logger.info(f"Image URL: {image_url}")
            
            headers = {
                'X-Api-Key': api_key,
                'Content-Type': 'application/json'
            }
            
            # First, upload the photo to get talking_photo_id
            current_app.logger.info("Step 1: Uploading photo to HeyGen...")
            talking_photo_id = HeyGenHelper.upload_talking_photo(image_url)
            current_app.logger.info(f"Got talking_photo_id: {talking_photo_id}")
            
            # Build request body with talking_photo_id
            video_inputs = [{
                "character": {
                    "type": "talking_photo",
                    "talking_photo_id": talking_photo_id,
                    "talking_style": "stable"  # or "expressive"
                },
                "voice": {
                    "type": "audio",
                    "audio_url": audio_url
                },
                "background": {
                    "type": "color",
                    "value": "#000000"  # Black background
                }
            }]
            
            request_body = {
                "video_inputs": video_inputs,
                "dimension": {
                    "width": 832,
                    "height": 1088
                },
                "aspect_ratio": "9:16",  # Vertical video for mobile
                "test": False  # Set to True for watermarked test videos
            }
            
            current_app.logger.info(f"HeyGen request body: {request_body}")
            
            # Submit request to HeyGen
            response = requests.post(
                f"{HeyGenHelper.BASE_URL}/v2/video/generate",
                headers=headers,
                json=request_body,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            current_app.logger.info(f"HeyGen response: {result}")
            
            # Extract video_id from response
            if result.get('error'):
                error_msg = result.get('error', {}).get('message', 'Unknown error')
                current_app.logger.error(f"HeyGen API error: {error_msg}")
                raise RuntimeError(f"HeyGen error: {error_msg}")
            
            video_id = result.get('data', {}).get('video_id')
            
            if not video_id:
                raise ValueError("No video_id in HeyGen response")
            
            current_app.logger.info(f"HeyGen request submitted: {video_id}")

            return {
                'request_id': video_id,  # Use video_id as request_id for compatibility
                'status': 'processing'
            }
            
        except requests.exceptions.HTTPError as e:
            try:
                error_body = e.response.json()
                error_msg = error_body.get('error', {}).get('message', str(e))
                current_app.logger.error(f"HeyGen HTTP error: {e.response.status_code} - {error_msg}")
                raise RuntimeError(f"HeyGen API error: {error_msg}")
            except Exception:
                current_app.logger.error(f"HeyGen HTTP error: {str(e)}")
                raise RuntimeError(f"HeyGen API error: {str(e)}")
                
        except Exception as e:
            current_app.logger.error(f"HeyGen generation error: {str(e)}")
            current_app.logger.error(f"Error type: {type(e).__name__}")
            raise RuntimeError(str(e))
    
    @staticmethod
    def check_status(video_id: str) -> Dict:
        """
        Check current status of HeyGen video generation
        
        Args:
            video_id: HeyGen video ID (can also be called request_id for compatibility)
            
        Returns:
            Dict with status info and video_url if completed
        """
        try:
            current_app.logger.info(f"Checking HeyGen status for video: {video_id}")
            
            api_key = current_app.config.get('HEYGEN_API_KEY')
            if not api_key:
                raise ValueError("HEYGEN_API_KEY not configured")
            
            headers = {
                'X-Api-Key': api_key
            }
            
            # Check status via Video Status API
            status_url = f"{HeyGenHelper.BASE_URL}/v1/video_status.get"
            
            response = requests.get(
                status_url,
                headers=headers,
                params={'video_id': video_id},
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            current_app.logger.info(f"HeyGen status response: {result}")
            
            if result.get('error'):
                error_msg = result.get('error', {}).get('message', 'Unknown error')
                current_app.logger.error(f"HeyGen status error: {error_msg}")
                return {'status': 'error', 'error': error_msg}
            
            data = result.get('data', {})
            status = data.get('status')
            
            current_app.logger.info(f"Video status: {status}")
            
            # HeyGen status values:
            # pending - waiting to start
            # processing - currently rendering
            # completed - finished successfully
            # failed - error occurred
            
            if status == 'completed':
                video_url = data.get('video_url')
                
                if not video_url:
                    current_app.logger.error("No video URL in completed response")
                    return {'status': 'error', 'error': 'No video URL in response'}
                
                current_app.logger.info(f"HeyGen generation completed: {video_url}")
                return {
                    'status': 'completed',
                    'video_url': video_url
                }
            
            elif status in ['pending', 'processing']:
                current_app.logger.info(f"Generation in progress: {status}")
                return {'status': 'processing'}
            
            elif status == 'failed':
                error_msg = data.get('error', 'Video generation failed')
                current_app.logger.error(f"HeyGen generation failed: {error_msg}")
                return {'status': 'error', 'error': error_msg}
            
            else:
                # Unknown status
                current_app.logger.warning(f"Unknown status: {status}")
                return {'status': 'processing'}  # Treat unknown as still processing
                
        except requests.exceptions.HTTPError as e:
            try:
                error_body = e.response.json()
                error_msg = error_body.get('error', {}).get('message', str(e))
                current_app.logger.error(f"HeyGen status check HTTP error: {error_msg}")
            except Exception:
                error_msg = str(e)
                current_app.logger.error(f"HeyGen status check HTTP error: {error_msg}")
            
            return {
                'status': 'error',
                'error': error_msg
            }
                
        except Exception as e:
            current_app.logger.error(f"HeyGen status check error: {str(e)}")
            current_app.logger.error(f"Error type: {type(e).__name__}")
            return {
                'status': 'error',
                'error': str(e)
            }


heygen_helper = HeyGenHelper()
