"""FastAPI application entry point."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from core.config import settings
from core.logging import setup_logging, get_logger
from apps.api.middleware.request_id import RequestIDMiddleware
from apps.api.middleware.timing import TimingMiddleware
from apps.api.routers import health, auth, spotify, assistant, voice
from storage.sqlite import init_database

# Setup logging
setup_logging(level="INFO")
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Hey Spotify API...")
    await init_database()
    logger.info("Database initialized")
    yield
    # Shutdown
    logger.info("Shutting down Hey Spotify API...")


# Create FastAPI app
app = FastAPI(
    title="Hey Spotify",
    description="Voice assistant for Spotify with OAuth PKCE and intelligent intent parsing",
    version="0.1.0",
    lifespan=lifespan,
)

# Add middleware (order matters - first added is outermost)
app.add_middleware(TimingMiddleware)
app.add_middleware(RequestIDMiddleware)

# Add routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(spotify.router)
app.include_router(assistant.router)
app.include_router(voice.router)

# Serve static files (web UI)
try:
    app.mount("/static", StaticFiles(directory="web"), name="static")
except RuntimeError:
    # Directory doesn't exist yet - that's ok
    pass


@app.get("/")
async def root():
    """Serve the web UI."""
    try:
        return FileResponse("web/index.html")
    except FileNotFoundError:
        return {
            "message": "Hey Spotify API",
            "status": "running",
            "docs": "/docs",
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "apps.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
