"""Tests for AI API router."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client() -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_ai_health_does_not_break(client: AsyncClient) -> None:
    response = await client.get("/api/v1/ai/health")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert "ollama" in data
    assert "base_url" in data
    assert isinstance(data["ollama"], bool)
    assert isinstance(data["models"], list)
    if not data["ollama"]:
        assert data["models"] == []
        assert "error" in data


@pytest.mark.asyncio
async def test_ai_models_offline_does_not_break(client: AsyncClient) -> None:
    response = await client.get("/api/v1/ai/models")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "models" in body["data"]


@pytest.mark.asyncio
async def test_route_test_short_message_uses_fast_model(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/ai/route-test",
        json={"message": "listar tarefas"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert data["complexity"] == "simple"
    assert "llama" in data["model"] or "3b" in data["model"]
    assert "reason" in data


@pytest.mark.asyncio
async def test_route_test_complex_message_uses_main_model(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/ai/route-test",
        json={"message": "Preciso de uma análise financeira detalhada do mês"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["complexity"] == "complex"
    assert "mistral" in data["model"]


@pytest.mark.asyncio
async def test_route_test_force_flags(client: AsyncClient) -> None:
    fast_resp = await client.post(
        "/api/v1/ai/route-test",
        json={"message": "análise complexa", "force_fast": True},
    )
    deep_resp = await client.post(
        "/api/v1/ai/route-test",
        json={"message": "ok", "force_deep": True},
    )

    assert "llama" in fast_resp.json()["data"]["model"]
    assert "mistral" in deep_resp.json()["data"]["model"]


@pytest.mark.asyncio
async def test_choose_model_without_ollama_dependency() -> None:
    from app.ai.router import choose_model

    result = choose_model("planejamento de estudos para a semana")
    assert result["complexity"] == "complex"
    assert result["model"]
    assert result["reason"]
