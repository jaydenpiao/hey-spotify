"""Rule-based intent parser using regex patterns."""
import re
from services.intent.schema import Intent, IntentType, IntentArgs, QueryType
from core.logging import get_logger

logger = get_logger(__name__)


# Intent patterns (pattern, intent_type, extract_query)
INTENT_PATTERNS = [
    # Playback control
    (r'^(pause|stop)$', IntentType.PAUSE, False),
    (r'^(resume|continue|unpause)$', IntentType.RESUME, False),
    (r'^(next|skip|skip next)$', IntentType.SKIP_NEXT, False),
    (r'^(previous|back|skip previous|skip back)$', IntentType.SKIP_PREV, False),
    
    # Play commands
    (r'^play\s+(.+)$', IntentType.PLAY, True),
    (r'^start playing\s+(.+)$', IntentType.PLAY, True),
    (r'^put on\s+(.+)$', IntentType.PLAY, True),
    
    # Queue commands
    (r'^queue\s+(.+)$', IntentType.QUEUE, True),
    (r'^add to queue\s+(.+)$', IntentType.QUEUE, True),
    (r'^add\s+(.+)\s+to queue$', IntentType.QUEUE, True),
    
    # Information
    (r'^(devices|list devices|show devices)$', IntentType.GET_DEVICES, False),
    (r'^(now playing|what\'?s playing|current song|what song)$', IntentType.GET_NOW_PLAYING, False),
    
    # Search
    (r'^search\s+(.+)$', IntentType.SEARCH, True),
    (r'^find\s+(.+)$', IntentType.SEARCH, True),
    (r'^look for\s+(.+)$', IntentType.SEARCH, True),
    
    # Volume
    (r'^(volume|set volume)\s+(\d+)$', IntentType.SET_VOLUME, False),
    (r'^set volume to\s+(\d+)$', IntentType.SET_VOLUME, False),
]


def parse_command(command: str) -> Intent:
    """Parse text command into structured intent.
    
    Args:
        command: User command text
        
    Returns:
        Parsed intent
    """
    command_lower = command.lower().strip()
    
    # Try to match patterns
    for pattern, intent_type, has_query in INTENT_PATTERNS:
        match = re.match(pattern, command_lower, re.IGNORECASE)
        if match:
            args = IntentArgs()
            
            # Extract query if present
            if has_query and len(match.groups()) > 0:
                args.query = match.group(1).strip()
            
            # Special handling for volume
            if intent_type == IntentType.SET_VOLUME and len(match.groups()) > 0:
                # Find the volume number in any group
                for group in match.groups():
                    if group and group.isdigit():
                        args.volume_percent = int(group)
                        break
            
            logger.info(f"Parsed command: '{command}' -> {intent_type}", extra={"intent": intent_type.value})
            
            return Intent(
                intent=intent_type,
                confidence=1.0,
                args=args,
                raw_command=command,
            )
    
    # No match found
    logger.warning(f"Could not parse command: '{command}'")
    return Intent(
        intent=IntentType.UNKNOWN,
        confidence=0.0,
        args=IntentArgs(),
        raw_command=command,
    )


def extract_query_type(query: str) -> QueryType:
    """Infer query type from text (for future use).
    
    Args:
        query: Search query
        
    Returns:
        Inferred query type
    """
    query_lower = query.lower()
    
    if any(word in query_lower for word in ['playlist', 'mix']):
        return QueryType.PLAYLIST
    if any(word in query_lower for word in ['album', 'ep']):
        return QueryType.ALBUM
    if any(word in query_lower for word in ['by ', 'artist', 'band']):
        return QueryType.ARTIST
    if any(word in query_lower for word in ['song', 'track']):
        return QueryType.TRACK
    
    return QueryType.MIXED
