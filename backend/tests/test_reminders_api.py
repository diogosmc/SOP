"""CRUD and service tests for reminders."""

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient

from app.modules.reminders.models import ReminderChannel, ReminderStatus
from app.modules.reminders.schemas import ReminderCreate
from app.modules.reminders.service import ReminderService


@pytest.mark.integration
@pytest.mark.asyncio
async def test_reminder_crud(client: AsyncClient) -> None:
    remind_at = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
    create_resp = await client.post(
        "/api/v1/reminders",
        json={
            "title": "Revisar física",
            "description": "Capítulo 3",
            "remind_at": remind_at,
            "channel": ReminderChannel.TELEGRAM.value,
        },
    )
    assert create_resp.status_code == 200
    reminder = create_resp.json()["data"]
    reminder_id = reminder["id"]
    assert reminder["status"] == ReminderStatus.PENDING.value

    list_resp = await client.get("/api/v1/reminders")
    assert list_resp.status_code == 200
    assert any(item["id"] == reminder_id for item in list_resp.json()["data"]["items"])

    update_resp = await client.put(
        f"/api/v1/reminders/{reminder_id}",
        json={"title": "Revisar física amanhã"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["data"]["title"] == "Revisar física amanhã"

    delete_resp = await client.delete(f"/api/v1/reminders/{reminder_id}")
    assert delete_resp.status_code == 200


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_due_reminders(db_session, default_user_id) -> None:
    service = ReminderService(db_session)
    past = datetime.now(timezone.utc) - timedelta(minutes=5)
    future = datetime.now(timezone.utc) + timedelta(hours=1)

    due = await service.create(
        default_user_id,
        ReminderCreate(title="Due now", remind_at=past),
    )
    await service.create(
        default_user_id,
        ReminderCreate(title="Later", remind_at=future),
    )

    due_list = await service.get_due_reminders(default_user_id)
    assert any(item.id == due.id for item in due_list)
    assert all(item.status == ReminderStatus.PENDING for item in due_list)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_mark_reminder_sent(db_session, default_user_id) -> None:
    service = ReminderService(db_session)
    reminder = await service.create(
        default_user_id,
        ReminderCreate(
            title="Send me",
            remind_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        ),
    )
    updated = await service.mark_sent(reminder.id, default_user_id)
    assert updated.status == ReminderStatus.SENT


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cancel_reminder(client: AsyncClient) -> None:
    remind_at = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    create_resp = await client.post(
        "/api/v1/reminders",
        json={"title": "Cancelável", "remind_at": remind_at},
    )
    reminder_id = create_resp.json()["data"]["id"]

    cancel_resp = await client.post(f"/api/v1/reminders/{reminder_id}/cancel")
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["data"]["status"] == ReminderStatus.CANCELLED.value
