"""Ensure the configured default user exists in the database."""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import app.db.models  # noqa: F401 — register all ORM mappers
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.db.session import AsyncSessionLocal
from app.modules.users.service import ensure_default_user_exists

logger = logging.getLogger(__name__)


async def main() -> None:
    settings = get_settings()
    setup_logging(settings.log_level)

    async with AsyncSessionLocal() as db:
        user = await ensure_default_user_exists(db, settings)
        await db.commit()
        logger.info(
            "default_user_ready id=%s name=%s email=%s",
            user.id,
            user.name,
            user.email,
        )


if __name__ == "__main__":
    asyncio.run(main())
