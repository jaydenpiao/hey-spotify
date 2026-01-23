"""Assistant orchestrator - main command flow."""
from services.intent.rules import parse_command
from services.intent.schema import IntentResponse
from services.assistant.executor import execute_intent
from core.logging import get_logger

logger = get_logger(__name__)


async def process_command(user_id: str, command: str) -> IntentResponse:
    """Process a text command end-to-end.
    
    Args:
        user_id: User ID
        command: User command text
        
    Returns:
        Intent response
    """
    logger.info(f"Processing command: '{command}'", extra={"user_id": user_id})
    
    # Step 1: Parse command to intent
    intent = parse_command(command)
    
    # Step 2: Execute intent
    response = await execute_intent(user_id, intent)
    
    logger.info(
        f"Command completed: success={response.success}",
        extra={
            "user_id": user_id,
            "intent": intent.intent.value,
            "success": response.success,
        }
    )
    
    return response
