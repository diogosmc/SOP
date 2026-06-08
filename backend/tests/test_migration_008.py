"""Migration 008 user_state tests."""

import pytest
from sqlalchemy import inspect


@pytest.mark.integration
@pytest.mark.asyncio
async def test_user_state_table_exists(db_session) -> None:
    conn = await db_session.connection()
    def _check(sync_conn):
        return inspect(sync_conn).has_table("user_state")

    exists = await conn.run_sync(_check)
    assert exists
