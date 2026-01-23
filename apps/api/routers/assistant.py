"""Assistant command endpoint."""
from fastapi import APIRouter, HTTPException, Cookie
from pydantic import BaseModel

from services.assistant.orchestrator import process_command
from services.intent.schema import IntentResponse
from core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/assistant", tags=["assistant"])


class CommandRequest(BaseModel):
    """Command request model."""
    command: str


def get_user_id(session_user_id: str | None = Cookie(default=None)) -> str:
    """Get user ID from session cookie."""
    if not session_user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return session_user_id


@router.post("/command", response_model=IntentResponse)
async def execute_command(
    request: CommandRequest,
    user_id: str = Cookie(alias="session_user_id"),
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
