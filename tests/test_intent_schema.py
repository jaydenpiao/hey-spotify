"""Tests for intent schema validation."""
import pytest
from pydantic import ValidationError
from services.intent.schema import (
    Intent,
    IntentType,
    IntentArgs,
    QueryType,
    IntentResponse,
)


def test_intent_basic():
    """Test basic intent creation."""
    intent = Intent(
        intent=IntentType.PLAY,
        args=IntentArgs(query="test song"),
    )
    
    assert intent.intent == IntentType.PLAY
    assert intent.args.query == "test song"
    assert intent.confidence == 1.0
    assert not intent.needs_disambiguation


def test_intent_with_all_fields():
    """Test intent with all fields."""
    intent = Intent(
        intent=IntentType.PLAY,
        confidence=0.95,
        args=IntentArgs(
            query="test query",
            query_type=QueryType.TRACK,
            device_id="device123",
        ),
        needs_disambiguation=True,
        candidates=[{"id": "1", "name": "Track 1"}],
        raw_command="play test query",
    )
    
    assert intent.intent == IntentType.PLAY
    assert intent.confidence == 0.95
    assert intent.args.query == "test query"
    assert intent.args.query_type == QueryType.TRACK
    assert intent.needs_disambiguation
    assert len(intent.candidates) == 1


def test_intent_args_volume_validation():
    """Test volume percent validation."""
    # Valid volume
    args = IntentArgs(volume_percent=50)
    assert args.volume_percent == 50
    
    # Edge cases
    args = IntentArgs(volume_percent=0)
    assert args.volume_percent == 0
    
    args = IntentArgs(volume_percent=100)
    assert args.volume_percent == 100
    
    # Invalid volumes should raise error
    with pytest.raises(ValidationError):
        IntentArgs(volume_percent=-1)
    
    with pytest.raises(ValidationError):
        IntentArgs(volume_percent=101)


def test_intent_response():
    """Test intent response model."""
    response = IntentResponse(
        success=True,
        message="Command executed successfully",
        data={"track_uri": "spotify:track:123"},
    )
    
    assert response.success
    assert "success" in response.message
    assert response.data["track_uri"] == "spotify:track:123"


def test_intent_response_minimal():
    """Test intent response with minimal fields."""
    response = IntentResponse(
        success=False,
        message="Error occurred",
    )
    
    assert not response.success
    assert response.data is None


def test_intent_types_enum():
    """Test intent type enum values."""
    assert IntentType.PLAY.value == "PLAY"
    assert IntentType.PAUSE.value == "PAUSE"
    assert IntentType.GET_DEVICES.value == "GET_DEVICES"
    
    # Should be able to create from string
    intent_type = IntentType("PLAY")
    assert intent_type == IntentType.PLAY


def test_query_types_enum():
    """Test query type enum values."""
    assert QueryType.TRACK.value == "track"
    assert QueryType.ARTIST.value == "artist"
    assert QueryType.MIXED.value == "mixed"
