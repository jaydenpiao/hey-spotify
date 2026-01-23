"""Voice command endpoints."""
from fastapi import APIRouter, UploadFile, File, HTTPException, Cookie
from pydantic import BaseModel

from services.voice.whisper import get_whisper_client, WhisperError
from services.assistant.orchestrator import process_command
from core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/voice", tags=["voice"])


class TranscribeResponse(BaseModel):
    """Transcription response."""
    transcript: str
    language: str
    duration: float
    latency_ms: float


class VoiceCommandResponse(BaseModel):
    """Voice command execution response."""
    transcript: str
    success: bool
    message: str
    data: dict | None = None
    latency_breakdown: dict


def get_user_id(session_user_id: str | None = Cookie(default=None)) -> str:
    """Get user ID from session cookie."""
    if not session_user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return session_user_id


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: str | None = None,
    user_id: str = Cookie(alias="session_user_id"),
):
    """Transcribe audio file to text using Whisper API.
    
    Args:
        audio: Audio file (webm, mp3, wav, etc.)
        language: Optional language code (e.g., "en")
        user_id: User ID from session
        
    Returns:
        Transcription result with latency metrics
    """
    user_id = get_user_id(user_id)
    
    # Validate file size (25MB = Whisper API limit)
    max_size = 25 * 1024 * 1024  # 25MB
    
    # Read file content
    content = await audio.read()
    
    if len(content) > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is 25MB, got {len(content) / 1024 / 1024:.1f}MB"
        )
    
    if len(content) == 0:
        raise HTTPException(
            status_code=400,
            detail="Empty audio file"
        )
    
    logger.info(
        f"Received audio file for transcription",
        extra={
            "user_id": user_id,
            "filename": audio.filename,
            "content_type": audio.content_type,
            "size_bytes": len(content),
        }
    )
    
    try:
        whisper_client = get_whisper_client()
        result = await whisper_client.transcribe_audio(
            audio_file=content,
            filename=audio.filename or "audio.webm",
            language=language,
        )
        
        return TranscribeResponse(
            transcript=result["text"],
            language=result["language"],
            duration=result["duration"],
            latency_ms=result["latency_ms"],
        )
    
    except WhisperError as e:
        logger.error(f"Whisper transcription failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in transcription: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/command", response_model=VoiceCommandResponse)
async def execute_voice_command(
    audio: UploadFile = File(...),
    language: str | None = None,
    user_id: str = Cookie(alias="session_user_id"),
):
    """Transcribe audio and execute the command.
    
    This is an end-to-end endpoint: audio → transcript → execute
    
    Args:
        audio: Audio file (webm, mp3, wav, etc.)
        language: Optional language code (e.g., "en")
        user_id: User ID from session
        
    Returns:
        Command execution result with latency breakdown
    """
    import time
    
    user_id = get_user_id(user_id)
    overall_start = time.perf_counter()
    
    # Step 1: Transcribe audio
    transcribe_start = time.perf_counter()
    
    content = await audio.read()
    
    if len(content) > 25 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 25MB)")
    
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty audio file")
    
    try:
        whisper_client = get_whisper_client()
        transcription = await whisper_client.transcribe_audio(
            audio_file=content,
            filename=audio.filename or "audio.webm",
            language=language,
        )
        
        transcribe_ms = (time.perf_counter() - transcribe_start) * 1000
        transcript = transcription["text"]
        
        logger.info(
            f"Voice command transcribed: '{transcript}'",
            extra={"user_id": user_id, "transcript": transcript}
        )
        
        # Step 2: Execute command
        execute_start = time.perf_counter()
        result = await process_command(user_id, transcript)
        execute_ms = (time.perf_counter() - execute_start) * 1000
        
        total_ms = (time.perf_counter() - overall_start) * 1000
        
        return VoiceCommandResponse(
            transcript=transcript,
            success=result.success,
            message=result.message,
            data=result.data,
            latency_breakdown={
                "transcribe_ms": round(transcribe_ms, 2),
                "execute_ms": round(execute_ms, 2),
                "total_ms": round(total_ms, 2),
            }
        )
    
    except WhisperError as e:
        logger.error(f"Whisper error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Error executing voice command: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
