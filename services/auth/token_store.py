"""Token storage and management."""
from datetime import datetime, timedelta
import httpx

from storage.sqlite import get_db
from storage.models import Token, User, OAuthSession
from core.config import settings
from core.errors import InvalidTokenError
from core.logging import get_logger

logger = get_logger(__name__)


async def save_oauth_session(state: str, code_verifier: str) -> None:
    """Save OAuth session for PKCE verification.
    
    Args:
        state: OAuth state parameter
        code_verifier: PKCE code verifier
    """
    db = await get_db()
    await db.execute(
        "INSERT OR REPLACE INTO oauth_sessions (state, code_verifier) VALUES (?, ?)",
        (state, code_verifier)
    )
    await db.commit()


async def get_oauth_session(state: str) -> OAuthSession | None:
    """Get OAuth session by state.
    
    Args:
        state: OAuth state parameter
        
    Returns:
        OAuth session or None if not found
    """
    db = await get_db()
    async with db.execute(
        "SELECT * FROM oauth_sessions WHERE state = ?",
        (state,)
    ) as cursor:
        row = await cursor.fetchone()
        if row:
            return OAuthSession(**dict(row))
    return None


async def delete_oauth_session(state: str) -> None:
    """Delete OAuth session after use.
    
    Args:
        state: OAuth state parameter
    """
    db = await get_db()
    await db.execute("DELETE FROM oauth_sessions WHERE state = ?", (state,))
    await db.commit()


async def save_user(user: User) -> None:
    """Save or update user.
    
    Args:
        user: User model
    """
    db = await get_db()
    await db.execute(
        """INSERT OR REPLACE INTO users (id, email, display_name)
           VALUES (?, ?, ?)""",
        (user.id, user.email, user.display_name)
    )
    await db.commit()


async def save_token(token: Token) -> None:
    """Save or update user token.
    
    Args:
        token: Token model
    """
    db = await get_db()
    await db.execute(
        """INSERT OR REPLACE INTO tokens 
           (user_id, access_token, refresh_token, token_type, expires_at, scope)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            token.user_id,
            token.access_token,
            token.refresh_token,
            token.token_type,
            token.expires_at.isoformat(),
            token.scope,
        )
    )
    await db.commit()
    logger.info(f"Token saved for user {token.user_id}")


async def get_token(user_id: str) -> Token | None:
    """Get token for user.
    
    Args:
        user_id: User ID
        
    Returns:
        Token or None if not found
    """
    db = await get_db()
    async with db.execute(
        "SELECT * FROM tokens WHERE user_id = ?",
        (user_id,)
    ) as cursor:
        row = await cursor.fetchone()
        if row:
            data = dict(row)
            # Parse datetime string
            data["expires_at"] = datetime.fromisoformat(data["expires_at"])
            if data.get("updated_at"):
                data["updated_at"] = datetime.fromisoformat(data["updated_at"])
            return Token(**data)
    return None


async def get_user(user_id: str) -> User | None:
    """Get user by ID.
    
    Args:
        user_id: User ID
        
    Returns:
        User or None if not found
    """
    db = await get_db()
    async with db.execute(
        "SELECT * FROM users WHERE id = ?",
        (user_id,)
    ) as cursor:
        row = await cursor.fetchone()
        if row:
            data = dict(row)
            if data.get("created_at"):
                data["created_at"] = datetime.fromisoformat(data["created_at"])
            return User(**data)
    return None


async def refresh_access_token(user_id: str) -> Token:
    """Refresh access token using refresh token.
    
    Args:
        user_id: User ID
        
    Returns:
        Updated token
        
    Raises:
        InvalidTokenError: If refresh fails
    """
    token = await get_token(user_id)
    if not token:
        raise InvalidTokenError("No token found for user")
    
    # Exchange refresh token for new access token
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.spotify_accounts_base_url}/api/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": token.refresh_token,
                "client_id": settings.spotify_client_id,
                "client_secret": settings.spotify_client_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        
        if response.status_code != 200:
            logger.error(f"Token refresh failed: {response.text}")
            raise InvalidTokenError("Failed to refresh token")
        
        data = response.json()
        
        # Update token
        new_token = Token(
            user_id=user_id,
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token", token.refresh_token),
            token_type=data.get("token_type", "Bearer"),
            expires_at=datetime.utcnow() + timedelta(seconds=data["expires_in"]),
            scope=data.get("scope"),
        )
        
        await save_token(new_token)
        logger.info(f"Token refreshed for user {user_id}")
        
        return new_token


async def is_token_expired(user_id: str) -> bool:
    """Check if token is expired.
    
    Args:
        user_id: User ID
        
    Returns:
        True if expired or not found
    """
    token = await get_token(user_id)
    if not token:
        return True
    
    # Add 5 minute buffer
    return datetime.utcnow() >= (token.expires_at - timedelta(minutes=5))
