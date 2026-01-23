"""Spotify API endpoints."""
from fastapi import APIRouter, HTTPException, Query, Cookie
from pydantic import BaseModel

from core.errors import NoActiveDeviceError, SpotifyAPIError
from core.logging import get_logger
from services.spotify import devices, playback, search
from services.spotify.models import Device, PlaybackState, Track

logger = get_logger(__name__)
router = APIRouter(prefix="/spotify", tags=["spotify"])


class PlayRequest(BaseModel):
    """Play request model."""
    query: str | None = None
    track_uri: str | None = None
    device_id: str | None = None


class QueueRequest(BaseModel):
    """Queue request model."""
    query: str | None = None
    track_uri: str | None = None
    device_id: str | None = None


class VolumeRequest(BaseModel):
    """Volume request model."""
    volume_percent: int
    device_id: str | None = None


def get_user_id(session_user_id: str | None = Cookie(default=None)) -> str:
    """Get user ID from session cookie.
    
    Args:
        session_user_id: User ID from cookie
        
    Returns:
        User ID
        
    Raises:
        HTTPException: If not authenticated
    """
    if not session_user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return session_user_id


@router.get("/devices", response_model=list[Device])
async def list_devices(user_id: str = Cookie(alias="session_user_id")):
    """List user's available Spotify devices.
    
    Args:
        user_id: User ID from session
        
    Returns:
        List of devices
    """
    user_id = get_user_id(user_id)
    try:
        return await devices.get_devices(user_id)
    except SpotifyAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.get("/now-playing")
async def now_playing(user_id: str = Cookie(alias="session_user_id")):
    """Get currently playing track.
    
    Args:
        user_id: User ID from session
        
    Returns:
        Current playback state or null
    """
    user_id = get_user_id(user_id)
    try:
        state = await playback.get_current_playback(user_id)
        if state:
            return state.model_dump()
        return None
    except SpotifyAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.post("/play")
async def play_music(
    query: str | None = Query(default=None),
    track_uri: str | None = Query(default=None),
    device_id: str | None = Query(default=None),
    user_id: str = Cookie(alias="session_user_id"),
):
    """Start playback.
    
    Args:
        query: Search query for track
        track_uri: Spotify URI to play directly
        device_id: Target device ID
        user_id: User ID from session
        
    Returns:
        Success message
    """
    user_id = get_user_id(user_id)
    
    try:
        # If query provided, search for track first
        if query and not track_uri:
            tracks = await search.search_tracks(user_id, query, limit=1)
            if not tracks:
                raise HTTPException(status_code=404, detail="No tracks found")
            track_uri = tracks[0].uri
        
        # Start playback
        await playback.play(user_id, track_uri=track_uri, device_id=device_id)
        
        return {"message": "Playback started", "track_uri": track_uri}
    
    except NoActiveDeviceError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SpotifyAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.post("/pause")
async def pause_playback(
    device_id: str | None = Query(default=None),
    user_id: str = Cookie(alias="session_user_id"),
):
    """Pause playback.
    
    Args:
        device_id: Target device ID
        user_id: User ID from session
        
    Returns:
        Success message
    """
    user_id = get_user_id(user_id)
    
    try:
        await playback.pause(user_id, device_id=device_id)
        return {"message": "Playback paused"}
    except SpotifyAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.post("/resume")
async def resume_playback(
    device_id: str | None = Query(default=None),
    user_id: str = Cookie(alias="session_user_id"),
):
    """Resume playback.
    
    Args:
        device_id: Target device ID
        user_id: User ID from session
        
    Returns:
        Success message
    """
    user_id = get_user_id(user_id)
    
    try:
        await playback.resume(user_id, device_id=device_id)
        return {"message": "Playback resumed"}
    except NoActiveDeviceError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SpotifyAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.post("/next")
async def next_track(
    device_id: str | None = Query(default=None),
    user_id: str = Cookie(alias="session_user_id"),
):
    """Skip to next track.
    
    Args:
        device_id: Target device ID
        user_id: User ID from session
        
    Returns:
        Success message
    """
    user_id = get_user_id(user_id)
    
    try:
        await playback.skip_next(user_id, device_id=device_id)
        return {"message": "Skipped to next track"}
    except SpotifyAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.post("/previous")
async def previous_track(
    device_id: str | None = Query(default=None),
    user_id: str = Cookie(alias="session_user_id"),
):
    """Skip to previous track.
    
    Args:
        device_id: Target device ID
        user_id: User ID from session
        
    Returns:
        Success message
    """
    user_id = get_user_id(user_id)
    
    try:
        await playback.skip_previous(user_id, device_id=device_id)
        return {"message": "Skipped to previous track"}
    except SpotifyAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.post("/queue")
async def queue_track(
    query: str | None = Query(default=None),
    track_uri: str | None = Query(default=None),
    device_id: str | None = Query(default=None),
    user_id: str = Cookie(alias="session_user_id"),
):
    """Add track to queue.
    
    Args:
        query: Search query for track
        track_uri: Spotify URI to queue directly
        device_id: Target device ID
        user_id: User ID from session
        
    Returns:
        Success message
    """
    user_id = get_user_id(user_id)
    
    try:
        # If query provided, search for track first
        if query and not track_uri:
            tracks = await search.search_tracks(user_id, query, limit=1)
            if not tracks:
                raise HTTPException(status_code=404, detail="No tracks found")
            track_uri = tracks[0].uri
        
        if not track_uri:
            raise HTTPException(status_code=400, detail="Either query or track_uri required")
        
        # Add to queue
        await playback.add_to_queue(user_id, track_uri, device_id=device_id)
        
        return {"message": "Track added to queue", "track_uri": track_uri}
    
    except SpotifyAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.get("/search/tracks", response_model=list[Track])
async def search_tracks_endpoint(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=50),
    user_id: str = Cookie(alias="session_user_id"),
):
    """Search for tracks.
    
    Args:
        q: Search query
        limit: Maximum results
        user_id: User ID from session
        
    Returns:
        List of tracks
    """
    user_id = get_user_id(user_id)
    
    try:
        return await search.search_tracks(user_id, q, limit=limit)
    except SpotifyAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))
