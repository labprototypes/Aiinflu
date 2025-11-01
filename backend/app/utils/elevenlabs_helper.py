"""ElevenLabs TTS helper for audio generation with timestamps."""
import requests
import base64
from flask import current_app


class ElevenLabsHelper:
    """Helper class for ElevenLabs text-to-speech."""
    
    def __init__(self):
        """Initialize ElevenLabs helper."""
        self.base_url = "https://api.elevenlabs.io/v1"
    
    def _get_headers(self):
        """Get API headers."""
        return {
            "xi-api-key": current_app.config['ELEVENLABS_API_KEY'],
            "Content-Type": "application/json"
        }
    
    def generate_speech_with_timestamps(
        self,
        text: str,
        voice_id: str,
        model_id: str = "eleven_multilingual_v2"
    ) -> dict:
        """
        Generate speech with character-level timestamps.
        
        Args:
            text: Text to convert to speech
            voice_id: ElevenLabs voice ID
            model_id: Model to use (default: eleven_multilingual_v2)
            
        Returns:
            dict: {
                'audio_base64': str,
                'audio_url': str (after S3 upload),
                'alignment': {
                    'characters': list,
                    'character_start_times_seconds': list,
                    'character_end_times_seconds': list
                }
            }
        """
        url = f"{self.base_url}/text-to-speech/{voice_id}/with-timestamps"
        
        payload = {
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0,
                "use_speaker_boost": True
            }
        }
        
        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Upload audio to S3
            from app.utils.s3_helper import s3_helper
            audio_bytes = base64.b64decode(data['audio_base64'])
            
            # Create file-like object for S3 upload
            from io import BytesIO
            audio_file = BytesIO(audio_bytes)
            audio_file.name = f"audio_{voice_id}.mp3"
            audio_file.content_type = "audio/mpeg"
            
            audio_url = s3_helper.upload_file(audio_file, folder='audio')
            
            return {
                'audio_url': audio_url,
                'alignment': data.get('alignment'),
                'normalized_alignment': data.get('normalized_alignment')
            }
            
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"ElevenLabs API error: {str(e)}")
            raise Exception(f"Failed to generate speech: {str(e)}")
    
    def list_voices(self) -> list:
        """
        List available voices.
        
        Returns:
            list: Available voices with IDs and metadata
        """
        url = f"{self.base_url}/voices"
        
        try:
            response = requests.get(url, headers=self._get_headers())
            response.raise_for_status()
            return response.json().get('voices', [])
        except Exception as e:
            current_app.logger.error(f"Failed to list voices: {str(e)}")
            return []


# Global instance
elevenlabs_helper = ElevenLabsHelper()
