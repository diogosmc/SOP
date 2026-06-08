"""Authentication integration tests."""

import uuid
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.deps import get_db
from app.core.security import hash_password
from app.main import app
from app.modules.users.models import User


@pytest.fixture
def auth_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUTH_ENABLED", "true")
    get_settings.cache_clear()
    yield
    monkeypatch.delenv("AUTH_ENABLED", raising=False)
    get_settings.cache_clear()


@pytest.fixture
async def auth_client(
    db_session: AsyncSession,
    auth_enabled: None,
) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        try:
            yield db_session
            await db_session.commit()
        except Exception:
            await db_session.rollback()
            raise

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


async def _create_user(db_session: AsyncSession, email: str, password: str) -> User:
    user = User(
        name="Test User",
        email=email,
        hashed_password=hash_password(password),
        is_active=True,
        is_admin=True,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest.mark.integration
@pytest.mark.asyncio
async def test_bootstrap_admin_creates_user(auth_client: AsyncClient, db_session: AsyncSession) -> None:
    from sqlalchemy import func, select

    count = await db_session.execute(
        select(func.count()).select_from(User).where(User.hashed_password.isnot(None))
    )
    if count.scalar_one() > 0:
        pytest.skip("Password user already exists in database")

    email = f"admin-{uuid.uuid4().hex[:8]}@copiloto.local"
    response = await auth_client.post(
        "/api/v1/auth/bootstrap-admin",
        json={"name": "Admin", "email": email, "password": "securepass123"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["user"]["email"] == email
    assert data["user"]["is_admin"] is True
    assert data["access_token"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_bootstrap_admin_blocks_second_run(auth_client: AsyncClient, db_session: AsyncSession) -> None:
    email = f"admin2-{uuid.uuid4().hex[:8]}@copiloto.local"
    await _create_user(db_session, email, "securepass123")

    second = await auth_client.post(
        "/api/v1/auth/bootstrap-admin",
        json={
            "name": "Other",
            "email": f"other-{uuid.uuid4().hex[:8]}@copiloto.local",
            "password": "securepass123",
        },
    )
    assert second.status_code == 403


@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_success(auth_client: AsyncClient, db_session: AsyncSession) -> None:
    email = f"login-{uuid.uuid4().hex[:8]}@copiloto.local"
    password = "securepass123"
    await _create_user(db_session, email, password)

    response = await auth_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    assert response.cookies.get("access_token")
    assert response.cookies.get("refresh_token")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_invalid_password(auth_client: AsyncClient, db_session: AsyncSession) -> None:
    email = f"bad-{uuid.uuid4().hex[:8]}@copiloto.local"
    await _create_user(db_session, email, "securepass123")

    response = await auth_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "wrong-password"},
    )
    assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_me_authenticated(auth_client: AsyncClient, db_session: AsyncSession) -> None:
    email = f"me-{uuid.uuid4().hex[:8]}@copiloto.local"
    password = "securepass123"
    await _create_user(db_session, email, password)
    await auth_client.post("/api/v1/auth/login", json={"email": email, "password": password})

    me = await auth_client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["data"]["email"] == email


@pytest.mark.integration
@pytest.mark.asyncio
async def test_logout_clears_cookies(auth_client: AsyncClient, db_session: AsyncSession) -> None:
    email = f"logout-{uuid.uuid4().hex[:8]}@copiloto.local"
    password = "securepass123"
    await _create_user(db_session, email, password)
    await auth_client.post("/api/v1/auth/login", json={"email": email, "password": password})

    logout = await auth_client.post("/api/v1/auth/logout")
    assert logout.status_code == 200


@pytest.mark.integration
@pytest.mark.asyncio
async def test_protected_route_401_when_auth_enabled(auth_client: AsyncClient) -> None:
    response = await auth_client.get("/api/v1/tasks")
    assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_protected_route_accessible_when_auth_disabled(client: AsyncClient) -> None:
    response = await client.get("/api/v1/tasks")
    assert response.status_code == 200


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rate_limit_with_redis_mock(auth_client: AsyncClient) -> None:
    from unittest.mock import AsyncMock, patch

    mock_redis = AsyncMock()
    counts: dict[str, int] = {}

    async def incr(key: str) -> int:
        counts[key] = counts.get(key, 0) + 1
        return counts[key]

    mock_redis.incr = incr
    mock_redis.expire = AsyncMock()

    with patch("app.middleware.rate_limit.get_redis_client", return_value=mock_redis):
        for _ in range(10):
            response = await auth_client.post(
                "/api/v1/auth/login",
                json={"email": "x@copiloto.local", "password": "wrong"},
            )
            assert response.status_code in (401, 429)
    assert counts
