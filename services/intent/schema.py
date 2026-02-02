"""Intent schema definitions."""
from enum import Enum
from pydantic import BaseModel, Field


class IntentType(str, Enum):
    """Supported intent types."""
    GET_DEVICES = "GET_DEVICES"
    GET_NOW_PLAYING = "GET_NOW_PLAYING"
    PLAY = "PLAY"
    PAUSE = "PAUSE"
    RESUME = "RESUME"
    SKIP_NEXT = "SKIP_NEXT"
    SKIP_PREV = "SKIP_PREV"
    SET_VOLUME = "SET_VOLUME"
    QUEUE = "QUEUE"
    TRANSFER_PLAYBACK = "TRANSFER_PLAYBACK"
    SEARCH = "SEARCH"
    UNKNOWN = "UNKNOWN"


class QueryType(str, Enum):
    """Query type for search/play."""
    TRACK = "track"
    ARTIST = "artist"
    PLAYLIST = "playlist"
    ALBUM = "album"
    MIXED = "mixed"


class IntentArgs(BaseModel):
    """Arguments for intent execution."""
    query: str | None = None
    query_type: QueryType | None = QueryType.MIXED  # Made optional to match JSON schema
    device_id: str | None = None
    volume_percent: int | None = Field(None, ge=0, le=100)
    track_uri: str | None = None


class Intent(BaseModel):
    """Parsed user intent."""
    intent: IntentType
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    args: IntentArgs = Field(default_factory=IntentArgs)
    needs_disambiguation: bool = False
    candidates: list[dict] = Field(default_factory=list)
    raw_command: str | None = None


class IntentResponse(BaseModel):
    """Response after executing an intent."""
    success: bool
    message: str
    data: dict | None = None
