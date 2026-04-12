"""Shared OpenAI dependency status with short-lived caching."""
import time
from dataclasses import dataclass
from typing import Literal

from openai import (
    APIConnectionError,
    APIError,
    APIStatusError,
    APITimeoutError,
    AsyncOpenAI,
    AuthenticationError,
    PermissionDeniedError,
)

from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)

OpenAIStatusValue = Literal["ok", "missing", "invalid_auth", "probe_error"]
CACHE_TTL_SECONDS = 60.0

STATUS_REASONS: dict[OpenAIStatusValue, str | None] = {
    "ok": None,
    "missing": "OpenAI API key is not configured.",
    "invalid_auth": "OpenAI credentials are invalid.",
    "probe_error": "OpenAI service is temporarily unavailable.",
}

STATUS_ERROR_CODES: dict[OpenAIStatusValue, str | None] = {
    "ok": None,
    "missing": "openai_missing_config",
    "invalid_auth": "openai_invalid_auth",
    "probe_error": "openai_probe_error",
}

VOICE_DETAILS: dict[OpenAIStatusValue, str | None] = {
    "ok": None,
    "missing": "Voice input unavailable: OPENAI_API_KEY is not configured.",
    "invalid_auth": "Voice input unavailable: OpenAI credentials are invalid.",
    "probe_error": "Voice input unavailable: OpenAI service is temporarily unavailable.",
}

WAKE_DETAILS: dict[OpenAIStatusValue, str | None] = {
    "ok": None,
    "missing": "Wake word unavailable: OPENAI_API_KEY is not configured.",
    "invalid_auth": "Wake word unavailable: OpenAI credentials are invalid.",
    "probe_error": "Wake word unavailable: OpenAI service is temporarily unavailable.",
}


@dataclass(frozen=True)
class OpenAIDependencyStatus:
    """Cached OpenAI dependency state."""

    status: OpenAIStatusValue
    reason: str | None
    checked_at: float


_cached_status: OpenAIDependencyStatus | None = None
_cache_expires_at: float = 0.0
_last_logged_status: OpenAIStatusValue | None = None


def _build_status(status: OpenAIStatusValue) -> OpenAIDependencyStatus:
    """Create a status payload."""
    return OpenAIDependencyStatus(
        status=status,
        reason=STATUS_REASONS[status],
        checked_at=time.time(),
    )


def _cache_status(status: OpenAIStatusValue) -> OpenAIDependencyStatus:
    """Persist and log a dependency status transition."""
    global _cached_status, _cache_expires_at, _last_logged_status

    cached = _build_status(status)
    _cached_status = cached
    _cache_expires_at = time.monotonic() + CACHE_TTL_SECONDS

    if _last_logged_status != status:
        log = logger.info if status == "ok" else logger.warning
        extra = {
            "dependency": "openai",
            "openai_status": status,
        }
        error_code = STATUS_ERROR_CODES[status]
        if error_code:
            extra["error_code"] = error_code
        log("OpenAI dependency status changed", extra=extra)
        _last_logged_status = status

    return cached


async def get_openai_dependency_status(
    force_refresh: bool = False,
) -> OpenAIDependencyStatus:
    """Return cached OpenAI dependency health, probing if needed."""
    if not settings.openai_api_key:
        return _cache_status("missing")

    if (
        not force_refresh
        and _cached_status is not None
        and time.monotonic() < _cache_expires_at
    ):
        return _cached_status

    client = AsyncOpenAI(api_key=settings.openai_api_key)

    try:
        await client.models.list()
    except (AuthenticationError, PermissionDeniedError):
        return _cache_status("invalid_auth")
    except (APIConnectionError, APITimeoutError, APIStatusError, APIError):
        return _cache_status("probe_error")
    except Exception:
        return _cache_status("probe_error")

    return _cache_status("ok")


def update_openai_dependency_status(
    status: OpenAIStatusValue,
) -> OpenAIDependencyStatus:
    """Immediately update the cached OpenAI dependency state."""
    return _cache_status(status)


def get_openai_error_code(status: OpenAIStatusValue) -> str | None:
    """Return the stable error code for a dependency status."""
    return STATUS_ERROR_CODES[status]


def get_voice_unavailable_detail(status: OpenAIStatusValue) -> str:
    """Return the user-facing voice unavailability reason."""
    detail = VOICE_DETAILS[status]
    if detail is None:
        raise ValueError("Voice detail requested for healthy OpenAI status")
    return detail


def get_wake_unavailable_detail(status: OpenAIStatusValue) -> str:
    """Return the user-facing wake-word unavailability reason."""
    detail = WAKE_DETAILS[status]
    if detail is None:
        raise ValueError("Wake detail requested for healthy OpenAI status")
    return detail


def reset_openai_dependency_status_cache() -> None:
    """Reset the in-memory dependency cache (primarily for tests)."""
    global _cached_status, _cache_expires_at, _last_logged_status
    _cached_status = None
    _cache_expires_at = 0.0
    _last_logged_status = None
