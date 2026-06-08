"""FastAPI dependencies."""

import uuid
from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_db_session
from app.modules.users.service import ensure_default_user_exists


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db_session():
        yield session


async def get_current_user_id(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> uuid.UUID:
    """Return authenticated user ID or default when auth is disabled."""
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return uuid.UUID(str(user_id))
    if not settings.auth_enabled:
        user = await ensure_default_user_exists(db, settings)
        return user.id
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
    )
