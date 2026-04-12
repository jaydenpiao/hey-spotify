"""Tests for LLM intent compiler."""
import os

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")

from services.intent.llm_compiler import (
    compile_intent_with_llm,
    get_llm_compiler,
    LLMCompilerError,
    _load_examples,
    _build_system_prompt,
    INTENT_SCHEMA,
)
from services.intent.schema import Intent, IntentType, IntentArgs


def test_load_examples():
    """Test loading examples from YAML."""
    examples = _load_examples()
    
    # Should contain formatted examples
    assert len(examples) > 0
    assert "User:" in examples
    assert "Intent:" in examples


def test_build_system_prompt():
    """Test system prompt construction."""
    prompt = _build_system_prompt()
    
    # Should contain key instructions
    assert "Spotify voice assistant" in prompt
    assert "PLAY" in prompt
    assert "PAUSE" in prompt
    assert "Examples:" in prompt


@pytest.mark.asyncio
async def test_simple_commands():
    """Test simple command parsing."""
    # Mock OpenAI response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '{"intent": "PAUSE", "confidence": 1.0, "args": {}, "needs_disambiguation": false}'
    
    with patch('services.intent.llm_compiler.AsyncOpenAI') as mock_openai:
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_openai.return_value = mock_client
        
        # Force reinitialize compiler with mock
        import services.intent.llm_compiler as llm_module
        llm_module._llm_compiler = None
        
        intent = await compile_intent_with_llm("pause")
        
        assert intent.intent == IntentType.PAUSE
        assert intent.confidence == 1.0


@pytest.mark.asyncio
async def test_play_commands():
    """Test play command variations."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '{"intent": "PLAY", "confidence": 0.95, "args": {"query": "jazz music", "query_type": "mixed"}, "needs_disambiguation": false}'
    
    with patch('services.intent.llm_compiler.AsyncOpenAI') as mock_openai:
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_openai.return_value = mock_client
        
        import services.intent.llm_compiler as llm_module
        llm_module._llm_compiler = None
        
        intent = await compile_intent_with_llm("play some jazz music")
        
        assert intent.intent == IntentType.PLAY
        assert intent.args.query == "jazz music"


@pytest.mark.asyncio
async def test_natural_variations():
    """Test natural language variations."""
    test_cases = [
        ("could you pause please", "PAUSE"),
        ("please play something", "PLAY"),
        ("what's currently playing", "GET_NOW_PLAYING"),
    ]
    
    for command, expected_intent in test_cases:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = f'{{"intent": "{expected_intent}", "confidence": 0.9, "args": {{}}, "needs_disambiguation": false}}'
        
        with patch('services.intent.llm_compiler.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client
            
            import services.intent.llm_compiler as llm_module
            llm_module._llm_compiler = None
            
            intent = await compile_intent_with_llm(command)
            assert intent.intent == IntentType(expected_intent)


@pytest.mark.asyncio
async def test_complex_queries():
    """Test complex search queries."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '{"intent": "PLAY", "confidence": 0.8, "args": {"query": "upbeat indie 2000s", "query_type": "mixed"}, "needs_disambiguation": false}'
    
    with patch('services.intent.llm_compiler.AsyncOpenAI') as mock_openai:
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_openai.return_value = mock_client
        
        import services.intent.llm_compiler as llm_module
        llm_module._llm_compiler = None
        
        intent = await compile_intent_with_llm("play upbeat indie music from the 2000s")
        
        assert intent.intent == IntentType.PLAY
        assert "upbeat" in intent.args.query
        assert "indie" in intent.args.query


@pytest.mark.asyncio
async def test_punctuation_handling():
    """Test handling of punctuation in commands."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '{"intent": "PAUSE", "confidence": 1.0, "args": {}, "needs_disambiguation": false}'
    
    with patch('services.intent.llm_compiler.AsyncOpenAI') as mock_openai:
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_openai.return_value = mock_client
        
        import services.intent.llm_compiler as llm_module
        llm_module._llm_compiler = None
        
        # Should handle punctuation naturally
        intent = await compile_intent_with_llm("Pause.")
        assert intent.intent == IntentType.PAUSE


@pytest.mark.asyncio
async def test_empty_response_error():
    """Test handling of empty LLM response."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = None
    
    with patch('services.intent.llm_compiler.AsyncOpenAI') as mock_openai:
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_openai.return_value = mock_client
        
        import services.intent.llm_compiler as llm_module
        llm_module._llm_compiler = None
        
        with pytest.raises(LLMCompilerError, match="Empty response"):
            await compile_intent_with_llm("pause")


@pytest.mark.asyncio
async def test_invalid_json_error():
    """Test handling of invalid JSON from LLM."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "not valid json"
    
    with patch('services.intent.llm_compiler.AsyncOpenAI') as mock_openai:
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_openai.return_value = mock_client
        
        import services.intent.llm_compiler as llm_module
        llm_module._llm_compiler = None
        
        with pytest.raises(LLMCompilerError):
            await compile_intent_with_llm("pause")


@pytest.mark.asyncio
async def test_network_error():
    """Test handling of network errors."""
    with patch('services.intent.llm_compiler.AsyncOpenAI') as mock_openai:
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("Network error"))
        mock_openai.return_value = mock_client
        
        import services.intent.llm_compiler as llm_module
        llm_module._llm_compiler = None
        
        with pytest.raises(LLMCompilerError, match="Network error"):
            await compile_intent_with_llm("pause")


def test_no_api_key_error():
    """Test error when API key is not configured."""
    with patch('services.intent.llm_compiler.settings') as mock_settings:
        mock_settings.openai_api_key = None
        
        import services.intent.llm_compiler as llm_module
        llm_module._llm_compiler = None
        
        with pytest.raises(LLMCompilerError, match="API key not configured"):
            get_llm_compiler()


def test_schema_structure():
    """Verify JSON schema is valid for OpenAI strict mode."""
    schema = INTENT_SCHEMA["schema"]
    
    # Top level must have required
    assert "required" in schema
    assert isinstance(schema["required"], list)
    assert len(schema["required"]) > 0
    
    # Required fields must include intent, confidence, args, needs_disambiguation
    assert "intent" in schema["required"]
    assert "confidence" in schema["required"]
    assert "args" in schema["required"]
    assert "needs_disambiguation" in schema["required"]
    
    # Args must have required array
    args_props = schema["properties"]["args"]
    assert "required" in args_props
    assert isinstance(args_props["required"], list)
    
    # All args properties must be in required array (OpenAI strict mode requirement)
    args_properties = list(args_props["properties"].keys())
    assert set(args_props["required"]) == set(args_properties)
    
    # All args properties must be nullable for optional behavior
    for prop_name in args_properties:
        prop_schema = args_props["properties"][prop_name]
        if "type" in prop_schema:
            prop_type = prop_schema["type"]
            # Should be array with null
            assert isinstance(prop_type, list), f"{prop_name} should have array type"
            assert "null" in prop_type or None in prop_type, f"{prop_name} should be nullable"
