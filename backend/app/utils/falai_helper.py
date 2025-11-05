import fal_client
import requests
from flask import current_app
from typing import Optional, Dict
import time


class FalAIHelper:
    """Helper for fal.ai InfiniTalk video generation"""
    
    @staticmethod
    def start_avatar_generation(
        audio_url: str,
        image_url: str,
        expression_scale: float = 1.0,
        face_enhance: bool = True
    ) -> Dict:
        """
        Start async talking avatar video generation using fal.ai InfiniTalk
        Returns immediately with request_id for status polling.
        
        Args:
            audio_url: URL to audio file (must be publicly accessible)
            image_url: URL to avatar image (frontal photo)
            expression_scale: Not used in InfiniTalk (kept for API compatibility)
            face_enhance: Not used in InfiniTalk (kept for API compatibility)
            
        Returns:
            Dict with request_id for polling
        """
        api_key = current_app.config.get('FAL_KEY')
        if not api_key:
            raise ValueError("FAL_KEY not configured")
        
        try:
            current_app.logger.info(f"Starting fal.ai InfiniTalk generation (async)...")
            current_app.logger.info(f"Audio URL: {audio_url}")
            current_app.logger.info(f"Image URL: {image_url}")
            
            # Submit async request (returns immediately)
            handler = fal_client.submit(
                "fal-ai/infinitalk",
                arguments={
                    "audio_url": audio_url,
                    "image_url": image_url,
                    "prompt": "A professional content creator speaking naturally on camera",
                    "resolution": "720p",
                    "num_frames": 145,
                    "acceleration": "regular"
                }
            )
            
            request_id = handler.request_id
            current_app.logger.info(f"fal.ai request submitted: {request_id}")
            
            return {
                'request_id': request_id,
                'status': 'processing'
            }
            
        except Exception as e:
            current_app.logger.error(f"fal.ai generation error: {str(e)}")
            raise
    
    @staticmethod
    def generate_avatar_video(
        audio_url: str,
        image_url: str,
        expression_scale: float = 1.0,
        face_enhance: bool = True
    ) -> Dict:
        """
        Generate talking avatar video using fal.ai InfiniTalk (BLOCKING - deprecated)
        Use start_avatar_generation() + check_status() instead for async operation.
        
        Args:
            audio_url: URL to audio file (must be publicly accessible)
            image_url: URL to avatar image (frontal photo)
            expression_scale: Not used in InfiniTalk (kept for API compatibility)
            face_enhance: Not used in InfiniTalk (kept for API compatibility)
            
        Returns:
            Dict with video_url and request_id
        """
        api_key = current_app.config.get('FAL_KEY')
        if not api_key:
            raise ValueError("FAL_KEY not configured")
        
        try:
            current_app.logger.info(f"Starting fal.ai InfiniTalk generation...")
            current_app.logger.info(f"Audio URL: {audio_url}")
            current_app.logger.info(f"Image URL: {image_url}")
            
            # Use subscribe() which waits for completion (blocking)
            # This is intentional - we want the request to wait for the video
            handler = fal_client.submit(
                "fal-ai/infinitalk",
                arguments={
                    "audio_url": audio_url,
                    "image_url": image_url,
                    "prompt": "A professional content creator speaking naturally on camera",
                    "resolution": "720p",
                    "num_frames": 145,
                    "acceleration": "regular"
                }
            )
            
            request_id = handler.request_id
            current_app.logger.info(f"fal.ai request submitted: {request_id}")
            
            # Wait for result (will block until complete, typically 60-120 seconds)
            result = handler.get()
            
            video_url = result.get('video', {}).get('url')
            
            if not video_url:
                raise ValueError("No video URL in fal.ai response")
            
            current_app.logger.info(f"fal.ai InfiniTalk generation complete: {video_url}")
            
            return {
                'video_url': video_url,
                'request_id': request_id,
                'status': 'completed'
            }
            
        except Exception as e:
            current_app.logger.error(f"fal.ai generation error: {str(e)}")
            raise
    
    @staticmethod
    def check_status(request_id: str) -> Dict:
        """
        Check current status of fal.ai generation
        
        Args:
            request_id: fal.ai request ID
            
        Returns:
            Dict with status info and video_url if completed
        """
        try:
            current_app.logger.info(f"Checking fal.ai status for request: {request_id}")
            
            # Use SyncClient to get status by request_id
            from fal_client import sync_client
            
            try:
                # Get result with short timeout (non-blocking check)
                result = sync_client.result("fal-ai/infinitalk", request_id)
                
                video_url = result.get('video', {}).get('url')
                
                if video_url:
                    current_app.logger.info(f"fal.ai generation completed: {video_url}")
                    return {
                        'status': 'completed',
                        'video_url': video_url
                    }
                else:
                    return {'status': 'processing'}
                    
            except TimeoutError:
                # Still processing
                return {'status': 'processing'}
            except Exception as e:
                # Check if it's a "not ready" error
                if 'not ready' in str(e).lower() or 'in progress' in str(e).lower():
                    return {'status': 'processing'}
                else:
                    raise
                
        except Exception as e:
            current_app.logger.error(f"fal.ai status check error: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }


falai_helper = FalAIHelper()
