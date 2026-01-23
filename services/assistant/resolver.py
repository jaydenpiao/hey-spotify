"""Query resolver - converts text queries to Spotify URIs."""
from services.spotify import search
from services.spotify.models import Track
from core.logging import get_logger

logger = get_logger(__name__)


async def resolve_track_query(user_id: str, query: str) -> Track | None:
    """Resolve a text query to a Spotify track.
    
    Args:
        user_id: User ID
        query: Search query
        
    Returns:
        First matching track or None
    """
    tracks = await search.search_tracks(user_id, query, limit=1)
    if tracks:
        logger.info(f"Resolved '{query}' to track: {tracks[0].name}")
        return tracks[0]
    return None


async def resolve_track_uri(user_id: str, query: str) -> str | None:
    """Resolve a text query to a Spotify track URI.
    
    Args:
        user_id: User ID
        query: Search query
        
    Returns:
        Track URI or None
    """
    track = await resolve_track_query(user_id, query)
    return track.uri if track else None
