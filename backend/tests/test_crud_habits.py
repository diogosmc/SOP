"""CRUD tests for habits."""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_habit(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/habits",
        json={"name": "Morning run", "type": "positive", "frequency": "daily"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["name"] == "Morning run"
    assert body["data"]["type"] == "positive"
    assert body["data"]["active"] is True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_habits_with_filters(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/habits", json={"name": "Active positive", "type": "positive"}
    )
    await client.post(
        "/api/v1/habits", json={"name": "Inactive negative", "type": "negative"}
    )
    create_resp = await client.post(
        "/api/v1/habits", json={"name": "To deactivate", "type": "positive"}
    )
    habit_id = create_resp.json()["data"]["id"]
    await client.patch(f"/api/v1/habits/{habit_id}", json={"active": False})

    active_resp = await client.get("/api/v1/habits", params={"active": True})
    assert active_resp.status_code == 200
    assert all(h["active"] for h in active_resp.json()["data"]["items"])

    type_resp = await client.get("/api/v1/habits", params={"type": "negative"})
    assert type_resp.status_code == 200
    assert all(h["type"] == "negative" for h in type_resp.json()["data"]["items"])


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_habits_pagination(client: AsyncClient) -> None:
    for i in range(3):
        await client.post(
            "/api/v1/habits", json={"name": f"Habit {i}", "type": "positive"}
        )

    response = await client.get("/api/v1/habits", params={"page": 1, "page_size": 2})
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data["items"]) == 2
    assert data["total"] >= 3


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_update_delete_habit(client: AsyncClient) -> None:
    create_resp = await client.post(
        "/api/v1/habits", json={"name": "Read", "type": "positive"}
    )
    habit_id = create_resp.json()["data"]["id"]

    get_resp = await client.get(f"/api/v1/habits/{habit_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["name"] == "Read"

    update_resp = await client.patch(
        f"/api/v1/habits/{habit_id}",
        json={"name": "Read books", "active": False},
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()["data"]
    assert updated["name"] == "Read books"
    assert updated["active"] is False

    delete_resp = await client.delete(f"/api/v1/habits/{habit_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["success"] is True

    not_found = await client.get(f"/api/v1/habits/{habit_id}")
    assert not_found.status_code == 404
    assert not_found.json()["success"] is False
