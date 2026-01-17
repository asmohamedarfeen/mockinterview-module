"""
Google Cloud Text-to-Speech Client
Female professional voice for interview questions
"""
import os
import base64
import logging
from typing import Optional
import google.cloud.texttospeech as texttospeech
from google.oauth2 import service_account

from app.core.config import settings

logger = logging.getLogger(__name__)


class GoogleTTSClient:
    """
    Client for Google Cloud Text-to-Speech
    Uses female professional voice (en-US-Neural2-F)
    """
    
    def __init__(self):
        """Initialize Google TTS client"""
        self.client = None
        self.voice_name = "en-US-Neural2-F"  # Female professional voice
        self.language_code = "en-US"
        
        try:
            # Try service account first
            if settings.google_tts_service_account_path and os.path.exists(settings.google_tts_service_account_path):
                credentials = service_account.Credentials.from_service_account_file(
                    settings.google_tts_service_account_path
                )
                self.client = texttospeech.TextToSpeechClient(credentials=credentials)
                logger.info("Google TTS initialized with service account")
            # Try API key (if available in future)
            elif settings.google_tts_key:
                # Note: TTS typically requires service account, but keeping for flexibility
                self.client = texttospeech.TextToSpeechClient()
                logger.info("Google TTS initialized with API key")
            else:
                # Try default credentials (for GCP environments)
                try:
                    self.client = texttospeech.TextToSpeechClient()
                    logger.info("Google TTS initialized with default credentials")
                except Exception as e:
                    logger.warning(f"Google TTS not configured: {e}")
                    self.client = None
        except Exception as e:
            logger.error(f"Failed to initialize Google TTS client: {e}")
            self.client = None
    
    def synthesize_speech(
        self, 
        text: str, 
        voice_name: Optional[str] = None,
        speaking_rate: float = 1.0
    ) -> Optional[str]:
        """
        Synthesize speech from text and return base64 encoded audio
        
        Args:
            text: Text to convert to speech
            voice_name: Voice name (defaults to en-US-Neural2-F)
            speaking_rate: Speaking rate (0.25 to 4.0, default 1.0)
            
        Returns:
            Base64 encoded MP3 audio string, or None if failed
        """
        if not self.client:
            logger.warning("Google TTS client not available")
            return None
        
        try:
            # Configure voice
            voice = texttospeech.VoiceSelectionParams(
                language_code=self.language_code,
                name=voice_name or self.voice_name,
            )
            
            # Configure audio output
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=speaking_rate,
                pitch=0.0,  # Neutral pitch
                volume_gain_db=0.0,  # No volume adjustment
            )
            
            # Synthesize speech
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            # Encode audio to base64
            audio_base64 = base64.b64encode(response.audio_content).decode('utf-8')
            
            logger.info(f"Generated TTS audio for text: {text[:50]}... ({len(audio_base64)} bytes)")
            return audio_base64
            
        except Exception as e:
            logger.error(f"Failed to synthesize speech: {e}", exc_info=True)
            return None
    
    def synthesize_speech_bytes(
        self,
        text: str,
        voice_name: Optional[str] = None,
        speaking_rate: float = 1.0
    ) -> Optional[bytes]:
        """
        Synthesize speech and return raw audio bytes
        
        Args:
            text: Text to convert to speech
            voice_name: Voice name
            speaking_rate: Speaking rate
            
        Returns:
            Raw MP3 audio bytes, or None if failed
        """
        if not self.client:
            return None
        
        try:
            voice = texttospeech.VoiceSelectionParams(
                language_code=self.language_code,
                name=voice_name or self.voice_name,
            )
            
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=speaking_rate,
            )
            
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            return response.audio_content
            
        except Exception as e:
            logger.error(f"Failed to synthesize speech bytes: {e}", exc_info=True)
            return None
    
    def is_available(self) -> bool:
        """Check if TTS client is available"""
        return self.client is not None


# Global TTS client instance
tts_client = GoogleTTSClient()
