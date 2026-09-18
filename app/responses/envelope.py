"""Standardized response envelopes used across every endpoint in the API."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")

class MessageResponce(BaseModel):
    pass

class ErrorDetail(BaseModel):
    """A single field-level validation error entry."""
    field: str | None = None
    message: str


class ErrorResponse(BaseModel):
    """Uniform error response shape returned by every failure path in the API.

    status   -> HTTP status code
    message  -> human-readable, safe-to-display summary
    error    -> stable machine-readable error code (for client branching)
    details  -> optional list of field-level errors / extra context
    timestamp-> ISO-8601 UTC timestamp of when the error occurred
    request_id -> correlation id, echoed from the X-Request-ID header/middleware
    """
    status: int
    message: str
    error: str
    details: list[ErrorDetail] | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    request_id: str | None = None


class SuccessResponse(BaseModel, Generic[T]):
    """Uniform success envelope for single-resource endpoints."""
    status: int = 200
    message: str = "OK"
    data: T | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PaginationMeta(BaseModel):
    """Pagination metadata attached to list responses."""
    page: int
    limit: int
    total_items: int
    total_pages: int
    has_next: bool
    has_prev: bool


class PaginatedResponse(BaseModel, Generic[T]):
    """Uniform success envelope for paginated list endpoints."""
    status: int = 200
    message: str = "OK"
    data: list[T]
    meta: PaginationMeta
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


def build_pagination_meta(page: int, limit: int, total_items: int) -> PaginationMeta:
    """Compute PaginationMeta from raw counts. Pure function, no DB access."""
    total_pages = max(1, (total_items + limit - 1) // limit)
    return PaginationMeta(
        page=page,
        limit=limit,
        total_items=total_items,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )
