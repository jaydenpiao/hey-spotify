"""LLM-based intent compiler using OpenAI GPT-4o with structured outputs."""
import time
import yaml
from pathlib import Path
from openai import AsyncOpenAI
from pydantic import ValidationError

from services.intent.schema import Intent, IntentType, IntentArgs, QueryType
from core.config import settings
from core.logging import get_logger
from core.errors import HeySpotifyError

logger = get_logger(__name__)


class LLMCompilerError(HeySpotifyError):
    """Error in LLM intent compilation."""
    pass


# JSON Schema for GPT-5.2 structured output
INTENT_SCHEMA = {
    "name": "spotify_intent",
    "strict": True,
    "schema": {
        "type": "object",
        "required": ["intent", "confidence", "args", "needs_disambiguation"],
        "properties": {
            "intent": {
                "type": "string",
                "enum": [
                    "PLAY", "PAUSE", "RESUME", "SKIP_NEXT", "SKIP_PREV",
                    "QUEUE", "GET_DEVICES", "GET_NOW_PLAYING", "SEARCH",
                    "SET_VOLUME", "TRANSFER_PLAYBACK", "UNKNOWN"
                ]
            },
            "confidence": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0
            },
            "args": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": ["string", "null"],
                        "default": None
                    },
                    "query_type": {
                        "type": ["string", "null"],
                        "enum": ["track", "artist", "playlist", "album", "mixed", None],
                        "default": None
                    },
                    "volume_percent": {
                        "type": ["integer", "null"],
                        "minimum": 0,
                        "maximum": 100,
                        "default": None
                    }
                },
                "required": ["query", "query_type", "volume_percent"],
                "additionalProperties": False
            },
            "needs_disambiguation": {
                "type": "boolean",
                "default": False
            }
        },
        "additionalProperties": False
    }
}


def _load_examples() -> str:
    """Load few-shot examples from YAML file.
    
    Returns:
        Formatted examples string for prompt
    """
    examples_path = Path(__file__).parent / "examples.yaml"
    
    try:
        with open(examples_path, 'r') as f:
            data = yaml.safe_load(f)
        
        # Select best 5 examples for few-shot prompting
        examples = data.get('examples', [])[:5]
        
        formatted = []
        for ex in examples:
            utterance = ex['utterance']
            intent_data = ex['intent']
            
            # Format as example
            formatted.append(f"User: {utterance}")
            formatted.append(f"Intent: {intent_data}")
            formatted.append("")
        
        return "\n".join(formatted)
    
    except Exception as e:
        logger.warning(f"Could not load examples: {e}")
        # Return minimal examples if file can't be loaded
        return """User: pause
Intent: {'intent': 'PAUSE', 'confidence': 1.0, 'args': {}, 'needs_disambiguation': False}

User: play bohemian rhapsody by queen
Intent: {'intent': 'PLAY', 'confidence': 1.0, 'args': {'query': 'bohemian rhapsody queen', 'query_type': 'track'}, 'needs_disambiguation': False}
"""


def _build_system_prompt() -> str:
    """Build system prompt with instructions and examples.
    
    Returns:
        Complete system prompt
    """
    examples = _load_examples()
    
    return f"""You are a Spotify voice assistant intent parser. Convert user commands into structured JSON intents.

Available intents:
- PLAY: Play music (requires query)
- PAUSE: Pause playback
- RESUME: Resume playback
- SKIP_NEXT: Skip to next track
- SKIP_PREV: Go to previous track
- QUEUE: Add track to queue (requires query)
- GET_DEVICES: List Spotify devices
- GET_NOW_PLAYING: Get currently playing track
- SEARCH: Search for music (requires query)
- SET_VOLUME: Set volume (requires volume_percent)
- TRANSFER_PLAYBACK: Switch playback device (requires query)
- UNKNOWN: Unrecognized command

Rules:
1. Extract queries by removing command words (e.g., "play jazz" → query: "jazz")
2. Infer confidence based on clarity (0.0-1.0)
3. Set needs_disambiguation to true for ambiguous commands
4. Default query_type to "mixed" unless clearly specified
5. Be lenient with natural language variations

Examples:
{examples}

Always return valid JSON matching the schema."""


class LLMIntentCompiler:
    """OpenAI GPT-4o intent compiler with structured outputs."""
    
    def __init__(self):
        """Initialize LLM compiler."""
        if not settings.openai_api_key:
            raise LLMCompilerError("OpenAI API key not configured")
        
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.system_prompt = _build_system_prompt()
    
    async def compile(self, command: str) -> Intent:
        """Compile natural language command to structured intent.
        
        Args:
            command: User command text
            
        Returns:
            Parsed Intent object
            
        Raises:
            LLMCompilerError: If compilation fails
        """
        start_time = time.perf_counter()
        
        try:
            # Build API parameters
            # GPT-5.x models use max_completion_tokens
            # GPT-4.x and earlier use max_tokens
            api_params = {
                "model": settings.llm_model,
                "messages": [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"Parse this command: {command}"}
                ],
                "response_format": {
                    "type": "json_schema",
                    "json_schema": INTENT_SCHEMA
                },
                "temperature": settings.llm_temperature,
            }
            
            # Use correct parameter name based on model version
            if settings.llm_model.startswith("gpt-5"):
                api_params["max_completion_tokens"] = settings.llm_max_tokens
            else:
                api_params["max_tokens"] = settings.llm_max_tokens
            
            # Call OpenAI API with structured output
            response = await self.client.chat.completions.create(**api_params)
            
            latency_ms = (time.perf_counter() - start_time) * 1000
            
            # Extract JSON from response
            content = response.choices[0].message.content
            
            if not content:
                raise LLMCompilerError("Empty response from LLM")
            
            # Parse JSON
            import json
            intent_data = json.loads(content)
            
            # Validate and convert to Intent model
            intent = Intent(
                intent=IntentType(intent_data['intent']),
                confidence=intent_data['confidence'],
                args=IntentArgs(**intent_data.get('args', {})),
                needs_disambiguation=intent_data.get('needs_disambiguation', False),
                raw_command=command
            )
            
            logger.info(
                f"LLM compiled: '{command}' -> {intent.intent}",
                extra={
                    "intent": intent.intent.value,
                    "confidence": intent.confidence,
                    "latency_ms": round(latency_ms, 2),
                }
            )
            
            return intent
        
        except ValidationError as e:
            logger.error(f"Intent validation error: {e}")
            raise LLMCompilerError(f"Invalid intent structure: {e}")
        
        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"LLM compilation failed: {e}",
                extra={"latency_ms": round(latency_ms, 2)},
                exc_info=True
            )
            raise LLMCompilerError(f"LLM compilation failed: {str(e)}") from e


# Global instance
_llm_compiler = None


def get_llm_compiler() -> LLMIntentCompiler:
    """Get or create LLM compiler instance.
    
    Returns:
        LLMIntentCompiler instance
    """
    global _llm_compiler
    if _llm_compiler is None:
        _llm_compiler = LLMIntentCompiler()
    return _llm_compiler


async def compile_intent_with_llm(command: str) -> Intent:
    """Compile natural language command to intent using LLM.
    
    Args:
        command: User command text
        
    Returns:
        Parsed Intent object
        
    Raises:
        LLMCompilerError: If compilation fails
    """
    compiler = get_llm_compiler()
    return await compiler.compile(command)
