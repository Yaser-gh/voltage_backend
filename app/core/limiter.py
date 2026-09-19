"""SlowAPI rate limiter configuration, backed by Redis for multi-worker consistency."""
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config.settings import settings

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=str(settings.REDIS_URL),
    default_limits=[settings.RATE_LIMIT_DEFAULT],
    headers_enabled=False,
)
