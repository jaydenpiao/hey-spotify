"""Application configuration management."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Spotify OAuth
    spotify_client_id: str
    spotify_client_secret: str
    spotify_redirect_uri: str = "http://127.0.0.1:8000/auth/callback"
    
    # Application
    secret_key: str
    database_path: str = "./hey_spotify.db"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Optional: OpenAI (for future LLM integration)
    openai_api_key: str | None = None
    
    # Spotify API
    spotify_api_base_url: str = "https://api.spotify.com/v1"
    spotify_accounts_base_url: str = "https://accounts.spotify.com"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


# Global settings instance
settings = Settings()
