"""Custom exception classes for the application."""


class HeySpotifyError(Exception):
    """Base exception for all application errors."""
    pass


class AuthError(HeySpotifyError):
    """Authentication or authorization error."""
    pass


class SpotifyAPIError(HeySpotifyError):
    """Error calling Spotify API."""
    
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class RateLimitError(SpotifyAPIError):
    """Spotify API rate limit exceeded."""
    
    def __init__(self, retry_after: int | None = None):
        message = f"Rate limit exceeded. Retry after {retry_after}s" if retry_after else "Rate limit exceeded"
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


class NoActiveDeviceError(SpotifyAPIError):
    """No active Spotify device found."""
    
    def __init__(self):
        super().__init__("No active device found. Please open Spotify and start playing something.", status_code=404)


class IntentParseError(HeySpotifyError):
    """Failed to parse user intent from command."""
    pass


class OpenAIDependencyError(HeySpotifyError):
    """OpenAI-backed functionality is unavailable."""

    def __init__(self, detail: str, error_code: str, status: str):
        super().__init__(detail)
        self.detail = detail
        self.error_code = error_code
        self.status = status


class InvalidTokenError(AuthError):
    """Token is invalid or expired."""
    pass
