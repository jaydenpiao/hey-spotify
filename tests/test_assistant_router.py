"""Tests for assistant capability reporting."""
import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("SPOTIFY_CLIENT_ID", "test-client-id")
os.environ.setdefault("SPOTIFY_CLIENT_SECRET", "test-client-secret")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault(
    "DATABASE_PATH",
    str(Path(tempfile.gettempdir()) / "hey_spotify_test.db"),
)

from apps.api.main import app
from apps.api.routers import assistant as assistant_router
from services.openai_status import OpenAIDependencyStatus


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def authenticate_client(client):
    """Set the session cookie used by authenticated routes."""
    client.cookies.set("session_user_id", "user-123")


def make_status(status: str) -> OpenAIDependencyStatus:
    """Construct an OpenAI dependency status payload for tests."""
    reasons = {
        "ok": None,
        "missing": "OpenAI API key is not configured.",
        "invalid_auth": "OpenAI credentials are invalid.",
        "probe_error": "OpenAI service is temporarily unavailable.",
    }
    return OpenAIDependencyStatus(status=status, reason=reasons[status], checked_at=0.0)


def test_get_capabilities_success(client, monkeypatch):
    async def fake_status(force_refresh: bool = False):
        return make_status("ok")

    monkeypatch.setattr(assistant_router, "get_openai_dependency_status", fake_status)
    monkeypatch.setattr(assistant_router, "get_wake_server_availability", lambda: (True, None))
    monkeypatch.setattr(assistant_router.settings, "use_llm_intent_parser", True)
    authenticate_client(client)

    response = client.get("/assistant/capabilities")

    assert response.status_code == 200
    assert response.json() == {
        "text_command_mode": "llm",
        "voice_available": True,
        "voice_reason": None,
        "wake_server_available": True,
        "wake_server_reason": None,
        "openai_status": "ok",
    }


def test_get_capabilities_invalid_auth_disables_voice(client, monkeypatch):
    async def fake_status(force_refresh: bool = False):
        return make_status("invalid_auth")

    monkeypatch.setattr(assistant_router, "get_openai_dependency_status", fake_status)
    monkeypatch.setattr(assistant_router.settings, "use_llm_intent_parser", True)
    authenticate_client(client)

    response = client.get("/assistant/capabilities")

    assert response.status_code == 200
    assert response.json() == {
        "text_command_mode": "regex",
        "voice_available": False,
        "voice_reason": "Voice input unavailable: OpenAI credentials are invalid.",
        "wake_server_available": False,
        "wake_server_reason": "Wake word unavailable: OpenAI credentials are invalid.",
        "openai_status": "invalid_auth",
    }


def test_get_capabilities_wake_unavailable_when_openai_ok(client, monkeypatch):
    async def fake_status(force_refresh: bool = False):
        return make_status("ok")

    monkeypatch.setattr(assistant_router, "get_openai_dependency_status", fake_status)
    monkeypatch.setattr(
        assistant_router,
        "get_wake_server_availability",
        lambda: (False, "Wake word unavailable: PICOVOICE_ACCESS_KEY is not configured."),
    )
    monkeypatch.setattr(assistant_router.settings, "use_llm_intent_parser", True)
    authenticate_client(client)

    response = client.get("/assistant/capabilities")

    assert response.status_code == 200
    assert response.json() == {
        "text_command_mode": "llm",
        "voice_available": True,
        "voice_reason": None,
        "wake_server_available": False,
        "wake_server_reason": "Wake word unavailable: PICOVOICE_ACCESS_KEY is not configured.",
        "openai_status": "ok",
    }


def test_get_capabilities_requires_authentication(client):
    response = client.get("/assistant/capabilities")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
