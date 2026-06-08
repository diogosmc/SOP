"""CRUD and feature tests for study module."""

from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.asyncio
async def test_crud_subjects(client: AsyncClient) -> None:
    create = await client.post(
        "/api/v1/study/subjects",
        json={"name": "Matemática", "description": "Álgebra", "color": "#8b5cf6"},
    )
    assert create.status_code == 200
    subject_id = create.json()["data"]["id"]

    get_resp = await client.get(f"/api/v1/study/subjects/{subject_id}")
    assert get_resp.status_code == 200

    update = await client.patch(
        f"/api/v1/study/subjects/{subject_id}",
        json={"name": "Mat Avançada"},
    )
    assert update.status_code == 200
    assert update.json()["data"]["name"] == "Mat Avançada"

    listing = await client.get("/api/v1/study/subjects")
    assert listing.status_code == 200
    assert listing.json()["data"]["total"] >= 1

    delete = await client.delete(f"/api/v1/study/subjects/{subject_id}")
    assert delete.status_code == 200


@pytest.mark.integration
@pytest.mark.asyncio
async def test_crud_topics(client: AsyncClient) -> None:
    subject = await client.post("/api/v1/study/subjects", json={"name": "Física"})
    subject_id = subject.json()["data"]["id"]

    create = await client.post(
        "/api/v1/study/topics",
        json={
            "subject_id": subject_id,
            "title": "Lei de Ohm",
            "content": "V = R * I",
            "status": "in_progress",
            "difficulty": 4,
        },
    )
    assert create.status_code == 200
    topic_id = create.json()["data"]["id"]

    filtered = await client.get(
        "/api/v1/study/topics",
        params={"subject_id": subject_id, "status": "in_progress"},
    )
    assert filtered.status_code == 200
    assert all(item["status"] == "in_progress" for item in filtered.json()["data"]["items"])

    update = await client.patch(
        f"/api/v1/study/topics/{topic_id}",
        json={"status": "mastered"},
    )
    assert update.status_code == 200
    assert update.json()["data"]["status"] == "mastered"

    delete = await client.delete(f"/api/v1/study/topics/{topic_id}")
    assert delete.status_code == 200


@pytest.mark.integration
@pytest.mark.asyncio
async def test_crud_flashcards_and_review(client: AsyncClient) -> None:
    subject = await client.post("/api/v1/study/subjects", json={"name": "História"})
    subject_id = subject.json()["data"]["id"]
    topic = await client.post(
        "/api/v1/study/topics",
        json={"subject_id": subject_id, "title": "Brasil Colônia"},
    )
    topic_id = topic.json()["data"]["id"]

    create = await client.post(
        "/api/v1/study/flashcards",
        json={"topic_id": topic_id, "front": "1500?", "back": "Descobrimento"},
    )
    assert create.status_code == 200
    card = create.json()["data"]
    card_id = card["id"]
    assert card["repetitions"] == 0

    review = await client.patch(
        f"/api/v1/study/flashcards/{card_id}/review",
        json={"rating": "good"},
    )
    assert review.status_code == 200
    reviewed = review.json()["data"]
    assert reviewed["repetitions"] == 1
    assert reviewed["interval_days"] >= 1
    assert reviewed["next_review"] is not None

    delete = await client.delete(f"/api/v1/study/flashcards/{card_id}")
    assert delete.status_code == 200


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_study_session(client: AsyncClient) -> None:
    subject = await client.post("/api/v1/study/subjects", json={"name": "Química"})
    subject_id = subject.json()["data"]["id"]

    response = await client.post(
        "/api/v1/study/sessions",
        json={
            "subject_id": subject_id,
            "duration_minutes": 45,
            "technique": "pomodoro",
            "notes": "Revisão orgânica",
        },
    )
    assert response.status_code == 200
    assert response.json()["data"]["duration_minutes"] == 45

    listing = await client.get("/api/v1/study/sessions")
    assert listing.status_code == 200
    assert listing.json()["data"]["total"] >= 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_study_summary(client: AsyncClient) -> None:
    subject = await client.post("/api/v1/study/subjects", json={"name": "Biologia"})
    subject_id = subject.json()["data"]["id"]
    await client.post(
        "/api/v1/study/topics",
        json={"subject_id": subject_id, "title": "Célula", "status": "in_progress"},
    )
    await client.post(
        "/api/v1/study/sessions",
        json={"subject_id": subject_id, "duration_minutes": 30},
    )

    response = await client.get("/api/v1/study/summary")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total_subjects"] >= 1
    assert data["total_topics"] >= 1
    assert data["topics_in_progress"] >= 1
    assert data["minutes_studied_today"] >= 30


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ai_plan_mocked(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    subject = await client.post("/api/v1/study/subjects", json={"name": "Redação"})
    subject_id = subject.json()["data"]["id"]
    topic = await client.post(
        "/api/v1/study/topics",
        json={
            "subject_id": subject_id,
            "title": "Dissertação",
            "content": "Introdução, desenvolvimento, conclusão",
        },
    )
    topic_id = topic.json()["data"]["id"]

    async def mock_ollama(messages, model=None, options=None):
        return {"message": {"content": "## Plano\n1. Ler proposta\n2. Esboço\n3. Revisão"}}

    monkeypatch.setattr("app.modules.study.service.ollama_chat", AsyncMock(side_effect=mock_ollama))

    response = await client.post(f"/api/v1/study/topics/{topic_id}/ai-plan")
    assert response.status_code == 200
    plan = response.json()["data"]["plan"]
    assert "Plano" in plan


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ai_plan_offline(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    subject = await client.post("/api/v1/study/subjects", json={"name": "Geografia"})
    subject_id = subject.json()["data"]["id"]
    topic = await client.post(
        "/api/v1/study/topics",
        json={"subject_id": subject_id, "title": "Clima"},
    )
    topic_id = topic.json()["data"]["id"]

    from app.ai.ollama import OllamaError

    async def fail_ollama(*args, **kwargs):
        raise OllamaError("offline")

    monkeypatch.setattr("app.modules.study.service.ollama_chat", fail_ollama)

    response = await client.post(f"/api/v1/study/topics/{topic_id}/ai-plan")
    assert response.status_code == 503
