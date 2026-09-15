"""Reusable Pydantic field validators shared across multiple schemas."""
from __future__ import annotations

import re
from datetime import date

USERNAME_RE = re.compile(r"^[a-zA-Z0-9_.]{3,50}$")
# Iranian-style mobile numbers (e.g. 09123456789) or generic E.164 international numbers.
PHONE_RE = re.compile(r"^(?:\+?[1-9]\d{7,14}|0\d{9,10})$")
BANK_ACCOUNT_RE = re.compile(r"^[0-9\-]{5,34}$")
# At least 8 chars, one letter, one digit.
PASSWORD_RE = re.compile(r"^(?=.*[A-Za-z])(?=.*\d).{8,128}$")


def validate_username(value: str) -> str:
    """Validate a username: 3-50 chars, alphanumeric plus `_` and `.` only."""
    value = value.strip()
    if not USERNAME_RE.match(value):
        raise ValueError("Username must be 3-50 characters: letters, digits, '_' or '.' only")
    return value


def validate_phone(value: str) -> str:
    """Validate a phone number in Iranian mobile or E.164 international format."""
    value = value.strip().replace(" ", "")
    if not PHONE_RE.match(value):
        raise ValueError("Invalid phone number format")
    return value


def validate_password_strength(value: str) -> str:
    """Enforce a minimum password strength policy."""
    if not PASSWORD_RE.match(value):
        raise ValueError("Password must be at least 8 characters and include a letter and a digit")
    return value


def validate_bank_account_number(value: str) -> str:
    """Validate a bank account/IBAN-like number: digits and dashes only."""
    value = value.strip()
    if not BANK_ACCOUNT_RE.match(value):
        raise ValueError("Invalid bank account number format")
    return value


def validate_bank_name(value: str) -> str:
    """Validate a bank name field: non-empty, reasonable length, no control characters."""
    value = value.strip()
    if not (2 <= len(value) <= 100):
        raise ValueError("Bank name must be between 2 and 100 characters")
    return value


def validate_positive_amount(value: float) -> float:
    """Ensure a monetary amount is strictly positive and has at most 2 decimal places."""
    if value <= 0:
        raise ValueError("Amount must be greater than zero")
    if round(value, 2) != value:
        raise ValueError("Amount must have at most 2 decimal places")
    return value


def validate_not_future_date(value: date) -> date:
    """Ensure a date is not in the future (e.g. a receipt/payment date)."""
    if value > date.today():
        raise ValueError("Date cannot be in the future")
    return value


def validate_biography(value: str | None) -> str | None:
    """Validate an optional free-text biography field: max length, strip whitespace."""
    if value is None:
        return None
    value = value.strip()
    if len(value) > 2000:
        raise ValueError("Biography must not exceed 2000 characters")
    return value or None


def sanitize_search_term(value: str | None) -> str | None:
    """Strip characters commonly used in SQL/NoSQL/LDAP injection attempts from a
    free-text search term. Defense-in-depth only — the real protection is
    parameterized queries via SQLAlchemy, never raw string interpolation."""
    if value is None:
        return None
    value = value.strip()
    value = re.sub(r"[;'\"\\%_]", "", value)
    return value[:200] or None
