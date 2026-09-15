"""Shared pagination/sorting/search query-parameter dependency."""
from dataclasses import dataclass
from typing import Literal

from fastapi import Query

from app.core.constants import DEFAULT_LIMIT, DEFAULT_PAGE, MAX_LIMIT


@dataclass(slots=True)
class PaginationParams:
    """Normalized pagination + sorting + search parameters for list endpoints."""
    page: int
    limit: int
    offset: int
    sort_by: str | None
    sort_order: Literal["asc", "desc"]
    search: str | None


def pagination_params(
    page: int = Query(DEFAULT_PAGE, ge=1, description="Page number, 1-indexed"),
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT, description="Items per page"),
    sort_by: str | None = Query(None, description="Field name to sort by"),
    sort_order: Literal["asc", "desc"] = Query("desc", description="Sort direction"),
    search: str | None = Query(None, min_length=1, max_length=200, description="Free-text search term"),
) -> PaginationParams:
    """FastAPI dependency: parses and validates common list-endpoint query params."""
    return PaginationParams(
        page=page,
        limit=limit,
        offset=(page - 1) * limit,
        sort_by=sort_by,
        sort_order=sort_order,
        search=search,
    )
