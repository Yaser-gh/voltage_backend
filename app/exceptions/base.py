"""Base application exception classes with a consistent shape for API errors."""
from __future__ import annotations

from typing import Any


class AppException(Exception):
    """Base class for all deliberate, handled application exceptions.

    Attributes mirror the fields of the standardized error response so the
    global exception handler can serialize them uniformly.
    """
    status_code: int = 500
    error_code: str = "internal_error"
    message: str = "An unexpected error occurred"

    def __init__(
        self,
        message: str | None = None,
        *,
        error_code: str | None = None,
        status_code: int | None = None,
        details: Any = None,
    ) -> None:
        self.message = message or self.message
        self.error_code = error_code or self.error_code
        self.status_code = status_code or self.status_code
        self.details = details
        super().__init__(self.message)
