"""Tests for debug routes endpoint."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client() -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_debug_routes_lists_key_paths(client: AsyncClient) -> None:
    response = await client.get("/api/v1/debug/routes")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    routes = body["data"]
    assert "/api/v1/ai/health" in routes
    assert "/api/v1/auth/bootstrap-admin" in routes
    assert "/health" in routes
