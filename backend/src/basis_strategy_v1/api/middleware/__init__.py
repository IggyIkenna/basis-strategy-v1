"""Middleware package for FastAPI application.

Contains middleware components for cross-cutting concerns like
correlation ID tracking, authentication, and monitoring.
"""

from .correlation import CorrelationMiddleware

__all__ = [
    "CorrelationMiddleware",
]
