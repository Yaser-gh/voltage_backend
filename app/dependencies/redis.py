"""Redis connection pool and FastAPI dependency."""
from collections.abc import AsyncGenerator

from redis.asyncio import ConnectionPool, Redis

from app.config.settings import settings

_pool: ConnectionPool = ConnectionPool.from_url(str(settings.REDIS_URL), decode_responses=True)


async def get_redis() -> AsyncGenerator[Redis, None]:
    """FastAPI dependency yielding a Redis client bound to the shared connection pool."""
    client = Redis(connection_pool=_pool)
    try:
        yield client
    finally:
        await client.aclose()


async def dispose_redis_pool() -> None:
    """Gracefully close the Redis connection pool on application shutdown."""
    await _pool.disconnect()
