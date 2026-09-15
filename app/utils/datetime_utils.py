"""Date/time helper utilities used across services and schemas."""
from __future__ import annotations

from datetime import date, datetime, timezone


def utcnow() -> datetime:
    """Timezone-aware current UTC datetime. Prefer this over datetime.utcnow()."""
    return datetime.now(timezone.utc)


def to_date(value: datetime | date) -> date:
    """Normalize a datetime or date value down to a plain date."""
    return value.date() if isinstance(value, datetime) else value


def is_same_month(value: date, reference: date | None = None) -> bool:
    """Check whether `value` falls in the same year/month as `reference` (default: today)."""
    reference = reference or date.today()
    return value.year == reference.year and value.month == reference.month


def month_range(reference: date | None = None) -> tuple[date, date]:
    """Return the (first_day, last_day) of the month containing `reference` (default: today)."""
    reference = reference or date.today()
    first_day = reference.replace(day=1)
    if reference.month == 12:
        next_month = reference.replace(year=reference.year + 1, month=1, day=1)
    else:
        next_month = reference.replace(month=reference.month + 1, day=1)
    from datetime import timedelta
    last_day = next_month - timedelta(days=1)
    return first_day, last_day
