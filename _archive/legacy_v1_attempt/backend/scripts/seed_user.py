"""Seed default user for single-user mode."""

import asyncio
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.modules.users.models import User


async def seed_default_user() -> None:
    settings = get_settings()
    user_id = uuid.UUID(settings.default_user_id)

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        if result.scalar_one_or_none():
            print("Default user already exists.")
            return

        user = User(
            id=user_id,
            email="admin@copiloto.local",
            hashed_password=hash_password("copiloto123"),
            full_name="Copiloto User",
            is_active=True,
        )
        session.add(user)
        await session.commit()
        print(f"Default user created: {user.email} (id={user.id})")


if __name__ == "__main__":
    asyncio.run(seed_default_user())
