"""Standardized API Response Envelopes."""

from typing import Generic, TypeVar, Optional, List, Any
from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None


class ApiResponse(BaseModel, Generic[T]):
    """Standard success response wrapper."""
    success: bool = True
    data: T
    error: Optional[ErrorDetail] = None


class PaginationMeta(BaseModel):
    page: int
    size: int
    total_records: int
    has_next: bool


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated collection response envelope."""
    success: bool = True
    pagination: PaginationMeta
    data: List[T]
    error: Optional[ErrorDetail] = None


class HealthResponse(BaseModel):
    """Health check payload."""
    status: str = "ok"
    version: str
    environment: str
    upstream_status: str
