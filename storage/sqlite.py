"""SQLite database connection and initialization."""
import aiosqlite
from pathlib import Path

from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)

_db_connection = None


async def get_db() -> aiosqlite.Connection:
    """Get database connection (creates if needed).
    
    Returns:
        Database connection
    """
    global _db_connection
    if _db_connection is None:
        db_path = Path(settings.database_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        _db_connection = await aiosqlite.connect(str(db_path))
        _db_connection.row_factory = aiosqlite.Row
    return _db_connection


async def init_database():
    """Initialize database schema."""
    db = await get_db()
    
    # Create users table
    await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE,
            display_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create tokens table
    await db.execute("""
        CREATE TABLE IF NOT EXISTS tokens (
            user_id TEXT PRIMARY KEY,
            access_token TEXT NOT NULL,
            refresh_token TEXT NOT NULL,
            token_type TEXT DEFAULT 'Bearer',
            expires_at TIMESTAMP NOT NULL,
            scope TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Create sessions table for OAuth state
    await db.execute("""
        CREATE TABLE IF NOT EXISTS oauth_sessions (
            state TEXT PRIMARY KEY,
            code_verifier TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    await db.commit()
    logger.info("Database schema initialized")


async def close_db():
    """Close database connection."""
    global _db_connection
    if _db_connection:
        await _db_connection.close()
        _db_connection = None
