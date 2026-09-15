"""Global exception handlers, registered on the FastAPI app in main.py.

Guarantees that every error response — expected or not — has the exact
same JSON shape (see app.responses.envelope.ErrorResponse), and that
unexpected exceptions never leak internal details (stack traces, SQL, etc.)
to the client.
"""
from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.constants import REQUEST_ID_HEADER
from app.core.logging import get_logger
from app.exceptions.base import AppException
from app.responses.envelope import ErrorDetail, ErrorResponse

logger = get_logger("exceptions")


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None) or request.headers.get(REQUEST_ID_HEADER)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle all deliberately-raised AppException subclasses."""
    logger.warning(
        "handled_exception",
        error_code=exc.error_code,
        status_code=exc.status_code,
        path=request.url.path,
        request_id=_request_id(request),
    )
    body = ErrorResponse(
        status=exc.status_code,
        message=exc.message,
        error=exc.error_code,
        details=exc.details,
        request_id=_request_id(request),
    )
    return JSONResponse(status_code=exc.status_code, content=body.model_dump(mode="json"))


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle standard Starlette/FastAPI HTTPExceptions (e.g. 404 route not found)."""
    body = ErrorResponse(
        status=exc.status_code,
        message=str(exc.detail),
        error="http_error",
        request_id=_request_id(request),
    )
    return JSONResponse(status_code=exc.status_code, content=body.model_dump(mode="json"))


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic/FastAPI request validation errors with field-level details."""
    details = [
        ErrorDetail(field=".".join(str(p) for p in err["loc"][1:]), message=err["msg"])
        for err in exc.errors()
    ]
    body = ErrorResponse(
        status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message="One or more fields failed validation",
        error="validation_error",
        details=details,
        request_id=_request_id(request),
    )
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=body.model_dump(mode="json"))


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for any exception not otherwise handled.

    Logs the full exception server-side but returns a generic, safe message
    to the client — never leak internals like stack traces or SQL statements.
    """
    logger.error(
        "unhandled_exception",
        exc_info=exc,
        path=request.url.path,
        request_id=_request_id(request),
    )
    body = ErrorResponse(
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message="An unexpected error occurred. Please try again later.",
        error="internal_error",
        request_id=_request_id(request),
    )
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=body.model_dump(mode="json"))


def register_exception_handlers(app: FastAPI) -> None:
    """Attach all global exception handlers to the FastAPI application instance."""
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
