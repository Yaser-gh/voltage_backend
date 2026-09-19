"""Middleware: attaches standard security-hardening HTTP response headers."""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.config.settings import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Sets defensive headers to mitigate XSS, clickjacking, MIME sniffing, etc.

    Note: CSRF is primarily mitigated at the architecture level here since
    this API is consumed via Bearer tokens (not cookies), which are not
    automatically attached cross-site by browsers. The `X-CSRF-Structure`
    header below documents the double-submit-cookie pattern to use *if* a
    cookie-based auth flow is ever introduced.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        if request.url.path in {"/docs", "/redoc"}:
            response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https:; "
            "font-src 'self' data: https://cdn.jsdelivr.net; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        else:
            response.headers["Content-Security-Policy"] = (
            "default-src 'none'; "
            "frame-ancestors 'none'"
        )
        return response
