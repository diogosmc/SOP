"""Pytest fixtures for backend tests."""

import uuid
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

import app.db.models  # noqa: F401 — register all ORM mappers
from app.core.config import get_settings
from app.core.deps import get_current_user_id, get_db
from app.main import app
from app.modules.users.models import User

_test_engine = create_async_engine(
    get_settings().database_url,
    poolclass=NullPool,
    echo=False,
)
TestSessionLocal = async_sessionmaker(
    _test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def postgres_url() -> str:
    get_settings.cache_clear()
    return get_settings().database_url


@pytest.fixture
async def default_user_id() -> uuid.UUID:
    settings = get_settings()
    user_id = uuid.UUID(settings.default_user_id)
    async with TestSessionLocal() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        if result.scalar_one_or_none() is None:
            session.add(
                User(
                    id=user_id,
                    name="Test User",
                    email="test@copiloto.local",
                )
            )
            await session.commit()
    return user_id


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture
async def client(
    db_session: AsyncSession, default_user_id: uuid.UUID
) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        try:
            yield db_session
            await db_session.commit()
        except Exception:
            await db_session.rollback()
            raise

    def override_get_current_user_id() -> uuid.UUID:
        return default_user_id

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_id] = override_get_current_user_id

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
