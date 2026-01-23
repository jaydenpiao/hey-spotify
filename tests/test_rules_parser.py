"""Tests for rule-based intent parser."""
import pytest
from services.intent.rules import parse_command, extract_query_type
from services.intent.schema import IntentType, QueryType


def test_parse_play_command():
    """Test parsing play commands."""
    intent = parse_command("play bohemian rhapsody")
    assert intent.intent == IntentType.PLAY
    assert intent.args.query == "bohemian rhapsody"
    assert intent.confidence == 1.0


def test_parse_play_variations():
    """Test variations of play command."""
    commands = [
        "play some jazz",
        "start playing upbeat music",
        "put on taylor swift",
    ]
    
    for cmd in commands:
        intent = parse_command(cmd)
        assert intent.intent == IntentType.PLAY
        assert intent.args.query is not None


def test_parse_pause():
    """Test parsing pause commands."""
    for cmd in ["pause", "stop"]:
        intent = parse_command(cmd)
        assert intent.intent == IntentType.PAUSE
        assert intent.args.query is None


def test_parse_resume():
    """Test parsing resume commands."""
    for cmd in ["resume", "continue", "unpause"]:
        intent = parse_command(cmd)
        assert intent.intent == IntentType.RESUME


def test_parse_skip_next():
    """Test parsing skip next commands."""
    for cmd in ["next", "skip", "skip next"]:
        intent = parse_command(cmd)
        assert intent.intent == IntentType.SKIP_NEXT


def test_parse_skip_previous():
    """Test parsing skip previous commands."""
    for cmd in ["previous", "back", "skip previous"]:
        intent = parse_command(cmd)
        assert intent.intent == IntentType.SKIP_PREV


def test_parse_queue():
    """Test parsing queue commands."""
    intent = parse_command("queue dancing queen")
    assert intent.intent == IntentType.QUEUE
    assert intent.args.query == "dancing queen"
    
    intent = parse_command("add to queue bohemian rhapsody")
    assert intent.intent == IntentType.QUEUE
    assert intent.args.query == "bohemian rhapsody"


def test_parse_devices():
    """Test parsing device commands."""
    for cmd in ["devices", "list devices", "show devices"]:
        intent = parse_command(cmd)
        assert intent.intent == IntentType.GET_DEVICES


def test_parse_now_playing():
    """Test parsing now playing commands."""
    for cmd in ["now playing", "what's playing", "current song"]:
        intent = parse_command(cmd)
        assert intent.intent == IntentType.GET_NOW_PLAYING


def test_parse_search():
    """Test parsing search commands."""
    intent = parse_command("search taylor swift")
    assert intent.intent == IntentType.SEARCH
    assert intent.args.query == "taylor swift"
    
    intent = parse_command("find kanye west")
    assert intent.intent == IntentType.SEARCH


def test_parse_volume():
    """Test parsing volume commands."""
    intent = parse_command("volume 50")
    assert intent.intent == IntentType.SET_VOLUME
    assert intent.args.volume_percent == 50
    
    intent = parse_command("set volume to 75")
    assert intent.intent == IntentType.SET_VOLUME
    assert intent.args.volume_percent == 75


def test_parse_unknown_command():
    """Test parsing unknown commands."""
    intent = parse_command("do something weird")
    assert intent.intent == IntentType.UNKNOWN
    assert intent.confidence == 0.0


def test_case_insensitive():
    """Test that parsing is case insensitive."""
    commands = [
        "PLAY test",
        "Play test",
        "pLaY test",
    ]
    
    for cmd in commands:
        intent = parse_command(cmd)
        assert intent.intent == IntentType.PLAY


def test_whitespace_handling():
    """Test handling of extra whitespace."""
    intent = parse_command("  play   test song  ")
    assert intent.intent == IntentType.PLAY
    assert intent.args.query == "test song"


def test_extract_query_type():
    """Test query type extraction."""
    assert extract_query_type("playlist summer vibes") == QueryType.PLAYLIST
    assert extract_query_type("album thriller") == QueryType.ALBUM
    assert extract_query_type("song by taylor swift") == QueryType.ARTIST
    assert extract_query_type("track bohemian rhapsody") == QueryType.TRACK
    assert extract_query_type("kanye west") == QueryType.MIXED
