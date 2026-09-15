"""Concrete, domain-specific application exceptions used throughout the API."""
from app.exceptions.base import AppException


class NotFoundException(AppException):
    status_code = 404
    error_code = "not_found"
    message = "The requested resource was not found"


class AlreadyExistsException(AppException):
    status_code = 409
    error_code = "already_exists"
    message = "The resource already exists"


class ValidationException(AppException):
    status_code = 422
    error_code = "validation_error"
    message = "Validation failed"


class UnauthorizedException(AppException):
    status_code = 401
    error_code = "unauthorized"
    message = "Authentication is required"


class InvalidCredentialsException(AppException):
    """Deliberately generic message — never reveal whether the username or
    the password was the incorrect part (prevents user enumeration)."""
    status_code = 401
    error_code = "invalid_credentials"
    message = "Invalid username or password"


class TokenExpiredException(AppException):
    status_code = 401
    error_code = "token_expired"
    message = "Token has expired"


class TokenInvalidException(AppException):
    status_code = 401
    error_code = "token_invalid"
    message = "Token is invalid"


class TokenRevokedException(AppException):
    status_code = 401
    error_code = "token_revoked"
    message = "Token has been revoked"


class AccountLockedException(AppException):
    status_code = 423
    error_code = "account_locked"
    message = "Account is temporarily locked due to repeated failed login attempts"


class ForbiddenException(AppException):
    status_code = 403
    error_code = "forbidden"
    message = "You do not have permission to perform this action"


class RateLimitExceededException(AppException):
    status_code = 429
    error_code = "rate_limit_exceeded"
    message = "Too many requests, please try again later"


class FileValidationException(AppException):
    status_code = 400
    error_code = "file_validation_error"
    message = "The uploaded file failed validation"


class FileTooLargeException(AppException):
    status_code = 413
    error_code = "file_too_large"
    message = "The uploaded file exceeds the maximum allowed size"


class UnsupportedMediaTypeException(AppException):
    status_code = 415
    error_code = "unsupported_media_type"
    message = "The uploaded file type is not supported"


class PathTraversalException(AppException):
    status_code = 400
    error_code = "invalid_path"
    message = "Invalid file path"


class BusinessRuleViolationException(AppException):
    status_code = 422
    error_code = "business_rule_violation"
    message = "The requested operation violates a business rule"
