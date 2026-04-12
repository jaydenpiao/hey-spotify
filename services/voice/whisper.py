"""OpenAI Whisper API integration for speech-to-text."""
import time
from openai import (
    APIConnectionError,
    APIError,
    APIStatusError,
    APITimeoutError,
    AsyncOpenAI,
    AuthenticationError,
    PermissionDeniedError,
)

from core.config import settings
from core.logging import get_logger
from core.errors import HeySpotifyError, OpenAIDependencyError
from services.openai_status import (
    get_openai_error_code,
    get_voice_unavailable_detail,
    update_openai_dependency_status,
)

logger = get_logger(__name__)


class WhisperError(HeySpotifyError):
    """Error calling Whisper API."""

    def __init__(self, message: str, http_status: int = 500):
        super().__init__(message)
        self.http_status = http_status


class WhisperClient:
    """Client for OpenAI Whisper API."""
    
    def __init__(self):
        """Initialize Whisper client."""
        if not settings.openai_api_key:
            update_openai_dependency_status("missing")
            raise OpenAIDependencyError(
                detail=get_voice_unavailable_detail("missing"),
                error_code=get_openai_error_code("missing") or "openai_missing_config",
                status="missing",
            )
        
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
    
    async def transcribe_audio(
        self,
        audio_file: bytes,
        filename: str = "audio.webm",
        language: str | None = None,
    ) -> dict:
        """Transcribe audio file using Whisper API.
        
        Args:
            audio_file: Audio file bytes
            filename: Original filename (for format detection)
            language: Optional language code (e.g., "en")
            
        Returns:
            Dict with transcript and metadata:
            {
                "text": str,
                "language": str,
                "duration": float,  # seconds
                "latency_ms": float
            }
            
        Raises:
            WhisperError: If transcription fails
        """
        start_time = time.perf_counter()
        
        try:
            # Prepare file for upload
            # Whisper expects a file-like object with name attribute
            file_tuple = (filename, audio_file)
            
            logger.info(
                f"Transcribing audio file: {filename}",
                extra={"audio_filename": filename, "size_bytes": len(audio_file)}
            )
            
            # Call Whisper API
            params = {
                "model": "whisper-1",
                "file": file_tuple,
                "response_format": "verbose_json",  # Get extra metadata
            }
            
            if language:
                params["language"] = language
            
            response = await self.client.audio.transcriptions.create(**params)
            
            latency_ms = (time.perf_counter() - start_time) * 1000
            
            # Extract response data
            transcript = response.text
            detected_language = getattr(response, "language", "unknown")
            duration = getattr(response, "duration", 0.0)
            
            logger.info(
                f"Transcription complete: '{transcript[:50]}...'",
                extra={
                    "transcript_length": len(transcript),
                    "language": detected_language,
                    "duration_seconds": duration,
                    "latency_ms": round(latency_ms, 2),
                }
            )
            
            return {
                "text": transcript,
                "language": detected_language,
                "duration": duration,
                "latency_ms": round(latency_ms, 2),
            }
        
        except (AuthenticationError, PermissionDeniedError) as e:
            update_openai_dependency_status("invalid_auth")
            raise OpenAIDependencyError(
                detail=get_voice_unavailable_detail("invalid_auth"),
                error_code=get_openai_error_code("invalid_auth") or "openai_invalid_auth",
                status="invalid_auth",
            ) from e

        except (APIConnectionError, APITimeoutError, APIStatusError, APIError) as e:
            update_openai_dependency_status("probe_error")
            raise OpenAIDependencyError(
                detail=get_voice_unavailable_detail("probe_error"),
                error_code=get_openai_error_code("probe_error") or "openai_probe_error",
                status="probe_error",
            ) from e

        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"Whisper API error: {e}",
                extra={"latency_ms": round(latency_ms, 2)},
                exc_info=True
            )
            raise WhisperError(f"Failed to transcribe audio: {str(e)}") from e


# Global instance
_whisper_client = None


def get_whisper_client() -> WhisperClient:
    """Get or create Whisper client instance.
    
    Returns:
        WhisperClient instance
    """
    global _whisper_client
    if _whisper_client is None:
        _whisper_client = WhisperClient()
    return _whisper_client
