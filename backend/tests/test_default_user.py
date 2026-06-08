"""Tests for default user bootstrap."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import delete, func, select

from app.core.config import get_settings
from app.modules.memory.service import MemoryService
from app.modules.users.models import User
from app.modules.users.service import ensure_default_user_exists
from app.telegram.handlers import handle_free_text


async def _remove_default_user(db_session) -> uuid.UUID:
    settings = get_settings()
    user_id = uuid.UUID(settings.default_user_id)
    await db_session.execute(delete(User).where(User.id == user_id))
    await db_session.commit()
    return user_id


@pytest.mark.asyncio
async def test_ensure_default_user_creates_on_empty_db(db_session) -> None:
    user_id = await _remove_default_user(db_session)

    user = await ensure_default_user_exists(db_session)
    await db_session.commit()

    assert user.id == user_id
    assert user.name == "Diogo"
    assert user.email == "default@copiloto.local"
    assert user.is_active is True
    assert user.is_admin is True
    assert user.timezone == get_settings().timezone


@pytest.mark.asyncio
async def test_ensure_default_user_idempotent(db_session) -> None:
    await _remove_default_user(db_session)

    user1 = await ensure_default_user_exists(db_session)
    await db_session.commit()
    user2 = await ensure_default_user_exists(db_session)

    count = await db_session.scalar(
        select(func.count()).select_from(User).where(User.id == user1.id)
    )
    assert count == 1
    assert user2.id == user1.id


@pytest.mark.asyncio
async def test_memory_service_after_ensure(db_session) -> None:
    await _remove_default_user(db_session)

    user = await ensure_default_user_exists(db_session)
    await db_session.commit()

    service = MemoryService(db_session)
    await service.process_chat_message(user.id, "Estou desanimado hoje")
    await db_session.commit()

    result = await db_session.execute(select(User).where(User.id == user.id))
    assert result.scalar_one_or_none() is not None


class _SessionContext:
    def __init__(self, session) -> None:
        self._session = session

    async def __aenter__(self):
        return self._session

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_handle_free_text_after_db_reset(db_session) -> None:
    user_id = await _remove_default_user(db_session)

    update = MagicMock()
    update.effective_user = MagicMock(id=12345)
    update.message = MagicMock()
    update.message.text = "Estou desanimado hoje"
    update.message.reply_text = AsyncMock()
    context = MagicMock()

    with patch(
        "app.telegram.handlers.AsyncSessionLocal",
        return_value=_SessionContext(db_session),
    ):
        with patch("app.telegram.handlers.is_user_allowed", return_value=True):
            with patch(
                "app.telegram.handlers.route_instructor_message",
                new=AsyncMock(return_value="Entendo. Quer conversar sobre isso?"),
            ):
                await handle_free_text(update, context)

    update.message.reply_text.assert_awaited_once()
    reply_text = update.message.reply_text.await_args.args[0]
    assert "usuário padrão" not in reply_text.lower()
    assert "algo deu errado" not in reply_text.lower()

    result = await db_session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    assert user is not None
    assert user.name == "Diogo"
