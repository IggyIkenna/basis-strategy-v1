"""Correlation ID middleware for request tracking."""

import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import structlog

logger = structlog.get_logger()


class CorrelationMiddleware(BaseHTTPMiddleware):
    """Add correlation ID to all requests for tracking and tracing."""

    async def dispatch(self, request: Request, call_next):
        """Add correlation ID to request and response."""
        # Get or generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))

        # Store in request state for access by handlers
        request.state.correlation_id = correlation_id

        # Log request start
        logger.info(
            "Request started",
            correlation_id=correlation_id,
            method=request.method,
            path=request.url.path,
            user_agent=request.headers.get("User-Agent"),
        )

        # Process request
        response = await call_next(request)

        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id

        # Log request completion
        logger.info(
            "Request completed",
            correlation_id=correlation_id,
            status_code=response.status_code,
            method=request.method,
            path=request.url.path,
        )

        return response
