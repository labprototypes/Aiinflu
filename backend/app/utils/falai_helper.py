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
            
            arguments_dict = {
                "audio_url": audio_url,
                "image_url": image_url
            }
            current_app.logger.info(f"fal.ai arguments: {arguments_dict}")
            
            # Submit async request (returns immediately)
            handler = fal_client.submit(
                "fal-ai/infinitalk",
                arguments=arguments_dict
            )
            
            request_id = handler.request_id
            current_app.logger.info(f"fal.ai request submitted: {request_id}")
            
            return {
                'request_id': request_id,
                'status': 'processing'
            }
            
        except Exception as e:
            current_app.logger.error(f"fal.ai generation error: {str(e)}")
            current_app.logger.error(f"Error type: {type(e).__name__}")
            if hasattr(e, 'response'):
                current_app.logger.error(f"Response body: {getattr(e.response, 'text', 'N/A')}")
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
                    "image_url": image_url
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
            
            # Use fal_client.status() method directly - it handles everything internally
            try:
                # Try to get result - will raise if not ready
                result = fal_client.result("fal-ai/infinitalk", request_id)
                
                # If we get here, generation is complete
                video_url = result.get('video', {}).get('url')
                
                if video_url:
                    current_app.logger.info(f"fal.ai generation completed: {video_url}")
                    return {
                        'status': 'completed',
                        'video_url': video_url
                    }
                else:
                    current_app.logger.error(f"No video URL in result: {result}")
                    return {'status': 'error', 'error': 'No video URL in response'}
                    
            except Exception as inner_e:
                # If error contains "IN_PROGRESS" or similar, it means still processing
                error_msg = str(inner_e).lower()
                if 'in progress' in error_msg or 'in_progress' in error_msg or 'not completed' in error_msg:
                    current_app.logger.info(f"Generation still in progress")
                    return {'status': 'processing'}
                # Otherwise it's a real error
                raise
                
        except Exception as e:
            current_app.logger.error(f"fal.ai status check error: {str(e)}")
            current_app.logger.error(f"Error type: {type(e).__name__}")
            current_app.logger.error(f"Request ID: {request_id}")
            if hasattr(e, 'response'):
                current_app.logger.error(f"Response status: {getattr(e.response, 'status_code', 'N/A')}")
                current_app.logger.error(f"Response body: {getattr(e.response, 'text', 'N/A')}")
            # Return error status so frontend can stop polling
            return {
                'status': 'error',
                'error': str(e)
            }


falai_helper = FalAIHelper()
