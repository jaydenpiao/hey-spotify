"""Authentication endpoints."""
from fastapi import APIRouter, HTTPException, Response, Cookie
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from core.errors import AuthError
from core.logging import get_logger
from services.auth.spotify_oauth import generate_authorization_url, exchange_code_for_token
from services.auth.token_store import get_user, save_oauth_session

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


class AuthResponse(BaseModel):
    """Authentication response."""
    user_id: str
    email: str | None
    display_name: str | None


@router.get("/login")
async def login():
    """Initiate Spotify OAuth login flow.
    
    Redirects user to Spotify authorization page.
    """
    auth_url, state, code_verifier = generate_authorization_url()
    
    # Save OAuth session
    await save_oauth_session(state, code_verifier)
    
    logger.info("OAuth login initiated", extra={"state": state})
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def callback(code: str | None = None, state: str | None = None, error: str | None = None):
    """Handle OAuth callback from Spotify.
    
    Args:
        code: Authorization code
        state: State parameter for verification
        error: Error from Spotify (if any)
        
    Returns:
        Redirect to home page with session cookie
    """
    if error:
        logger.error(f"OAuth error: {error}")
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
    
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state parameter")
    
    try:
        user, token = await exchange_code_for_token(code, state)
    except AuthError as e:
        logger.error(f"Token exchange failed: {e}")
        raise HTTPException(status_code=401, detail=str(e))
    
    # Create response with session cookie
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key="session_user_id",
        value=user.id,
        httponly=True,
        max_age=3600 * 24 * 30,  # 30 days
        samesite="lax",
    )
    
    return response


@router.get("/me", response_model=AuthResponse)
async def get_current_user(session_user_id: str | None = Cookie(default=None)):
    """Get current authenticated user.
    
    Args:
        session_user_id: User ID from session cookie
        
    Returns:
        User information
    """
    if not session_user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = await get_user(session_user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return AuthResponse(
        user_id=user.id,
        email=user.email,
        display_name=user.display_name,
    )


@router.post("/logout")
async def logout():
    """Logout current user.
    
    Returns:
        Response clearing session cookie
    """
    response = Response(content='{"message": "Logged out successfully"}')
    response.delete_cookie(key="session_user_id")
    return response
