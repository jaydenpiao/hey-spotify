"""Spotify OAuth 2.0 flow implementation."""
import secrets
from urllib.parse import urlencode
from datetime import datetime, timedelta
import httpx

from core.config import settings
from core.errors import AuthError
from core.logging import get_logger
from storage.models import Token, User
from services.auth.pkce import generate_pkce_pair
from services.auth.token_store import (
    save_oauth_session,
    get_oauth_session,
    delete_oauth_session,
    save_user,
    save_token,
)

logger = get_logger(__name__)

# Spotify OAuth scopes needed for our app
SPOTIFY_SCOPES = [
    "user-read-email",
    "user-read-private",
    "user-read-playback-state",
    "user-modify-playback-state",
    "user-read-currently-playing",
]


def generate_authorization_url() -> tuple[str, str]:
    """Generate Spotify authorization URL with PKCE.
    
    Returns:
        Tuple of (authorization_url, state)
    """
    # Generate PKCE pair
    code_verifier, code_challenge = generate_pkce_pair()
    
    # Generate random state
    state = secrets.token_urlsafe(32)
    
    # Build authorization URL
    params = {
        "client_id": settings.spotify_client_id,
        "response_type": "code",
        "redirect_uri": settings.spotify_redirect_uri,
        "code_challenge_method": "S256",
        "code_challenge": code_challenge,
        "state": state,
        "scope": " ".join(SPOTIFY_SCOPES),
    }
    
    auth_url = f"{settings.spotify_accounts_base_url}/authorize?{urlencode(params)}"
    
    # Store session for verification (this is async, but we'll handle it in the endpoint)
    # For now, return the state so the caller can store it
    return auth_url, state, code_verifier


async def exchange_code_for_token(code: str, state: str) -> tuple[User, Token]:
    """Exchange authorization code for access token.
    
    Args:
        code: Authorization code from Spotify
        state: State parameter for verification
        
    Returns:
        Tuple of (User, Token)
        
    Raises:
        AuthError: If exchange fails
    """
    # Verify state and get code verifier
    session = await get_oauth_session(state)
    if not session:
        raise AuthError("Invalid or expired OAuth state")
    
    code_verifier = session.code_verifier
    
    # Exchange code for token
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.spotify_accounts_base_url}/api/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.spotify_redirect_uri,
                "client_id": settings.spotify_client_id,
                "client_secret": settings.spotify_client_secret,
                "code_verifier": code_verifier,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        
        if response.status_code != 200:
            logger.error(f"Token exchange failed: {response.text}")
            raise AuthError(f"Failed to exchange code for token: {response.text}")
        
        token_data = response.json()
    
    # Get user info
    async with httpx.AsyncClient() as client:
        user_response = await client.get(
            f"{settings.spotify_api_base_url}/me",
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
        )
        
        if user_response.status_code != 200:
            logger.error(f"Failed to get user info: {user_response.text}")
            raise AuthError("Failed to get user information")
        
        user_data = user_response.json()
    
    # Create user and token models
    user = User(
        id=user_data["id"],
        email=user_data.get("email"),
        display_name=user_data.get("display_name"),
    )
    
    token = Token(
        user_id=user.id,
        access_token=token_data["access_token"],
        refresh_token=token_data["refresh_token"],
        token_type=token_data.get("token_type", "Bearer"),
        expires_at=datetime.utcnow() + timedelta(seconds=token_data["expires_in"]),
        scope=token_data.get("scope"),
    )
    
    # Save to database
    await save_user(user)
    await save_token(token)
    
    # Clean up OAuth session
    await delete_oauth_session(state)
    
    logger.info(f"User {user.id} authenticated successfully")
    
    return user, token
