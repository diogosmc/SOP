"""Tests for Redis cache helpers."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.core.cache import (
    TTL_DASHBOARD,
    build_cache_key,
    cache_delete,
    cache_get,
    cache_set,
    get_or_set_json,
    invalidate_user_cache,
)


@pytest.mark.asyncio
async def test_cache_set_and_get_with_redis_mock() -> None:
    store: dict[str, str] = {}
    mock_redis = AsyncMock()

    setex_mock = AsyncMock(side_effect=lambda key, ttl, value: store.__setitem__(key, value))
    mock_redis.set = AsyncMock(side_effect=lambda key, value, ex: store.__setitem__(key, value))
    mock_redis.setex = setex_mock
    mock_redis.get = AsyncMock(side_effect=lambda key: store.get(key))

    with patch("app.core.cache.get_redis_client", return_value=mock_redis):
        await cache_set("test:key", "value", 60)
        result = await cache_get("test:key")

    assert result == "value"
    mock_redis.set.assert_called_once()


@pytest.mark.asyncio
async def test_cache_fallback_when_redis_fails() -> None:
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(side_effect=ConnectionError("redis down"))

    calls = 0

    async def factory() -> dict[str, str]:
        nonlocal calls
        calls += 1
        return {"ok": True}

    with patch("app.core.cache.get_redis_client", return_value=mock_redis):
        result = await get_or_set_json("fail:key", TTL_DASHBOARD, factory)

    assert result == {"ok": True}
    assert calls == 1


@pytest.mark.asyncio
async def test_get_or_set_json_uses_cache() -> None:
    store: dict[str, str] = {}
    mock_redis = AsyncMock()

    mock_redis.set = AsyncMock(side_effect=lambda key, value, ex: store.__setitem__(key, value))
    mock_redis.get = AsyncMock(side_effect=lambda key: store.get(key))

    calls = 0

    async def factory() -> dict[str, int]:
        nonlocal calls
        calls += 1
        return {"count": 42}

    with patch("app.core.cache.get_redis_client", return_value=mock_redis):
        first = await get_or_set_json("cached:key", TTL_DASHBOARD, factory)
        second = await get_or_set_json("cached:key", TTL_DASHBOARD, factory)

    assert first == {"count": 42}
    assert second == {"count": 42}
    assert calls == 1


@pytest.mark.asyncio
async def test_invalidate_user_cache() -> None:
    user_id = uuid.uuid4()
    deleted: list[str] = []
    mock_redis = AsyncMock()

    async def scan_iter(match: str):
        yield f"copiloto:reports:{user_id}:daily"
        yield f"copiloto:reports:{user_id}:weekly"

    async def delete(*keys: str) -> None:
        deleted.extend(keys)

    mock_redis.scan_iter = scan_iter
    mock_redis.delete = delete

    with patch("app.core.cache.get_redis_client", return_value=mock_redis):
        await invalidate_user_cache(user_id, "reports")

    assert len(deleted) == 2


def test_build_cache_key() -> None:
    user_id = uuid.UUID("00000000-0000-4000-a000-000000000001")
    key = build_cache_key("finance:summary", user_id, "2026-06", "all")
    assert key.startswith("copiloto:finance:summary:")
    assert str(user_id) in key


@pytest.mark.asyncio
async def test_cache_delete() -> None:
    mock_redis = AsyncMock()
    with patch("app.core.cache.get_redis_client", return_value=mock_redis):
        await cache_delete("some:key")
    mock_redis.delete.assert_called_once_with("some:key")
