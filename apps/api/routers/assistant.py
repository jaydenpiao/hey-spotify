"""Assistant command endpoint."""
from typing import Literal

from fastapi import APIRouter, HTTPException, Cookie
from pydantic import BaseModel

from services.assistant.orchestrator import process_command
from services.intent.schema import IntentResponse
from services.openai_status import (
    get_openai_dependency_status,
    get_voice_unavailable_detail,
    get_wake_unavailable_detail,
)
from services.voice.wake import get_wake_server_availability
from core.config import settings
router = APIRouter(prefix="/assistant", tags=["assistant"])


class CommandRequest(BaseModel):
    """Command request model."""
    command: str


class AssistantCapabilitiesResponse(BaseModel):
    """Current frontend capability state."""

    text_command_mode: Literal["llm", "regex"]
    voice_available: bool
    voice_reason: str | None = None
    wake_server_available: bool
    wake_server_reason: str | None = None
    openai_status: Literal["ok", "missing", "invalid_auth", "probe_error"]


def get_user_id(session_user_id: str | None = Cookie(default=None)) -> str:
    """Get user ID from session cookie."""
    if not session_user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return session_user_id


@router.get("/capabilities", response_model=AssistantCapabilitiesResponse)
async def get_capabilities(
    user_id: str | None = Cookie(default=None, alias="session_user_id"),
):
    """Return the current assistant capability surface for the UI."""
    user_id = get_user_id(user_id)
    openai_status = await get_openai_dependency_status()

    text_command_mode: Literal["llm", "regex"] = (
        "llm"
        if settings.use_llm_intent_parser and openai_status.status == "ok"
        else "regex"
    )

    voice_available = openai_status.status == "ok"
    voice_reason = None if voice_available else get_voice_unavailable_detail(openai_status.status)

    if openai_status.status == "ok":
        wake_server_available, wake_server_reason = get_wake_server_availability()
    else:
        wake_server_available = False
        wake_server_reason = get_wake_unavailable_detail(openai_status.status)

    return AssistantCapabilitiesResponse(
        text_command_mode=text_command_mode,
        voice_available=voice_available,
        voice_reason=voice_reason,
        wake_server_available=wake_server_available,
        wake_server_reason=wake_server_reason,
        openai_status=openai_status.status,
    )


@router.post("/command", response_model=IntentResponse)
async def execute_command(
    request: CommandRequest,
    user_id: str | None = Cookie(default=None, alias="session_user_id"),
):
    """Execute a text command.
    
    Args:
        request: Command request
        user_id: User ID from session
        
    Returns:
        Intent response
    """
    user_id = get_user_id(user_id)
    
    if not request.command.strip():
        raise HTTPException(status_code=400, detail="Command cannot be empty")
    
    response = await process_command(user_id, request.command)
    return response
