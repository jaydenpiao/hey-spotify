"""Pydantic models for Spotify API responses."""
from pydantic import BaseModel


class Artist(BaseModel):
    """Spotify artist model."""
    id: str
    name: str
    uri: str


class Album(BaseModel):
    """Spotify album model."""
    id: str
    name: str
    uri: str
    images: list[dict] = []


class Track(BaseModel):
    """Spotify track model."""
    id: str
    name: str
    uri: str
    artists: list[Artist]
    album: Album
    duration_ms: int
    explicit: bool = False


class Device(BaseModel):
    """Spotify playback device model."""
    id: str | None
    name: str
    type: str
    is_active: bool
    is_private_session: bool
    is_restricted: bool
    volume_percent: int | None


class PlaybackState(BaseModel):
    """Spotify playback state model."""
    device: Device
    is_playing: bool
    progress_ms: int | None
    item: Track | None
    shuffle_state: bool
    repeat_state: str
    timestamp: int


class SearchResults(BaseModel):
    """Spotify search results model."""
    tracks: list[Track] = []
