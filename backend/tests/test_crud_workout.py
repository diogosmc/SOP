"""CRUD and feature tests for workout module."""

from datetime import date

import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.asyncio
async def test_upsert_and_get_profile(client: AsyncClient) -> None:
    put_resp = await client.put(
        "/api/v1/workout/profile",
        json={"height_cm": "175.5", "weight_kg": "72.0", "objective": "strength", "notes": "Test"},
    )
    assert put_resp.status_code == 200
    data = put_resp.json()["data"]
    assert data["objective"] == "strength"

    get_resp = await client.get("/api/v1/workout/profile")
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["height_cm"] == "175.5"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_crud_exercises(client: AsyncClient) -> None:
    create = await client.post(
        "/api/v1/workout/exercises",
        json={"name": "Supino reto", "muscle_group": "Peito", "exercise_type": "strength"},
    )
    assert create.status_code == 200
    ex_id = create.json()["data"]["id"]

    update = await client.patch(
        f"/api/v1/workout/exercises/{ex_id}",
        json={"name": "Supino inclinado"},
    )
    assert update.status_code == 200

    listing = await client.get("/api/v1/workout/exercises")
    assert listing.status_code == 200
    assert listing.json()["data"]["total"] >= 1

    delete = await client.delete(f"/api/v1/workout/exercises/{ex_id}")
    assert delete.status_code == 200


@pytest.mark.integration
@pytest.mark.asyncio
async def test_crud_plans_and_add_exercise(client: AsyncClient) -> None:
    exercise = await client.post(
        "/api/v1/workout/exercises",
        json={"name": "Agachamento", "muscle_group": "Pernas"},
    )
    ex_id = exercise.json()["data"]["id"]

    plan = await client.post(
        "/api/v1/workout/plans",
        json={"name": "ABC", "description": "Push pull legs", "active": True},
    )
    assert plan.status_code == 200
    plan_id = plan.json()["data"]["id"]

    add = await client.post(
        f"/api/v1/workout/plans/{plan_id}/exercises",
        json={
            "exercise_id": ex_id,
            "day_label": "A",
            "sets": 3,
            "reps": "8-12",
            "target_load_kg": "60",
            "order_index": 1,
        },
    )
    assert add.status_code == 200

    detail = await client.get(f"/api/v1/workout/plans/{plan_id}")
    assert detail.status_code == 200
    assert len(detail.json()["data"]["exercises"]) == 1

    plan_ex_id = detail.json()["data"]["exercises"][0]["id"]
    remove = await client.delete(f"/api/v1/workout/plans/{plan_id}/exercises/{plan_ex_id}")
    assert remove.status_code == 200


@pytest.mark.integration
@pytest.mark.asyncio
async def test_workout_log_and_sets(client: AsyncClient) -> None:
    exercise = await client.post(
        "/api/v1/workout/exercises",
        json={"name": "Remada", "muscle_group": "Costas"},
    )
    ex_id = exercise.json()["data"]["id"]

    log = await client.post(
        "/api/v1/workout/logs",
        json={"date": str(date.today()), "duration_minutes": 50, "completed": True},
    )
    assert log.status_code == 200
    log_id = log.json()["data"]["id"]

    set_resp = await client.post(
        f"/api/v1/workout/logs/{log_id}/sets",
        json={"exercise_id": ex_id, "set_number": 1, "reps": 10, "load_kg": "40"},
    )
    assert set_resp.status_code == 200

    detail = await client.get(f"/api/v1/workout/logs/{log_id}")
    assert detail.status_code == 200
    assert len(detail.json()["data"]["sets"]) == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_workout_summary(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/workout/logs",
        json={"date": str(date.today()), "duration_minutes": 30, "completed": True},
    )

    response = await client.get("/api/v1/workout/summary")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["workouts_this_week"] >= 1
    assert data["last_workout_date"] == str(date.today())


@pytest.mark.integration
@pytest.mark.asyncio
async def test_workout_progression(client: AsyncClient) -> None:
    exercise = await client.post(
        "/api/v1/workout/exercises",
        json={"name": "Leg press", "muscle_group": "Pernas"},
    )
    ex_id = exercise.json()["data"]["id"]
    log = await client.post(
        "/api/v1/workout/logs",
        json={"date": str(date.today()), "completed": True},
    )
    log_id = log.json()["data"]["id"]
    await client.post(
        f"/api/v1/workout/logs/{log_id}/sets",
        json={"exercise_id": ex_id, "set_number": 1, "reps": 12, "load_kg": "100"},
    )

    response = await client.get("/api/v1/workout/progression", params={"exercise_id": ex_id})
    assert response.status_code == 200
    points = response.json()["data"]
    assert len(points) >= 1
    assert points[0]["load_kg"] == "100.00" or float(points[0]["load_kg"]) == 100.0
