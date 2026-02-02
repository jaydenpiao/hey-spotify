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
    
    # OpenAI (for Whisper and LLM intent parsing)
    openai_api_key: str | None = None
    
    # LLM Intent Parser (Milestone 2)
    use_llm_intent_parser: bool = True
    llm_model: str = "gpt-4o"  # gpt-4o is better for structured outputs (supports temperature=0)
    llm_temperature: float = 0.0
    llm_max_tokens: int = 150  # Uses max_completion_tokens for GPT-5.x, max_tokens for GPT-4.x
    
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
