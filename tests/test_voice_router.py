"""Tests for wake word configuration endpoint."""
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
from apps.api.routers import voice as voice_router
from core.errors import OpenAIDependencyError
from services.voice import wake as wake_service


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def configure_wake_assets(monkeypatch, tmp_path, *, model_exists=True, keyword_exists=True):
    """Point the router to temporary wake word assets."""
    model_path = tmp_path / "porcupine_params.pv"
    keyword_path = tmp_path / "hey_spotify.ppn"

    if model_exists:
        model_path.write_bytes(b"model")
    if keyword_exists:
        keyword_path.write_bytes(b"keyword")

    monkeypatch.setattr(voice_router, "WAKE_MODEL_FILE", model_path)
    monkeypatch.setattr(voice_router, "WAKE_KEYWORD_FILE", keyword_path)
    monkeypatch.setattr(wake_service, "WAKE_MODEL_FILE", model_path)
    monkeypatch.setattr(wake_service, "WAKE_KEYWORD_FILE", keyword_path)


def authenticate_client(client):
    """Set the session cookie used by authenticated routes."""
    client.cookies.set("session_user_id", "user-123")


def test_get_wake_config_success(client, monkeypatch, tmp_path):
    configure_wake_assets(monkeypatch, tmp_path)
    monkeypatch.setattr(voice_router.settings, "picovoice_access_key", "test-access-key")
    authenticate_client(client)

    response = client.get("/voice/wake-config")

    assert response.status_code == 200
    assert response.json() == {
        "access_key": "test-access-key",
        "keyword_path": "/static/keywords/hey_spotify.ppn",
        "model_path": "/static/models/porcupine_params.pv",
        "sensitivity": 0.65,
    }


def test_get_wake_config_requires_access_key(client, monkeypatch, tmp_path):
    configure_wake_assets(monkeypatch, tmp_path)
    monkeypatch.setattr(voice_router.settings, "picovoice_access_key", None)
    authenticate_client(client)

    response = client.get("/voice/wake-config")

    assert response.status_code == 400
    assert response.json()["detail"] == "PICOVOICE_ACCESS_KEY not configured"


def test_get_wake_config_requires_model_file(client, monkeypatch, tmp_path):
    configure_wake_assets(monkeypatch, tmp_path, model_exists=False)
    monkeypatch.setattr(voice_router.settings, "picovoice_access_key", "test-access-key")
    authenticate_client(client)

    response = client.get("/voice/wake-config")

    assert response.status_code == 400
    assert "Wake model not found" in response.json()["detail"]


def test_get_wake_config_requires_keyword_file(client, monkeypatch, tmp_path):
    configure_wake_assets(monkeypatch, tmp_path, keyword_exists=False)
    monkeypatch.setattr(voice_router.settings, "picovoice_access_key", "test-access-key")
    authenticate_client(client)

    response = client.get("/voice/wake-config")

    assert response.status_code == 400
    assert "Wake keyword not found" in response.json()["detail"]


def test_get_wake_config_requires_authentication(client, monkeypatch, tmp_path):
    configure_wake_assets(monkeypatch, tmp_path)
    monkeypatch.setattr(voice_router.settings, "picovoice_access_key", "test-access-key")

    response = client.get("/voice/wake-config")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_voice_command_invalid_openai_auth_returns_503(client, monkeypatch):
    class InvalidAuthWhisperClient:
        async def transcribe_audio(self, **kwargs):
            raise OpenAIDependencyError(
                detail="Voice input unavailable: OpenAI credentials are invalid.",
                error_code="openai_invalid_auth",
                status="invalid_auth",
            )

    monkeypatch.setattr(voice_router, "get_whisper_client", lambda: InvalidAuthWhisperClient())
    authenticate_client(client)

    response = client.post(
        "/voice/command",
        files={"audio": ("recording.webm", b"audio-bytes", "audio/webm")},
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Voice input unavailable: OpenAI credentials are invalid.",
        "error_code": "openai_invalid_auth",
    }


def test_transcribe_missing_openai_config_returns_503(client, monkeypatch):
    class MissingConfigWhisperClient:
        async def transcribe_audio(self, **kwargs):
            raise OpenAIDependencyError(
                detail="Voice input unavailable: OPENAI_API_KEY is not configured.",
                error_code="openai_missing_config",
                status="missing",
            )

    monkeypatch.setattr(voice_router, "get_whisper_client", lambda: MissingConfigWhisperClient())
    authenticate_client(client)

    response = client.post(
        "/voice/transcribe",
        files={"audio": ("recording.webm", b"audio-bytes", "audio/webm")},
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Voice input unavailable: OPENAI_API_KEY is not configured.",
        "error_code": "openai_missing_config",
    }
