"""CRUD tests for notes."""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_note(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/notes",
        json={
            "title": "My note",
            "content": "Some content",
            "tags": ["work", "ideas"],
            "favorite": True,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["title"] == "My note"
    assert body["data"]["tags"] == ["work", "ideas"]
    assert body["data"]["favorite"] is True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_notes_with_filters(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/notes",
        json={"title": "Fav note", "tags": ["personal"], "favorite": True},
    )
    await client.post(
        "/api/v1/notes",
        json={"title": "Archived note", "archived": True},
    )
    await client.post(
        "/api/v1/notes",
        json={"title": "Work note", "tags": ["work"]},
    )

    fav_resp = await client.get("/api/v1/notes", params={"favorite": True})
    assert fav_resp.status_code == 200
    assert all(n["favorite"] for n in fav_resp.json()["data"]["items"])

    tag_resp = await client.get("/api/v1/notes", params={"tag": "work"})
    assert tag_resp.status_code == 200
    assert all("work" in (n["tags"] or []) for n in tag_resp.json()["data"]["items"])

    archived_resp = await client.get("/api/v1/notes", params={"archived": True})
    assert archived_resp.status_code == 200
    assert all(n["archived"] for n in archived_resp.json()["data"]["items"])


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_notes_pagination(client: AsyncClient) -> None:
    for i in range(3):
        await client.post("/api/v1/notes", json={"title": f"Note {i}"})

    response = await client.get("/api/v1/notes", params={"page": 1, "page_size": 2})
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data["items"]) == 2
    assert data["total"] >= 3


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_notes(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/notes",
        json={"title": "Python tips", "content": "Use type hints"},
    )
    await client.post(
        "/api/v1/notes",
        json={"title": "Shopping", "content": "Buy milk"},
    )

    response = await client.get("/api/v1/notes/search", params={"q": "python"})
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["total"] >= 1
    assert any("Python" in item["title"] for item in body["data"]["items"])


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_update_delete_note(client: AsyncClient) -> None:
    create_resp = await client.post(
        "/api/v1/notes", json={"title": "Draft", "content": "Initial"}
    )
    note_id = create_resp.json()["data"]["id"]

    get_resp = await client.get(f"/api/v1/notes/{note_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["title"] == "Draft"

    update_resp = await client.patch(
        f"/api/v1/notes/{note_id}",
        json={"title": "Final", "content": "Updated content", "archived": True},
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()["data"]
    assert updated["title"] == "Final"
    assert updated["archived"] is True

    delete_resp = await client.delete(f"/api/v1/notes/{note_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["success"] is True

    not_found = await client.get(f"/api/v1/notes/{note_id}")
    assert not_found.status_code == 404
    assert not_found.json()["success"] is False


@pytest.mark.integration
@pytest.mark.asyncio
async def test_note_response_wrapper(client: AsyncClient) -> None:
    response = await client.post("/api/v1/notes", json={"title": "Wrapper note"})
    body = response.json()
    assert body["success"] is True
    assert "data" in body
    assert "id" in body["data"]
