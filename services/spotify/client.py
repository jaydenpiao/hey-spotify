"""Spotify Web API client with retries and rate limiting."""
import asyncio
from typing import Any
import httpx

from core.config import settings
from core.errors import SpotifyAPIError, RateLimitError, InvalidTokenError
from core.logging import get_logger
from core.rate_limit import calculate_backoff
from services.auth.token_store import get_token, refresh_access_token, is_token_expired

logger = get_logger(__name__)


class SpotifyClient:
    """HTTP client for Spotify Web API with automatic retries and rate limiting."""
    
    def __init__(self, user_id: str):
        """Initialize Spotify client for a user.
        
        Args:
            user_id: User ID
        """
        self.user_id = user_id
        self.base_url = settings.spotify_api_base_url
        self._client = httpx.AsyncClient(timeout=10.0)
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._client.aclose()
    
    async def _get_access_token(self) -> str:
        """Get valid access token (refreshing if needed).
        
        Returns:
            Access token
            
        Raises:
            InvalidTokenError: If token cannot be retrieved
        """
        # Check if token needs refresh
        if await is_token_expired(self.user_id):
            logger.info(f"Token expired for user {self.user_id}, refreshing...")
            token = await refresh_access_token(self.user_id)
        else:
            token = await get_token(self.user_id)
        
        if not token:
            raise InvalidTokenError("No token available for user")
        
        return token.access_token
    
    async def request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        max_retries: int = 3,
    ) -> dict[str, Any] | None:
        """Make request to Spotify API with retries and rate limiting.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., '/me/player/devices')
            params: Query parameters
            json: JSON body
            max_retries: Maximum retry attempts for 5xx errors
            
        Returns:
            Response JSON or None for 204 responses
            
        Raises:
            SpotifyAPIError: For non-retryable errors
            RateLimitError: If rate limited after retries
        """
        url = f"{self.base_url}{endpoint}"
        attempt = 0
        
        while attempt <= max_retries:
            try:
                # Get fresh token
                access_token = await self._get_access_token()
                
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                }
                
                # Make request
                start_time = asyncio.get_event_loop().time()
                response = await self._client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json,
                    headers=headers,
                )
                latency_ms = (asyncio.get_event_loop().time() - start_time) * 1000
                
                # Log request
                logger.info(
                    f"Spotify API: {method} {endpoint} -> {response.status_code}",
                    extra={
                        "method": method,
                        "endpoint": endpoint,
                        "status_code": response.status_code,
                        "latency_ms": round(latency_ms, 2),
                    }
                )
                
                # Handle 401 - token might be invalid, try refresh once
                if response.status_code == 401 and attempt == 0:
                    logger.warning("Got 401, forcing token refresh...")
                    await refresh_access_token(self.user_id)
                    attempt += 1
                    continue
                
                # Handle 429 - rate limited
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 1))
                    logger.warning(
                        f"Rate limited by Spotify. Retry after {retry_after}s",
                        extra={"retry_after": retry_after}
                    )
                    
                    if attempt < max_retries:
                        await asyncio.sleep(retry_after)
                        attempt += 1
                        continue
                    else:
                        raise RateLimitError(retry_after=retry_after)
                
                # Handle 5xx - server errors (retry with backoff)
                if 500 <= response.status_code < 600:
                    if attempt < max_retries:
                        delay = calculate_backoff(attempt)
                        logger.warning(
                            f"Server error {response.status_code}, retrying in {delay:.2f}s...",
                            extra={"attempt": attempt + 1, "delay_seconds": delay}
                        )
                        await asyncio.sleep(delay)
                        attempt += 1
                        continue
                    else:
                        raise SpotifyAPIError(
                            f"Server error after {max_retries} retries: {response.text}",
                            status_code=response.status_code
                        )
                
                # Handle other errors
                if response.status_code >= 400:
                    error_msg = response.text
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("error", {}).get("message", error_msg)
                    except:
                        pass
                    
                    raise SpotifyAPIError(
                        f"Spotify API error: {error_msg}",
                        status_code=response.status_code
                    )
                
                # Success - return JSON or None for 204 / empty body
                if response.status_code == 204 or not response.content:
                    return None
                
                # Try to parse JSON, handle empty responses gracefully
                try:
                    return response.json()
                except ValueError:
                    # Response claims to have content but isn't valid JSON
                    logger.warning(
                        f"Response has content but isn't valid JSON: {response.text[:100]}",
                        extra={"status_code": response.status_code}
                    )
                    return None
            
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                if attempt < max_retries:
                    delay = calculate_backoff(attempt)
                    logger.warning(
                        f"Network error: {e}. Retrying in {delay:.2f}s...",
                        extra={"attempt": attempt + 1, "delay_seconds": delay}
                    )
                    await asyncio.sleep(delay)
                    attempt += 1
                else:
                    raise SpotifyAPIError(f"Network error after {max_retries} retries: {e}")
            
            except (SpotifyAPIError, RateLimitError, InvalidTokenError):
                # Don't retry these
                raise
        
        # Should not reach here
        raise SpotifyAPIError("Max retries exceeded")
    
    async def get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
        """GET request to Spotify API.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            Response JSON
        """
        return await self.request("GET", endpoint, params=params)
    
    async def post(
        self,
        endpoint: str,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        """POST request to Spotify API.
        
        Args:
            endpoint: API endpoint
            json: JSON body
            params: Query parameters
            
        Returns:
            Response JSON or None
        """
        return await self.request("POST", endpoint, json=json, params=params)
    
    async def put(
        self,
        endpoint: str,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        """PUT request to Spotify API.
        
        Args:
            endpoint: API endpoint
            json: JSON body
            params: Query parameters
            
        Returns:
            Response JSON or None
        """
        return await self.request("PUT", endpoint, json=json, params=params)
    
    async def delete(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
        """DELETE request to Spotify API.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            Response JSON or None
        """
        return await self.request("DELETE", endpoint, params=params)
