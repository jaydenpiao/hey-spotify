"""Spotify playback control."""
from services.spotify.client import SpotifyClient
from services.spotify.models import PlaybackState, Track, Device
from core.errors import NoActiveDeviceError
from core.logging import get_logger

logger = get_logger(__name__)


async def get_current_playback(user_id: str) -> PlaybackState | None:
    """Get current playback state.
    
    Args:
        user_id: User ID
        
    Returns:
        Playback state or None if nothing is playing
    """
    async with SpotifyClient(user_id) as client:
        data = await client.get("/me/player")
        if data:
            return PlaybackState(**data)
        return None


async def play(
    user_id: str,
    track_uri: str | None = None,
    device_id: str | None = None,
    context_uri: str | None = None,
) -> None:
    """Start or resume playback.
    
    Args:
        user_id: User ID
        track_uri: Spotify URI of track to play
        device_id: Target device ID
        context_uri: Spotify URI of album/playlist/artist
        
    Raises:
        NoActiveDeviceError: If no device is available
    """
    async with SpotifyClient(user_id) as client:
        body = {}
        if track_uri:
            body["uris"] = [track_uri]
        if context_uri:
            body["context_uri"] = context_uri
        
        params = {}
        if device_id:
            params["device_id"] = device_id
        
        try:
            await client.put("/me/player/play", json=body or None, params=params)
            logger.info(f"Started playback for user {user_id}")
        except Exception as e:
            if "NO_ACTIVE_DEVICE" in str(e) or "Device not found" in str(e):
                raise NoActiveDeviceError()
            raise


async def pause(user_id: str, device_id: str | None = None) -> None:
    """Pause playback.
    
    Args:
        user_id: User ID
        device_id: Target device ID
    """
    async with SpotifyClient(user_id) as client:
        params = {}
        if device_id:
            params["device_id"] = device_id
        
        await client.put("/me/player/pause", params=params)
        logger.info(f"Paused playback for user {user_id}")


async def resume(user_id: str, device_id: str | None = None) -> None:
    """Resume playback.
    
    Args:
        user_id: User ID
        device_id: Target device ID
    """
    await play(user_id, device_id=device_id)


async def skip_next(user_id: str, device_id: str | None = None) -> None:
    """Skip to next track.
    
    Args:
        user_id: User ID
        device_id: Target device ID
    """
    async with SpotifyClient(user_id) as client:
        params = {}
        if device_id:
            params["device_id"] = device_id
        
        await client.post("/me/player/next", params=params)
        logger.info(f"Skipped to next track for user {user_id}")


async def skip_previous(user_id: str, device_id: str | None = None) -> None:
    """Skip to previous track.
    
    Args:
        user_id: User ID
        device_id: Target device ID
    """
    async with SpotifyClient(user_id) as client:
        params = {}
        if device_id:
            params["device_id"] = device_id
        
        await client.post("/me/player/previous", params=params)
        logger.info(f"Skipped to previous track for user {user_id}")


async def add_to_queue(user_id: str, track_uri: str, device_id: str | None = None) -> None:
    """Add track to queue.
    
    Args:
        user_id: User ID
        track_uri: Spotify URI of track to queue
        device_id: Target device ID
    """
    async with SpotifyClient(user_id) as client:
        params = {"uri": track_uri}
        if device_id:
            params["device_id"] = device_id
        
        await client.post("/me/player/queue", params=params)
        logger.info(f"Added track to queue for user {user_id}")


async def set_volume(user_id: str, volume_percent: int, device_id: str | None = None) -> None:
    """Set playback volume.
    
    Args:
        user_id: User ID
        volume_percent: Volume (0-100)
        device_id: Target device ID
    """
    async with SpotifyClient(user_id) as client:
        params = {"volume_percent": max(0, min(100, volume_percent))}
        if device_id:
            params["device_id"] = device_id
        
        await client.put("/me/player/volume", params=params)
        logger.info(f"Set volume to {volume_percent}% for user {user_id}")
