"""Redis cache helpers with graceful fallback when Redis is unavailable."""

from __future__ import annotations

import json
import logging
import uuid
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from app.db.redis import get_redis_client

logger = logging.getLogger(__name__)

T = TypeVar("T")

# TTL presets (seconds)
TTL_DASHBOARD = 60
TTL_ANALYTICS = 300
TTL_INSIGHTS = 900


def build_cache_key(prefix: str, user_id: uuid.UUID, *parts: str) -> str:
    """Build a namespaced cache key for a user-scoped resource."""
    suffix = ":".join(str(part) for part in parts if part)
    base = f"copiloto:{prefix}:{user_id}"
    return f"{base}:{suffix}" if suffix else base


async def cache_get(key: str) -> str | None:
    try:
        redis = get_redis_client()
        return await redis.get(key)
    except Exception as exc:
        logger.warning("cache_get_failed", extra={"key": key, "error": str(exc)})
        return None


async def cache_set(key: str, value: str, ttl: int) -> None:
    try:
        redis = get_redis_client()
        await redis.set(key, value, ex=ttl)
    except Exception as exc:
        logger.warning("cache_set_failed", extra={"key": key, "error": str(exc)})


async def cache_delete(key: str) -> None:
    try:
        redis = get_redis_client()
        await redis.delete(key)
    except Exception as exc:
        logger.warning("cache_delete_failed", extra={"key": key, "error": str(exc)})


async def cache_delete_prefix(prefix: str) -> None:
    """Delete all keys starting with prefix."""
    try:
        redis = get_redis_client()
        keys: list[str] = []
        async for key in redis.scan_iter(match=f"{prefix}*"):
            keys.append(key)
        if keys:
            await redis.delete(*keys)
    except Exception as exc:
        logger.warning("cache_delete_prefix_failed", extra={"prefix": prefix, "error": str(exc)})


def _serialize(value: Any) -> str:
    if hasattr(value, "model_dump"):
        payload = value.model_dump(mode="json")
    else:
        payload = value
    return json.dumps(payload, default=str)


def _deserialize(raw: str) -> Any:
    return json.loads(raw)


async def get_or_set_json(
    key: str,
    ttl: int,
    factory: Callable[[], Awaitable[T]],
) -> T:
    """Return cached JSON value or compute and store it."""
    cached = await cache_get(key)
    if cached is not None:
        return _deserialize(cached)

    result = await factory()
    await cache_set(key, _serialize(result), ttl)
    return result


async def invalidate_user_cache(user_id: uuid.UUID, prefix: str) -> None:
    """Invalidate all cache entries for a user under a prefix."""
    await cache_delete_prefix(f"copiloto:{prefix}:{user_id}")
