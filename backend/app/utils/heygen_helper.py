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
    def list_avatars() -> Dict:
        """
        Get list of available avatars from HeyGen account
        
        Returns:
            Dict with avatars list
        """
        api_key = current_app.config.get('HEYGEN_API_KEY')
        if not api_key:
            raise ValueError("HEYGEN_API_KEY not configured")
        
        try:
            current_app.logger.info("Fetching avatars list from HeyGen...")
            
            headers = {
                'X-Api-Key': api_key
            }
            
            # Try v2 API first
            response = requests.get(
                f"{HeyGenHelper.BASE_URL}/v2/avatars",
                headers=headers,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            current_app.logger.info(f"HeyGen avatars response: {result}")
            
            return result
            
        except Exception as e:
            current_app.logger.error(f"Failed to fetch avatars: {str(e)}")
            raise RuntimeError(f"Failed to fetch avatars: {str(e)}")
    
    @staticmethod
    def upload_asset(image_url: str) -> str:
        """
        Upload an image asset to HeyGen and get image_key
        
        Args:
            image_url: URL to the image file (must be publicly accessible)
            
        Returns:
            image_key for creating photo avatar group
        """
        api_key = current_app.config.get('HEYGEN_API_KEY')
        if not api_key:
            raise ValueError("HEYGEN_API_KEY not configured")
        
        try:
            current_app.logger.info(f"Uploading asset to HeyGen: {image_url}")
            
            # Download the image first
            current_app.logger.info("Downloading image from S3...")
            image_response = requests.get(image_url, timeout=60)
            image_response.raise_for_status()
            image_data = image_response.content
            current_app.logger.info(f"Image downloaded, size: {len(image_data)} bytes")
            
            # HeyGen expects raw binary data with Content-Type: image/png
            headers = {
                'accept': 'application/json',
                'Content-Type': 'image/png',
                'X-Api-Key': api_key
            }
            
            # Send raw binary data in body
            response = requests.post(
                "https://upload.heygen.com/v1/asset",
                headers=headers,
                data=image_data,  # Raw binary data
                timeout=120
            )
            
            current_app.logger.info(f"Upload asset response status: {response.status_code}")
            current_app.logger.info(f"Upload asset response body: {response.text}")
            
            # Parse response first before raising error
            try:
                result = response.json()
            except Exception as json_error:
                current_app.logger.error(f"Failed to parse JSON response: {json_error}")
                current_app.logger.error(f"Raw response: {response.text}")
                response.raise_for_status()  # Will show HTTP error
                raise
            
            # Check HTTP status after we have the result
            if response.status_code >= 400:
                error_msg = result.get('message', result.get('error', {}).get('message', 'Unknown error'))
                current_app.logger.error(f"HeyGen API error: {error_msg}")
                current_app.logger.error(f"Full response: {result}")
                raise RuntimeError(f"HeyGen API error ({response.status_code}): {error_msg}")
            
            current_app.logger.info(f"HeyGen upload asset response: {result}")
            
            # Check for error in response
            if result.get('error'):
                error_msg = result.get('error', {}).get('message', 'Unknown error')
                raise RuntimeError(f"HeyGen upload asset error: {error_msg}")
            
            if result.get('code') and result.get('code') != 100:
                # HeyGen returns error with code/message at root level
                error_msg = result.get('message', 'Unknown error')
                current_app.logger.error(f"HeyGen upload asset error: {error_msg}")
                current_app.logger.error(f"Full error response: {result}")
                raise RuntimeError(f"HeyGen upload asset error ({result.get('code')}): {error_msg}")
            
            image_key = result.get('data', {}).get('image_key')
            
            if not image_key:
                raise ValueError("No image_key in HeyGen response")
            
            current_app.logger.info(f"Asset uploaded successfully: {image_key}")
            return image_key
            
        except Exception as e:
            current_app.logger.error(f"Failed to upload asset: {str(e)}")
            raise RuntimeError(f"Asset upload failed: {str(e)}")
    
    @staticmethod
    def create_photo_avatar_group(name: str, image_key: str) -> Dict:
        """
        Create a photo avatar group with a single image
        
        Args:
            name: Name for the avatar group
            image_key: Image key from upload_asset
            
        Returns:
            Dict with group_id and avatar_id
        """
        api_key = current_app.config.get('HEYGEN_API_KEY')
        if not api_key:
            raise ValueError("HEYGEN_API_KEY not configured")
        
        try:
            current_app.logger.info(f"Creating photo avatar group: {name}")
            
            headers = {
                'X-Api-Key': api_key,
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                f"{HeyGenHelper.BASE_URL}/v2/photo_avatar/avatar_group/create",
                headers=headers,
                json={
                    'name': name,
                    'image_key': image_key
                },
                timeout=60
            )
            
            current_app.logger.info(f"Create group response status: {response.status_code}")
            current_app.logger.info(f"Create group response body: {response.text}")
            
            response.raise_for_status()
            result = response.json()
            
            current_app.logger.info(f"HeyGen create group response: {result}")
            
            if result.get('error'):
                error_msg = result.get('error', {}).get('message', 'Unknown error')
                raise RuntimeError(f"HeyGen create group error: {error_msg}")
            
            # Check for errors at root level
            if result.get('code') and result.get('code') != 100:
                error_msg = result.get('message', 'Unknown error')
                current_app.logger.error(f"HeyGen create group error: {error_msg}")
                raise RuntimeError(f"HeyGen create group error ({result.get('code')}): {error_msg}")
            
            data = result.get('data', {})
            # HeyGen returns 'id' for group_id, and 'id' is also the avatar_id
            group_id = data.get('id')  # This is the group_id
            avatar_id = data.get('id')  # This is also the avatar_id (same value)
            
            if not group_id:
                raise ValueError("No id in HeyGen response")
            
            current_app.logger.info(f"Avatar group created: group_id={group_id}, avatar_id={avatar_id}")
            
            # Wait for avatar to be ready (processing is asynchronous)
            current_app.logger.info("Waiting for avatar to complete processing...")
            talking_photo_id = HeyGenHelper._wait_for_avatar_ready(avatar_id)
            
            # If talking_photo_id not in status response, get it from group
            if not talking_photo_id:
                current_app.logger.info("talking_photo_id not found in status, getting from group...")
                talking_photo_id = HeyGenHelper.get_talking_photo_id_from_group(group_id)
            
            current_app.logger.info(f"Final talking_photo_id: {talking_photo_id}")
            
            return {
                'group_id': group_id,
                'avatar_id': avatar_id,
                'talking_photo_id': talking_photo_id
            }
            
        except Exception as e:
            current_app.logger.error(f"Failed to create avatar group: {str(e)}")
            raise RuntimeError(f"Avatar group creation failed: {str(e)}")
    
    @staticmethod
    def get_talking_photo_id_from_group(group_id: str) -> str:
        """
        Get talking_photo_id from an avatar group
        
        Args:
            group_id: Avatar group ID
            
        Returns:
            talking_photo_id for video generation
        """
        api_key = current_app.config.get('HEYGEN_API_KEY')
        if not api_key:
            raise ValueError("HEYGEN_API_KEY not configured")
        
        try:
            current_app.logger.info(f"Getting talking_photo_id from group: {group_id}")
            
            headers = {
                'accept': 'application/json',
                'x-api-key': api_key
            }
            
            # List all avatars in the group
            response = requests.get(
                f"{HeyGenHelper.BASE_URL}/v2/photo_avatar/avatar_group/{group_id}",
                headers=headers,
                timeout=30
            )
            
            current_app.logger.info(f"Get group response status: {response.status_code}")
            current_app.logger.info(f"Get group response body: {response.text}")
            
            response.raise_for_status()
            result = response.json()
            
            if result.get('error'):
                error_msg = result.get('error', {}).get('message', 'Unknown error')
                raise RuntimeError(f"HeyGen get group error: {error_msg}")
            
            data = result.get('data', {})
            avatars = data.get('avatars', [])
            
            if not avatars:
                raise ValueError(f"No avatars found in group {group_id}")
            
            # Get the first avatar's talking_photo_id
            talking_photo_id = avatars[0].get('talking_photo_id')
            
            if not talking_photo_id:
                raise ValueError(f"No talking_photo_id found in group {group_id}")
            
            current_app.logger.info(f"Found talking_photo_id: {talking_photo_id}")
            return talking_photo_id
            
        except Exception as e:
            current_app.logger.error(f"Failed to get talking_photo_id: {str(e)}")
            raise RuntimeError(f"Failed to get talking_photo_id: {str(e)}")
    
    @staticmethod
    def _wait_for_avatar_ready(avatar_id: str, max_wait: int = 60, poll_interval: int = 3) -> Optional[str]:
        """
        Poll avatar status until it's ready for use
        
        Args:
            avatar_id: Avatar ID to check
            max_wait: Maximum seconds to wait (default 60)
            poll_interval: Seconds between polls (default 3)
            
        Returns:
            talking_photo_id if found, None otherwise
        """
        api_key = current_app.config.get('HEYGEN_API_KEY')
        if not api_key:
            raise ValueError("HEYGEN_API_KEY not configured")
        
        headers = {
            'accept': 'application/json',
            'x-api-key': api_key
        }
        
        start_time = time.time()
        
        while True:
            elapsed = time.time() - start_time
            
            if elapsed > max_wait:
                current_app.logger.warning(f"Avatar {avatar_id} not ready after {max_wait}s, continuing anyway...")
                return  # Continue without error - might work
            
            try:
                # Check avatar status
                response = requests.get(
                    f"{HeyGenHelper.BASE_URL}/v2/photo_avatar/{avatar_id}",
                    headers=headers,
                    timeout=10
                )
                
                current_app.logger.info(f"Avatar status check: {response.status_code}")
                current_app.logger.info(f"Avatar status response: {response.text}")
                
                if response.status_code == 200:
                    result = response.json()
                    data = result.get('data', {})
                    status = data.get('status', 'unknown')
                    talking_photo_id = data.get('talking_photo_id')
                    
                    current_app.logger.info(f"Avatar status: {status} (waited {elapsed:.1f}s)")
                    if talking_photo_id:
                        current_app.logger.info(f"Found talking_photo_id: {talking_photo_id}")
                    
                    if status == 'completed':
                        current_app.logger.info(f"Avatar ready after {elapsed:.1f}s")
                        # Add extra 5 seconds buffer to ensure HeyGen internal sync
                        current_app.logger.info("Adding 5s buffer for HeyGen internal sync...")
                        time.sleep(5)
                        return talking_photo_id
                    elif status == 'failed':
                        raise RuntimeError(f"Avatar processing failed: {data.get('error', 'Unknown error')}")
                
            except requests.exceptions.RequestException as e:
                current_app.logger.warning(f"Error checking avatar status: {e}")
            
            # Wait before next poll
            time.sleep(poll_interval)
    
    @staticmethod
    def add_motion_to_avatar(avatar_id: str, motion_type: str = 'veo2') -> Dict:
        """
        Add motion (gesticulation) to photo avatar
        
        Args:
            avatar_id: Avatar ID from create_photo_avatar_group
            motion_type: Motion engine type (veo2, seedance, runway_gen3, etc.)
            
        Returns:
            Dict with motion status
        """
        api_key = current_app.config.get('HEYGEN_API_KEY')
        if not api_key:
            raise ValueError("HEYGEN_API_KEY not configured")
        
        try:
            current_app.logger.info(f"Adding motion to avatar: {avatar_id}, type={motion_type}")
            
            headers = {
                'accept': 'application/json',
                'content-type': 'application/json',
                'x-api-key': api_key
            }
            
            # API expects 'id' and 'motion_type', not 'avatar_id' and 'type'
            request_body = {
                'id': avatar_id,
                'motion_type': motion_type
            }
            
            current_app.logger.info(f"Add motion request body: {request_body}")
            
            response = requests.post(
                f"{HeyGenHelper.BASE_URL}/v2/photo_avatar/add_motion",
                headers=headers,
                json=request_body,
                timeout=60
            )
            
            current_app.logger.info(f"Add motion response status: {response.status_code}")
            current_app.logger.info(f"Add motion response body: {response.text}")
            
            # Parse response before raising error
            try:
                result = response.json()
            except Exception as json_error:
                current_app.logger.error(f"Failed to parse JSON response: {json_error}")
                current_app.logger.error(f"Raw response: {response.text}")
                response.raise_for_status()
                raise
            
            # Check for errors at any level
            if response.status_code >= 400:
                error_msg = result.get('message', result.get('error', {}).get('message', 'Unknown error'))
                current_app.logger.error(f"HeyGen add motion API error: {error_msg}")
                current_app.logger.error(f"Full error response: {result}")
                raise RuntimeError(f"HeyGen add motion error ({response.status_code}): {error_msg}")
            
            if result.get('error'):
                error_msg = result.get('error', {}).get('message', 'Unknown error')
                raise RuntimeError(f"HeyGen add motion error: {error_msg}")
            
            if result.get('code') and result.get('code') != 100:
                error_msg = result.get('message', 'Unknown error')
                current_app.logger.error(f"HeyGen add motion error: {error_msg}")
                raise RuntimeError(f"HeyGen add motion error ({result.get('code')}): {error_msg}")
            
            current_app.logger.info(f"Motion added successfully to avatar: {avatar_id}")
            return result
            
        except Exception as e:
            current_app.logger.error(f"Failed to add motion: {str(e)}")
            raise RuntimeError(f"Add motion failed: {str(e)}")
    
    @staticmethod
    def upload_talking_photo(image_url: str) -> str:
        """
        Upload a photo to HeyGen and get talking_photo_id
        
        Args:
            image_url: URL to the image file (must be publicly accessible)
            
        Returns:
            talking_photo_id for use in video generation
        """
        api_key = current_app.config.get('HEYGEN_API_KEY')
        if not api_key:
            raise ValueError("HEYGEN_API_KEY not configured")
        
        try:
            current_app.logger.info(f"Uploading talking photo to HeyGen: {image_url}")
            
            headers = {
                'X-Api-Key': api_key,
                'Content-Type': 'application/json'
            }
            
            # Try multiple endpoints (HeyGen API keeps changing)
            endpoints_to_try = [
                # v2 API - Instant Avatar (newer)
                {
                    'url': f"{HeyGenHelper.BASE_URL}/v2/avatars/instant",
                    'payload': {'image_url': image_url}
                },
                # v1 API - Talking Photo (older)
                {
                    'url': f"{HeyGenHelper.BASE_URL}/v1/talking_photo",
                    'payload': {'url': image_url}
                },
            ]
            
            last_error = None
            result = None
            
            for endpoint in endpoints_to_try:
                try:
                    current_app.logger.info(f"Trying endpoint: {endpoint['url']}")
                    
                    response = requests.post(
                        endpoint['url'],
                        headers=headers,
                        json=endpoint['payload'],
                        timeout=60
                    )
                    
                    current_app.logger.info(f"Response status: {response.status_code}")
                    current_app.logger.info(f"Response body: {response.text}")
                    
                    response.raise_for_status()
                    result = response.json()
                    
                    current_app.logger.info(f"HeyGen upload SUCCESS with {endpoint['url']}: {result}")
                    
                    # Success! Break the loop
                    break
                    
                except requests.exceptions.HTTPError as e:
                    last_error = e
                    current_app.logger.warning(f"Endpoint {endpoint['url']} failed: {e}")
                    continue  # Try next endpoint
            
            # Check if all endpoints failed
            if result is None:
                error_msg = f"All HeyGen endpoints failed. Last error: {last_error}"
                current_app.logger.error(error_msg)
                raise RuntimeError(error_msg)
            
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
            
            # HeyGen requires pre-configured avatar_id
            # You must create avatar in HeyGen dashboard first and use its ID
            # For now, use a placeholder or pass avatar_id parameter
            
            if not avatar_id:
                error_msg = (
                    "HeyGen requires a pre-configured avatar_id. "
                    "Please create an avatar in HeyGen dashboard (https://app.heygen.com/avatars) "
                    "and configure it in the blogger settings. "
                    "Current blogger has no avatar_id configured."
                )
                current_app.logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Strip whitespace and validate avatar_id
            avatar_id = avatar_id.strip() if avatar_id else None
            if not avatar_id or avatar_id == "00000":
                error_msg = (
                    "Invalid avatar_id. Please configure a valid HeyGen avatar ID in blogger settings. "
                    "Go to HeyGen dashboard (https://app.heygen.com/avatars) to create or find your avatar ID."
                )
                current_app.logger.error(error_msg)
                raise ValueError(error_msg)
            
            current_app.logger.info(f"Using HeyGen talking_photo_id: {avatar_id} (length: {len(avatar_id)})")
            
            # Use talking_photo_id with type "talking_photo" for Photo Avatar
            video_inputs = [{
                "character": {
                    "type": "talking_photo",
                    "talking_photo_id": avatar_id,
                    "talking_photo_style": "normal"
                },
                "voice": {
                    "type": "audio",
                    "audio_url": audio_url
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
                current_app.logger.error(f"Full error response: {error_body}")
                
                # Add helpful message for 404 avatar errors
                if e.response.status_code == 404 and 'avatar' in error_msg.lower():
                    helpful_msg = (
                        f"Avatar ID '{avatar_id}' not found in your HeyGen account. "
                        "Please verify the avatar ID at https://app.heygen.com/avatars "
                        "and update it in the blogger's location settings."
                    )
                    raise RuntimeError(helpful_msg)
                
                raise RuntimeError(f"HeyGen API error: {error_msg}")
            except RuntimeError:
                raise  # Re-raise our custom errors
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
