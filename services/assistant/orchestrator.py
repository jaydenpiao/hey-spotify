"""Assistant orchestrator - main command flow."""
import time

from services.intent.rules import parse_command
from services.intent.llm_compiler import compile_intent_with_llm, LLMCompilerError
from services.intent.schema import IntentResponse
from services.assistant.executor import execute_intent
from services.openai_status import get_openai_dependency_status
from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)


async def process_command(user_id: str, command: str) -> IntentResponse:
    """Process a text command end-to-end.
    
    Uses LLM intent parser if enabled and available, falls back to regex rules.
    
    Args:
        user_id: User ID
        command: User command text
        
    Returns:
        Intent response
    """
    logger.info(f"Processing command: '{command}'", extra={"user_id": user_id})
    
    parse_start = time.perf_counter()
    parser_used = "regex"
    openai_status = await get_openai_dependency_status()
    
    # Step 1: Parse command to intent
    # Try LLM first only when the dependency is healthy.
    if settings.use_llm_intent_parser and openai_status.status == "ok":
        try:
            intent = await compile_intent_with_llm(command)
            parser_used = "llm"
            
        except LLMCompilerError as e:
            # LLM failed, fall back to regex
            logger.warning(
                f"LLM parser failed, falling back to regex: {e}",
                extra={"error": str(e)}
            )
            intent = parse_command(command)
            parser_used = "regex_fallback"
        
        except Exception as e:
            # Unexpected error, fall back to regex
            logger.error(
                f"Unexpected error in LLM parser, falling back to regex: {e}",
                extra={"error": str(e)},
                exc_info=True
            )
            intent = parse_command(command)
            parser_used = "regex_fallback"
    else:
        intent = parse_command(command)
        if settings.use_llm_intent_parser and openai_status.status != "ok":
            parser_used = "regex_disabled_llm"
        elif not settings.use_llm_intent_parser:
            parser_used = "regex"
    
    parse_latency_ms = (time.perf_counter() - parse_start) * 1000
    
    # Step 2: Execute intent
    response = await execute_intent(user_id, intent)
    
    logger.info(
        f"Command completed: success={response.success}",
        extra={
            "user_id": user_id,
            "intent": intent.intent.value,
            "confidence": intent.confidence,
            "parser_used": parser_used,
            "parse_latency_ms": round(parse_latency_ms, 2),
            "success": response.success,
        }
    )
    
    return response
