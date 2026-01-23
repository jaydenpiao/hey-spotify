"""Spotify search functionality."""
from typing import List

from services.spotify.client import SpotifyClient
from services.spotify.models import Track, Artist, Album
from core.logging import get_logger

logger = get_logger(__name__)


async def search_tracks(user_id: str, query: str, limit: int = 10) -> List[Track]:
    """Search for tracks.
    
    Args:
        user_id: User ID
        query: Search query
        limit: Maximum results to return
        
    Returns:
        List of tracks
    """
    async with SpotifyClient(user_id) as client:
        data = await client.get(
            "/search",
            params={
                "q": query,
                "type": "track",
                "limit": limit,
            }
        )
        
        tracks = []
        for item in data.get("tracks", {}).get("items", []):
            # Convert nested artist and album data
            artists = [Artist(**artist) for artist in item.get("artists", [])]
            album_data = item.get("album", {})
            album = Album(
                id=album_data["id"],
                name=album_data["name"],
                uri=album_data["uri"],
                images=album_data.get("images", []),
            )
            
            track = Track(
                id=item["id"],
                name=item["name"],
                uri=item["uri"],
                artists=artists,
                album=album,
                duration_ms=item["duration_ms"],
                explicit=item.get("explicit", False),
            )
            tracks.append(track)
        
        logger.info(f"Found {len(tracks)} tracks for query: {query}")
        return tracks


async def search_artists(user_id: str, query: str, limit: int = 10) -> List[Artist]:
    """Search for artists.
    
    Args:
        user_id: User ID
        query: Search query
        limit: Maximum results to return
        
    Returns:
        List of artists
    """
    async with SpotifyClient(user_id) as client:
        data = await client.get(
            "/search",
            params={
                "q": query,
                "type": "artist",
                "limit": limit,
            }
        )
        
        artists = [Artist(**artist) for artist in data.get("artists", {}).get("items", [])]
        logger.info(f"Found {len(artists)} artists for query: {query}")
        return artists
