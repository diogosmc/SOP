"""Initialize database and seed default user."""

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.base import Base
from app.db import models  # noqa: F401
from app.db.session import engine
from scripts.seed_user import seed_default_user


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.execute(__import__("sqlalchemy").text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.execute(__import__("sqlalchemy").text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
        await conn.run_sync(Base.metadata.create_all)
    await seed_default_user()
    print("Database initialized successfully.")


if __name__ == "__main__":
    asyncio.run(init_db())
