"""Domain exception hierarchy for the application."""

from typing import Optional, Any, Dict


class AppError(Exception):
    """Base application exception."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ResourceNotFoundError(AppError):
    """Requested resource (e.g. fund, category) not found."""


class UpstreamError(AppError):
    """Base exception for upstream provider issues."""


class UpstreamServiceUnavailableError(UpstreamError):
    """Upstream service is unreachable, timed out, or returning 5xx."""


class UpstreamRateLimitedError(UpstreamError):
    """Upstream service rate-limited the request or returned bot challenge."""


class MalformedUpstreamDataError(UpstreamError):
    """Upstream returned an unexpected schema that could not be parsed."""


class ValidationError(AppError):
    """Client input validation error."""
