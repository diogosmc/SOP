"""Redis cache helpers for performance optimization."""

import json
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

from app.core.config import get_settings
from app.db.redis import get_redis_client

F = TypeVar("F", bound=Callable[..., Any])


async def cache_get(key: str) -> Optional[Any]:
    client = get_redis_client()
    raw = await client.get(key)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


async def cache_set(key: str, value: Any, ttl: int) -> None:
    client = get_redis_client()
    await client.set(key, json.dumps(value, default=str), ex=ttl)


async def cache_delete(key: str) -> None:
    client = get_redis_client()
    await client.delete(key)


def cached(prefix: str, ttl_setting: str = "cache_dashboard_ttl") -> Callable[[F], F]:
    """Decorator for async functions returning JSON-serializable data."""

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            cache_key_parts = [prefix]
            for arg in args[1:]:
                cache_key_parts.append(str(arg))
            for k, v in sorted(kwargs.items()):
                cache_key_parts.append(f"{k}:{v}")
            cache_key = ":".join(cache_key_parts)

            cached_value = await cache_get(cache_key)
            if cached_value is not None:
                return cached_value

            result = await func(*args, **kwargs)
            ttl = getattr(get_settings(), ttl_setting, 60)
            await cache_set(cache_key, result, ttl)
            return result

        return wrapper  # type: ignore[return-value]

    return decorator
