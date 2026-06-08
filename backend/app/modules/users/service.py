"""User business logic."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.modules.users.models import User


async def ensure_default_user_exists(
    db: AsyncSession,
    settings: Settings | None = None,
) -> User:
    """Return the configured default user, creating it when missing."""
    from app.telegram.security import is_valid_telegram_user_id

    cfg = settings or get_settings()
    user_id = uuid.UUID(cfg.default_user_id)

    result = await db.execute(select(User).where(User.id == user_id))
    existing = result.scalar_one_or_none()
    if existing is not None:
        return existing

    telegram_id: int | None = None
    if is_valid_telegram_user_id(cfg.telegram_allowed_user_id):
        telegram_id = int(cfg.telegram_allowed_user_id.strip())

    user = User(
        id=user_id,
        name="Diogo",
        email="default@copiloto.local",
        telegram_id=telegram_id,
        timezone=cfg.timezone,
        preferences={},
        is_active=True,
        is_admin=True,
    )
    db.add(user)
    await db.flush()
    return user
