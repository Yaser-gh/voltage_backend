"""Phone-number-specific validation helpers (thin wrapper for schema reuse)."""
from app.validators.common import validate_phone

__all__ = ["validate_phone"]
