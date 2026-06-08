"""Reports module tests."""

from datetime import date
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.asyncio
async def test_daily_report(client: AsyncClient) -> None:
    response = await client.get("/api/v1/reports/daily")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "date" in data
    assert "tasks_completed" in data
    assert "tasks_pending" in data
    assert "study_minutes" in data
    assert "workout_completed" in data
    assert "balance" in data


@pytest.mark.integration
@pytest.mark.asyncio
async def test_weekly_report(client: AsyncClient) -> None:
    response = await client.get("/api/v1/reports/weekly")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "week_start" in data
    assert "week_end" in data
    assert "wins" in data
    assert "problems" in data
    assert "recommendations" in data
    assert isinstance(data["wins"], list)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_analytics_structure(client: AsyncClient) -> None:
    response = await client.get("/api/v1/reports/analytics")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "tasks_by_status" in data
    assert "finance_by_category" in data
    assert "study_minutes_by_day" in data
    assert "workouts_by_day" in data
    assert "habits" in data
    assert "memories_by_type" in data
    assert "active" in data["habits"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rule_insights(client: AsyncClient) -> None:
    for _ in range(12):
        await client.post(
            "/api/v1/tasks",
            json={"title": f"Tarefa pendente {_}", "status": "pending", "priority": "medium"},
        )

    response = await client.get("/api/v1/reports/insights")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["source"] == "rules"
    assert len(data["insights"]) >= 1
    assert any("tarefa" in i.lower() for i in data["insights"])


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rebuild_daily(client: AsyncClient) -> None:
    response = await client.post("/api/v1/reports/rebuild-daily")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["rebuilt"] is True
    assert "report" in data
    assert data["report"]["date"] == str(date.today())


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ai_insights_mocked(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    async def mock_ollama(messages, model=None, options=None):
        return {"message": {"content": '{"insights": ["Insight IA de teste."]}'}}

    monkeypatch.setattr("app.ai.analyst.ollama_chat", AsyncMock(side_effect=mock_ollama))

    response = await client.get("/api/v1/reports/insights", params={"use_ai": "true"})
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["ai_used"] is True
    assert data["source"] == "ai"
    assert "Insight IA" in data["insights"][0]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ai_insights_fallback_to_rules(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.ai.ollama import OllamaError
    from app.core.config import get_settings

    monkeypatch.setenv("CACHE_ENABLED", "false")
    get_settings.cache_clear()

    async def fail_ollama(*args, **kwargs):
        raise OllamaError("offline")

    monkeypatch.setattr("app.ai.analyst.ollama_chat", fail_ollama)

    response = await client.get("/api/v1/reports/insights", params={"use_ai": "true"})
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["ai_used"] is False
    assert data["source"] == "rules"
    assert len(data["insights"]) >= 1
