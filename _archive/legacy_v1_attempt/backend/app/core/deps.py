"""FastAPI dependencies."""

import uuid
from typing import AsyncGenerator, Optional

from fastapi import Depends, HTTPException, Request, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.redis import get_redis_client
from app.db.session import get_db_session


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db_session():
        yield session


async def get_redis() -> AsyncGenerator[Redis, None]:
    client = get_redis_client()
    try:
        yield client
    finally:
        pass


def get_current_user_id(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> uuid.UUID:
    """Return authenticated user ID or default in single-user mode."""
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return uuid.UUID(str(user_id))
    if settings.single_user_mode:
        return uuid.UUID(settings.default_user_id)
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
    )
