"""LLM-based intent compiler (for Milestone 2).

This will replace the rules-based parser with OpenAI GPT-4
to generate structured intent JSON from natural language.
"""
from services.intent.schema import Intent, IntentType
from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)


async def compile_intent_with_llm(command: str) -> Intent:
    """Compile natural language command to intent using LLM.
    
    This is a placeholder for Milestone 2.
    Will use OpenAI GPT-4 with strict JSON schema output.
    
    Args:
        command: User command
        
    Returns:
        Parsed intent
    """
    # TODO: Implement in Milestone 2
    # - Use OpenAI API with structured output
    # - Prompt engineering for intent extraction
    # - Validate output against Intent schema
    
    logger.warning("LLM intent compiler not yet implemented (Milestone 2)")
    raise NotImplementedError("LLM intent compiler will be implemented in Milestone 2")
