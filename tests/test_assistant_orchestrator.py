"""Tests for assistant orchestration behavior under dependency degradation."""
import pytest

from services.assistant import orchestrator
from services.intent.schema import Intent, IntentArgs, IntentResponse, IntentType
from services.openai_status import OpenAIDependencyStatus


@pytest.mark.asyncio
async def test_process_command_skips_llm_when_openai_unhealthy(monkeypatch):
    """Regex parsing should be used directly when OpenAI is already unhealthy."""

    async def fake_status(force_refresh: bool = False):
        return OpenAIDependencyStatus(
            status="invalid_auth",
            reason="OpenAI credentials are invalid.",
            checked_at=0.0,
        )

    def fake_parse_command(command: str):
        return Intent(
            intent=IntentType.PAUSE,
            confidence=1.0,
            args=IntentArgs(),
            raw_command=command,
        )

    async def fake_execute_intent(user_id: str, intent: Intent):
        return IntentResponse(success=True, message="Paused playback", data=None)

    async def fail_compile(command: str):
        raise AssertionError("LLM compiler should not be called while OpenAI is unhealthy")

    monkeypatch.setattr(orchestrator, "get_openai_dependency_status", fake_status)
    monkeypatch.setattr(orchestrator, "parse_command", fake_parse_command)
    monkeypatch.setattr(orchestrator, "execute_intent", fake_execute_intent)
    monkeypatch.setattr(orchestrator, "compile_intent_with_llm", fail_compile)
    monkeypatch.setattr(orchestrator.settings, "use_llm_intent_parser", True)

    response = await orchestrator.process_command("user-123", "pause")

    assert response.success is True
    assert response.message == "Paused playback"
