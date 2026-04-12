"""Wake-word server configuration helpers."""
from pathlib import Path

from fastapi import HTTPException

from core.config import settings

WAKE_KEYWORD_FILE = Path("web/keywords/hey_spotify.ppn")
WAKE_MODEL_FILE = Path("web/models/porcupine_params.pv")


def validate_wake_assets() -> None:
    """Ensure required wake-word assets are present on disk."""
    if not WAKE_MODEL_FILE.exists():
        raise HTTPException(
            status_code=400,
            detail=f"Wake model not found: {WAKE_MODEL_FILE}",
        )

    if not WAKE_KEYWORD_FILE.exists():
        raise HTTPException(
            status_code=400,
            detail=f"Wake keyword not found: {WAKE_KEYWORD_FILE}",
        )


def get_wake_server_availability() -> tuple[bool, str | None]:
    """Return whether the server can offer wake-word configuration."""
    if not settings.picovoice_access_key:
        return False, "Wake word unavailable: PICOVOICE_ACCESS_KEY is not configured."

    if not WAKE_MODEL_FILE.exists():
        return False, "Wake word unavailable: Porcupine model file is missing."

    if not WAKE_KEYWORD_FILE.exists():
        return False, "Wake word unavailable: custom keyword file is missing."

    return True, None
