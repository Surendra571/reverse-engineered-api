"""Main FastAPI Application entrypoint."""

import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional, List
from fastapi import FastAPI, Request, status, Query, Path, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.core.http_client import HTTPClientManager
from app.core.exceptions import (
    AppError,
    ResourceNotFoundError,
    UpstreamServiceUnavailableError,
    UpstreamRateLimitedError,
    MalformedUpstreamDataError,
)
from app.core.handlers import (
    app_exception_handler,
    resource_not_found_handler,
    upstream_unavailable_handler,
    upstream_rate_limited_handler,
    malformed_upstream_handler,
    validation_exception_handler,
)
from app.models.response import HealthResponse, ApiResponse, PaginatedResponse
from app.models.domain import FundSearchResult, FundDetail, CategoriesMetadata
from app.services.fund_service import FundService
from app.api.deps import get_fund_service
from app.api.v1.router import api_v1_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manages application startup and shutdown events."""
    setup_logging(debug=settings.DEBUG)
    logger.info("Initializing application: %s v%s", settings.PROJECT_NAME, settings.VERSION)
    # Warm up HTTP client pool
    HTTPClientManager.get_client()
    yield
    logger.info("Shutting down application, closing client connections...")
    await HTTPClientManager.close_client()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Production-quality API facade over public mutual fund intelligence and compounding calculators. "
        "Built for the Razorpay Forward-Deployed Engineer technical assignment."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Cross-Origin Resource Sharing (CORS) Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing & tracing middleware
@app.middleware("http")
async def add_process_time_and_log(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start_time
    response.headers["X-Response-Time-Ms"] = f"{duration * 1000:.2f}"
    logger.info(
        "%s %s completed with status %d in %.2fms",
        request.method,
        request.url.path,
        response.status_code,
        duration * 1000,
    )
    return response


# Register Global Exception Handlers
app.add_exception_handler(ResourceNotFoundError, resource_not_found_handler)
app.add_exception_handler(UpstreamServiceUnavailableError, upstream_unavailable_handler)
app.add_exception_handler(UpstreamRateLimitedError, upstream_rate_limited_handler)
app.add_exception_handler(MalformedUpstreamDataError, malformed_upstream_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(AppError, app_exception_handler)


# Health Check Endpoint
@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="Service Health Check",
    description="Reports the service status, application version, and upstream reachability.",
)
async def health_check(service: FundService = Depends(get_fund_service)) -> HealthResponse:
    upstream_alive = await service.check_health()
    return HealthResponse(
        status="ok",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        upstream_status="healthy" if upstream_alive else "degraded",
    )


# Root landing endpoint
@app.get("/", tags=["System"], include_in_schema=False)
async def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs",
        "health_url": "/health",
    }


# Include Core API v1
app.include_router(api_v1_router, prefix=settings.API_V1_STR)


# Suggested Top-Level Route Aliases for assignment specification convenience:
# GET /api/search?q=<query>
# GET /api/items/{id}
# GET /api/categories
@app.get(
    "/api/search",
    response_model=ApiResponse[List[FundSearchResult]],
    tags=["Convenience Aliases"],
    summary="Search Mutual Funds (Alias)",
)
async def alias_search(
    q: str = Query(..., min_length=2, max_length=100),
    limit: int = Query(10, ge=1, le=50),
    service: FundService = Depends(get_fund_service),
) -> ApiResponse[List[FundSearchResult]]:
    results = await service.search_funds(query=q, limit=limit)
    return ApiResponse(data=results)


@app.get(
    "/api/items/{id}",
    response_model=ApiResponse[FundDetail],
    tags=["Convenience Aliases"],
    summary="Get Item Details (Alias)",
)
async def alias_item_detail(
    id: str = Path(..., min_length=3, max_length=150, pattern=r"^[a-z0-9\-]+$"),
    service: FundService = Depends(get_fund_service),
) -> ApiResponse[FundDetail]:
    detail = await service.get_fund_detail(fund_id=id)
    return ApiResponse(data=detail)


@app.get(
    "/api/categories",
    response_model=ApiResponse[CategoriesMetadata],
    tags=["Convenience Aliases"],
    summary="Get Categories (Alias)",
)
async def alias_categories(
    service: FundService = Depends(get_fund_service),
) -> ApiResponse[CategoriesMetadata]:
    meta = await service.get_categories_metadata()
    return ApiResponse(data=meta)
