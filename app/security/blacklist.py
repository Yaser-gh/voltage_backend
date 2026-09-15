"""
Token blacklist / revocation store backed by Redis.

Used to invalidate access tokens on logout before their natural expiry,
and to record rotated/reused refresh token families.
"""
from __future__ import annotations

from redis.asyncio import Redis

BLACKLIST_KEY_PREFIX = "token:blacklist:"


class TokenBlacklist:
    """Thin wrapper around Redis for JWT jti blacklisting."""

    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def add(self, jti: str, ttl_seconds: int) -> None:
        """Blacklist a token's jti for (at least) its remaining lifetime."""
        if ttl_seconds > 0:
            await self._redis.set(f"{BLACKLIST_KEY_PREFIX}{jti}", "1", ex=ttl_seconds)

    async def is_blacklisted(self, jti: str) -> bool:
        """Check whether a given jti has been revoked."""
        return await self._redis.exists(f"{BLACKLIST_KEY_PREFIX}{jti}") == 1
