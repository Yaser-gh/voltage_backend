"""Application-wide constant values and enums shared across layers."""
from enum import Enum


class ProjectStatus(str, Enum):
    """Lifecycle status of an electrical project."""
    ACTIVE = "active"
    STOPPED = "stopped"
    FINISHED = "finished"
    BAD = "bad"


class FileOwnerType(str, Enum):
    """What entity a stored file belongs to."""
    PROJECT = "project"
    PAYMENT = "payment"
    AVATAR = "avatar"


class TokenType(str, Enum):
    """JWT token category, embedded in the `type` claim."""
    ACCESS = "access"
    REFRESH = "refresh"
    RESET_PASSWORD = "reset_password"


class SecurityEventType(str, Enum):
    """Category of security-relevant log events."""
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    TOKEN_REFRESH = "token_refresh"
    TOKEN_REUSE_DETECTED = "token_reuse_detected"
    PASSWORD_CHANGED = "password_changed"
    PASSWORD_RESET_REQUESTED = "password_reset_requested"
    PASSWORD_RESET_COMPLETED = "password_reset_completed"
    ACCOUNT_LOCKED = "account_locked"
    PERMISSION_DENIED = "permission_denied"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_UPLOAD = "suspicious_upload"


# Header name used to correlate a single request across logs/services.
REQUEST_ID_HEADER = "X-Request-ID"

# Default pagination bounds, enforced by dependencies.pagination.
DEFAULT_PAGE = 1
DEFAULT_LIMIT = 20
MAX_LIMIT = 100
