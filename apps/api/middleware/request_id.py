"""Request ID middleware for tracking requests."""
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add unique request ID to each request."""
    
    async def dispatch(self, request: Request, call_next):
        """Process request and add request ID.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler
            
        Returns:
            HTTP response with X-Request-Id header
        """
        # Generate or use existing request ID
        request_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))
        
        # Store in request state for access by handlers
        request.state.request_id = request_id
        
        # Process request
        response: Response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-Id"] = request_id
        
        return response
