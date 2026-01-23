"""Health check endpoints."""
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/healthz")
async def health_check():
    """Health check endpoint.
    
    Returns:
        Status OK
    """
    return {"status": "ok"}
