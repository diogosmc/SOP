"""CRUD tests for memory API."""

import pytest
from httpx import AsyncClient

from app.modules.memory.models import MemoryType


@pytest.mark.integration
@pytest.mark.asyncio
async def test_memory_crud(client: AsyncClient) -> None:
    create_resp = await client.post(
        "/api/v1/memory/memories",
        json={
            "type": MemoryType.GOAL.value,
            "content": "Objetivo: aprender Python",
            "importance": 7,
            "confidence": 0.9,
            "source": "manual",
        },
    )
    assert create_resp.status_code == 200
    memory = create_resp.json()["data"]
    memory_id = memory["id"]

    list_resp = await client.get("/api/v1/memory/memories")
    assert list_resp.status_code == 200
    assert any(item["id"] == memory_id for item in list_resp.json()["data"]["items"])

    update_resp = await client.put(
        f"/api/v1/memory/memories/{memory_id}",
        json={"content": "Objetivo: dominar Python", "importance": 8},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["data"]["content"] == "Objetivo: dominar Python"
    assert update_resp.json()["data"]["importance"] == 8

    delete_resp = await client.delete(f"/api/v1/memory/memories/{memory_id}")
    assert delete_resp.status_code == 200


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ai_notes_crud(client: AsyncClient) -> None:
    create_resp = await client.post(
        "/api/v1/memory/notes",
        json={
            "title": "Insight interno",
            "content": "Usuário prefere estudar à noite",
            "category": "study",
            "importance": 6,
        },
    )
    assert create_resp.status_code == 200
    note_id = create_resp.json()["data"]["id"]

    list_resp = await client.get("/api/v1/memory/notes")
    assert list_resp.status_code == 200
    assert any(item["id"] == note_id for item in list_resp.json()["data"]["items"])

    delete_resp = await client.delete(f"/api/v1/memory/notes/{note_id}")
    assert delete_resp.status_code == 200
