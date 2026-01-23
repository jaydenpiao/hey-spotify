"""Database models."""
from datetime import datetime
from pydantic import BaseModel


class User(BaseModel):
    """User model."""
    id: str
    email: str | None = None
    display_name: str | None = None
    created_at: datetime | None = None


class Token(BaseModel):
    """Token model."""
    user_id: str
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_at: datetime
    scope: str | None = None
    updated_at: datetime | None = None


class OAuthSession(BaseModel):
    """OAuth session model."""
    state: str
    code_verifier: str
    created_at: datetime | None = None
