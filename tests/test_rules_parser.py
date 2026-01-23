"""Tests for rule-based intent parser."""
import pytest
from services.intent.rules import parse_command, extract_query_type, normalize_transcript
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


def test_normalize_transcript():
    """Test transcript normalization."""
    assert normalize_transcript("Pause.") == "pause"
    assert normalize_transcript("Now playing?") == "now playing"
    assert normalize_transcript("Devices!") == "devices"
    assert normalize_transcript("Play... something") == "play something"
    assert normalize_transcript("RESUME") == "resume"
    assert normalize_transcript("  pause  ") == "pause"
    assert normalize_transcript("What's playing?!") == "whats playing"


def test_parse_with_punctuation():
    """Test parsing commands with punctuation (from voice)."""
    # These should now work with punctuation
    assert parse_command("Pause.").intent == IntentType.PAUSE
    assert parse_command("Devices!").intent == IntentType.GET_DEVICES
    assert parse_command("Now playing?").intent == IntentType.GET_NOW_PLAYING
    assert parse_command("Resume.").intent == IntentType.RESUME
    
    intent = parse_command("Play kanye west.")
    assert intent.intent == IntentType.PLAY
    assert "kanye west" in intent.args.query.lower()


def test_parse_with_varied_capitalization():
    """Test that capitalization doesn't matter."""
    assert parse_command("PAUSE").intent == IntentType.PAUSE
    assert parse_command("Pause").intent == IntentType.PAUSE
    assert parse_command("PaUsE").intent == IntentType.PAUSE
