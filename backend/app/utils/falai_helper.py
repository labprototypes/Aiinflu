import fal_client
import requests
from flask import current_app
from typing import Optional, Dict
import time


class FalAIHelper:
    """Helper for fal.ai InfiniTalk video generation"""
    
    @staticmethod
    def generate_avatar_video(
        audio_url: str,
        image_url: str,
        expression_scale: float = 1.0,
        face_enhance: bool = True
    ) -> Dict:
        """
        Generate talking avatar video using fal.ai InfiniTalk
        
        Args:
            audio_url: URL to audio file
            image_url: URL to avatar image (frontal photo)
            expression_scale: Control expression intensity (0.0-2.0)
            face_enhance: Enable face enhancement
            
        Returns:
            Dict with video_url and request_id
        """
        api_key = current_app.config.get('FAL_KEY')
        if not api_key:
            raise ValueError("FAL_KEY not configured")
        
        try:
            # Submit generation request
            result = fal_client.submit(
                "fal-ai/infini-talk",
                arguments={
                    "audio_url": audio_url,
                    "image_url": image_url,
                    "expression_scale": expression_scale,
                    "face_enhance": face_enhance,
                }
            )
            
            request_id = result.request_id
            current_app.logger.info(f"fal.ai video generation started: {request_id}")
            
            # Poll for completion
            return FalAIHelper.poll_generation_status(request_id)
            
        except Exception as e:
            current_app.logger.error(f"fal.ai generation error: {str(e)}")
            raise
    
    @staticmethod
    def poll_generation_status(request_id: str, max_attempts: int = 60, delay: int = 10) -> Dict:
        """
        Poll fal.ai for generation status
        
        Args:
            request_id: fal.ai request ID
            max_attempts: Maximum polling attempts
            delay: Seconds between polls
            
        Returns:
            Dict with video_url when complete
        """
        api_key = current_app.config.get('FAL_KEY')
        
        for attempt in range(max_attempts):
            try:
                status = fal_client.status("fal-ai/infini-talk", request_id, with_logs=False)
                
                if status.completed:
                    result = fal_client.result("fal-ai/infini-talk", request_id)
                    video_url = result.get('video', {}).get('url')
                    
                    if video_url:
                        current_app.logger.info(f"fal.ai generation complete: {video_url}")
                        return {
                            'video_url': video_url,
                            'request_id': request_id,
                            'status': 'completed'
                        }
                
                # Still processing
                current_app.logger.info(f"fal.ai generation in progress (attempt {attempt + 1}/{max_attempts})")
                time.sleep(delay)
                
            except Exception as e:
                current_app.logger.error(f"fal.ai polling error: {str(e)}")
                if attempt < max_attempts - 1:
                    time.sleep(delay)
                else:
                    raise
        
        raise TimeoutError(f"fal.ai generation timeout after {max_attempts * delay} seconds")
    
    @staticmethod
    def check_status(request_id: str) -> Dict:
        """
        Check current status of fal.ai generation
        
        Args:
            request_id: fal.ai request ID
            
        Returns:
            Dict with status info
        """
        try:
            status = fal_client.status("fal-ai/infini-talk", request_id, with_logs=False)
            
            if status.completed:
                result = fal_client.result("fal-ai/infini-talk", request_id)
                return {
                    'status': 'completed',
                    'video_url': result.get('video', {}).get('url')
                }
            else:
                return {
                    'status': 'processing',
                    'logs': status.logs if hasattr(status, 'logs') else []
                }
        except Exception as e:
            current_app.logger.error(f"fal.ai status check error: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }


falai_helper = FalAIHelper()
