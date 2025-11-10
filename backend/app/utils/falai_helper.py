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
        prompt: str = None,
        audio_duration: float = None,
        expression_scale: float = 1.0,
        face_enhance: bool = True
    ) -> Dict:
        """
        Start async talking avatar video generation using fal.ai InfiniTalk
        Returns immediately with request_id for status polling.
        
        Args:
            audio_url: URL to audio file (must be publicly accessible)
            image_url: URL to avatar image (frontal photo)
            prompt: Text prompt to guide video generation (REQUIRED by fal.ai)
            audio_duration: Duration of audio in seconds (for calculating num_frames)
            expression_scale: Not used in InfiniTalk (kept for API compatibility)
            face_enhance: Not used in InfiniTalk (kept for API compatibility)
            
        Returns:
            Dict with request_id for polling
        """
        api_key = current_app.config.get('FAL_KEY')
        if not api_key:
            raise ValueError("FAL_KEY not configured")
        
        try:
            print(">>> [falai_helper] Starting fal.ai InfiniTalk generation (async)...")
            print(f">>> [falai_helper] Audio URL: {audio_url}")
            print(f">>> [falai_helper] Image URL: {image_url}")
            print(f">>> [falai_helper] Prompt: {prompt}")
            print(f">>> [falai_helper] Audio duration: {audio_duration}s")
            
            current_app.logger.info(f"Starting fal.ai InfiniTalk generation (async)...")
            current_app.logger.info(f"Audio URL: {audio_url}")
            current_app.logger.info(f"Image URL: {image_url}")
            
            # Generate default prompt if not provided
            if not prompt:
                prompt = "A professional influencer speaking directly to the camera with natural gestures and expressions, delivering engaging content with confidence and authenticity."
            
            # Calculate num_frames based on audio duration
            # InfiniTalk uses 25 FPS, so frames = duration * 25
            # Must be between 41 and 721
            num_frames = 145  # Default
            if audio_duration:
                calculated_frames = int(audio_duration * 25)
                num_frames = max(41, min(721, calculated_frames))
                print(f">>> [falai_helper] Calculated num_frames: {num_frames} (from {audio_duration}s audio)")
            
            arguments_dict = {
                "audio_url": audio_url,
                "image_url": image_url,
                "prompt": prompt,
                "num_frames": num_frames,
                "resolution": "720p",  # Always use 720p as requested
                "acceleration": "regular"  # Standard quality
            }
            print(f">>> [falai_helper] fal.ai arguments: {arguments_dict}")
            current_app.logger.info(f"fal.ai arguments: {arguments_dict}")
            
            # Submit async request (returns immediately)
            try:
                handler = fal_client.submit(
                    "fal-ai/infinitalk",
                    arguments=arguments_dict
                )
            except Exception as submit_err:
                # Try to extract useful info from httpx/HTTPStatusError-like exceptions
                try:
                    import httpx
                    if isinstance(submit_err, httpx.HTTPStatusError):
                        resp = submit_err.response
                        try:
                            body = resp.json()
                        except Exception:
                            body = resp.text
                        current_app.logger.error(f"fal.ai submit HTTP error: {resp.status_code} {body}")
                        raise RuntimeError(f"fal.ai submit failed: {resp.status_code} {body}")
                except Exception:
                    # Fallback generic handling
                    current_app.logger.error(f"fal.ai submit error: {str(submit_err)}")
                    raise
            
            request_id = handler.request_id
            current_app.logger.info(f"fal.ai request submitted: {request_id}")

            return {
                'request_id': request_id,
                'status': 'processing'
            }
            
        except Exception as e:
            # Ensure we log useful details for debugging
            current_app.logger.error(f"fal.ai generation error: {str(e)}")
            current_app.logger.error(f"Error type: {type(e).__name__}")
            try:
                import httpx
                if isinstance(e, httpx.HTTPStatusError) and hasattr(e, 'response'):
                    resp = e.response
                    try:
                        current_app.logger.error(f"Response body: {resp.json()}")
                    except Exception:
                        current_app.logger.error(f"Response body: {getattr(resp, 'text', 'N/A')}")
            except Exception:
                pass
            # Re-raise a runtime error with the message so caller can return a helpful API error
            raise RuntimeError(str(e))
    
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
            print(f">>> [check_status] Checking fal.ai status for request: {request_id}")
            current_app.logger.info(f"Checking fal.ai status for request: {request_id}")
            
            api_key = current_app.config.get('FAL_KEY')
            if not api_key:
                raise ValueError("FAL_KEY not configured")
            
            # Use httpx directly to check status via Queue API
            import httpx
            
            # Create authenticated client
            headers = {
                'Authorization': f'Key {api_key}',
                'Content-Type': 'application/json'
            }
            
            # Check status via Queue API
            status_url = f"https://queue.fal.run/fal-ai/infinitalk/requests/{request_id}/status"
            
            print(f">>> [check_status] Requesting: {status_url}")
            
            with httpx.Client(headers=headers, timeout=30.0) as client:
                response = client.get(status_url)
                response.raise_for_status()
                status_data = response.json()
            
            print(f">>> [check_status] Status data: {status_data}")
            current_app.logger.info(f"Status data: {status_data}")
            
            # Check status field
            status = status_data.get('status')
            
            print(f">>> [check_status] Status: {status}")
            
            if status == 'COMPLETED':
                # Use fal_client.result() to get the completed result
                print(f">>> [check_status] Getting result via fal_client.result()...")
                
                try:
                    result = fal_client.result("fal-ai/infinitalk", request_id)
                    
                    print(f">>> [check_status] Full result: {result}")
                    
                    # Try different possible paths for video URL
                    video_url = None
                    if isinstance(result, dict):
                        # Try video.url
                        if 'video' in result and isinstance(result['video'], dict):
                            video_url = result['video'].get('url')
                        # Try direct video_url
                        elif 'video_url' in result:
                            video_url = result['video_url']
                        # Try data.video_url
                        elif 'data' in result and isinstance(result['data'], dict):
                            video_url = result['data'].get('video_url') or result['data'].get('video', {}).get('url')
                    
                    print(f">>> [check_status] Extracted video_url: {video_url}")
                    
                    if video_url:
                        print(f">>> [check_status] COMPLETED! Video URL: {video_url}")
                        current_app.logger.info(f"fal.ai generation completed: {video_url}")
                        return {
                            'status': 'completed',
                            'video_url': video_url
                        }
                    else:
                        print(f">>> [check_status] ERROR: No video URL in result")
                        current_app.logger.error(f"No video URL in result: {result}")
                        return {'status': 'error', 'error': 'No video URL in response'}
                        
                except Exception as result_error:
                    print(f"!!! [check_status] ERROR getting result: {str(result_error)}")
                    print(f"!!! [check_status] Error type: {type(result_error).__name__}")
                    current_app.logger.error(f"Error getting result: {str(result_error)}")
                    return {'status': 'error', 'error': f'Failed to get result: {str(result_error)}'}
            
            elif status in ['IN_QUEUE', 'IN_PROGRESS']:
                print(f">>> [check_status] Still processing: {status}")
                current_app.logger.info(f"Generation in progress: {status}")
                return {'status': 'processing'}
            
            else:
                # Unknown or error status
                print(f">>> [check_status] Unknown status: {status}")
                current_app.logger.error(f"Unknown status: {status}")
                return {'status': 'error', 'error': f'Unknown status: {status}'}
                
        except Exception as e:
            print(f"!!! [check_status] ERROR: {str(e)}")
            print(f"!!! [check_status] Error type: {type(e).__name__}")
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
