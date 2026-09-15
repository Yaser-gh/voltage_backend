"""Middleware: structured access logging for every request/response pair."""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger

logger = get_logger("access")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Logs method, path, status code, and client IP for every request.

    Deliberately avoids logging request bodies (may contain passwords, PII)
    or full headers (may contain Authorization tokens).
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        logger.info(
            "http_request",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            client_ip=request.client.host if request.client else None,
        )
        return response
