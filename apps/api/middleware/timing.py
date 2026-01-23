"""Timing middleware for performance monitoring."""
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from core.logging import get_logger

logger = get_logger(__name__)


class TimingMiddleware(BaseHTTPMiddleware):
    """Add Server-Timing headers and log request latency."""
    
    async def dispatch(self, request: Request, call_next):
        """Process request and measure timing.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler
            
        Returns:
            HTTP response with Server-Timing header
        """
        start_time = time.perf_counter()
        
        # Process request
        response: Response = await call_next(request)
        
        # Calculate latency
        latency_ms = (time.perf_counter() - start_time) * 1000
        
        # Add Server-Timing header
        response.headers["Server-Timing"] = f"total;dur={latency_ms:.2f}"
        
        # Log request with timing info
        request_id = getattr(request.state, "request_id", "unknown")
        logger.info(
            f"{request.method} {request.url.path} {response.status_code}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "latency_ms": round(latency_ms, 2),
            }
        )
        
        return response
