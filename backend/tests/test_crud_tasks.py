"""CRUD tests for tasks."""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_task(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/tasks",
        json={"title": "Test task", "description": "Details", "status": "pending"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["title"] == "Test task"
    assert body["data"]["status"] == "pending"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_tasks_with_pagination(client: AsyncClient) -> None:
    for i in range(3):
        await client.post("/api/v1/tasks", json={"title": f"Task {i}"})

    response = await client.get("/api/v1/tasks", params={"page": 1, "page_size": 2})
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert data["total"] >= 3
    assert data["pages"] >= 2


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_tasks_filter_by_status(client: AsyncClient) -> None:
    await client.post("/api/v1/tasks", json={"title": "Pending task", "status": "pending"})
    await client.post(
        "/api/v1/tasks", json={"title": "Done task", "status": "completed"}
    )

    response = await client.get("/api/v1/tasks", params={"status": "completed"})
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert all(item["status"] == "completed" for item in body["data"]["items"])


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_update_delete_task(client: AsyncClient) -> None:
    create_resp = await client.post(
        "/api/v1/tasks", json={"title": "Original", "priority": "low"}
    )
    task_id = create_resp.json()["data"]["id"]

    get_resp = await client.get(f"/api/v1/tasks/{task_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["title"] == "Original"

    update_resp = await client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"title": "Updated", "status": "in_progress", "priority": "high"},
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()["data"]
    assert updated["title"] == "Updated"
    assert updated["status"] == "in_progress"
    assert updated["priority"] == "high"

    delete_resp = await client.delete(f"/api/v1/tasks/{task_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["success"] is True

    not_found = await client.get(f"/api/v1/tasks/{task_id}")
    assert not_found.status_code == 404
    error = not_found.json()
    assert error["success"] is False
    assert "message" in error["error"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_task_response_wrapper(client: AsyncClient) -> None:
    response = await client.post("/api/v1/tasks", json={"title": "Wrapper test"})
    body = response.json()
    assert "success" in body
    assert "data" in body
    assert body["success"] is True
    assert "id" in body["data"]
    assert "created_at" in body["data"]
