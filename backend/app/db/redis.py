"""Redis async client."""

from typing import Optional

from redis.asyncio import Redis

from app.core.config import get_settings

_redis_client: Optional[Redis] = None


def get_redis_client() -> Redis:
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        _redis_client = Redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def check_redis_health() -> bool:
    """Return True if Redis responds to PING."""
    try:
        client = get_redis_client()
        return bool(await client.ping())
    except Exception:
        return False


async def close_redis() -> None:
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
