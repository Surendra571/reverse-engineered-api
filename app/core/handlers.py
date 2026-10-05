"""Global exception handlers mapping domain and system exceptions to uniform HTTP responses."""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.exceptions import (
    AppError,
    ResourceNotFoundError,
    UpstreamServiceUnavailableError,
    UpstreamRateLimitedError,
    MalformedUpstreamDataError,
    ValidationError as CustomValidationError,
)
from app.core.logging import logger


async def app_exception_handler(request: Request, exc: AppError) -> JSONResponse:
    """Base handler for general application errors."""
    logger.error("Application error: %s", exc.message, extra={"path": request.url.path, "details": exc.details})
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "data": None,
            "error": {"code": "INTERNAL_ERROR", "message": exc.message, "details": exc.details or None},
        },
    )


async def resource_not_found_handler(request: Request, exc: ResourceNotFoundError) -> JSONResponse:
    """Handler for 404 resource not found errors."""
    logger.warning("Resource not found: %s", exc.message, extra={"path": request.url.path, "details": exc.details})
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "success": False,
            "data": None,
            "error": {"code": "NOT_FOUND", "message": exc.message, "details": exc.details or None},
        },
    )


async def upstream_unavailable_handler(request: Request, exc: UpstreamServiceUnavailableError) -> JSONResponse:
    """Handler for upstream 503 errors."""
    logger.error("Upstream unavailable: %s", exc.message, extra={"path": request.url.path, "details": exc.details})
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        headers={"Retry-After": "30"},
        content={
            "success": False,
            "data": None,
            "error": {"code": "UPSTREAM_UNAVAILABLE", "message": exc.message, "details": exc.details or None},
        },
    )


async def upstream_rate_limited_handler(request: Request, exc: UpstreamRateLimitedError) -> JSONResponse:
    """Handler for upstream 429/403 rate limit / anti-bot challenge errors."""
    logger.warning("Upstream rate limited: %s", exc.message, extra={"path": request.url.path, "details": exc.details})
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        headers={"Retry-After": "60"},
        content={
            "success": False,
            "data": None,
            "error": {"code": "UPSTREAM_RATE_LIMITED", "message": exc.message, "details": exc.details or None},
        },
    )


async def malformed_upstream_handler(request: Request, exc: MalformedUpstreamDataError) -> JSONResponse:
    """Handler for upstream schema / parsing errors."""
    logger.error("Malformed upstream response: %s", exc.message, extra={"path": request.url.path, "details": exc.details})
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={
            "success": False,
            "data": None,
            "error": {"code": "BAD_GATEWAY", "message": exc.message, "details": exc.details or None},
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handler for FastAPI request validation errors."""
    errors = exc.errors()
    sanitized_errors = []
    for e in errors:
        loc = [str(x) for x in e.get("loc", []) if x not in ("body", "query", "path")]
        field_name = ".".join(loc) or "parameter"
        sanitized_errors.append({
            "field": field_name,
            "message": e.get("msg", "Invalid value"),
            "type": e.get("type", "validation_error"),
        })

    logger.info("Request validation failed on %s: %s", request.url.path, str(sanitized_errors))
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request parameters.",
                "details": sanitized_errors,
            },
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler ensuring internal stack traces are NEVER exposed to clients."""
    logger.exception("Unhandled server exception: %s", str(exc), extra={"path": request.url.path})
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected server error occurred. Please try again later.",
                "details": None,
            },
        },
    )
