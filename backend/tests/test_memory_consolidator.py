"""Tests for memory consolidation."""

import pytest
from sqlalchemy import func, select

from app.ai.memory.consolidator import consolidate_memories
from app.modules.memory.models import AIMemory, MemoryType


@pytest.mark.integration
@pytest.mark.asyncio
async def test_consolidator_avoids_duplication(db_session, default_user_id) -> None:
    first = await consolidate_memories(
        db_session,
        default_user_id,
        [
            {
                "type": "goal",
                "content": "Objetivo do usuário: passar ou alcançar Medicina",
                "importance": 8,
                "confidence": 0.85,
                "source": "chat",
            }
        ],
    )
    assert len(first) == 1

    second = await consolidate_memories(
        db_session,
        default_user_id,
        [
            {
                "type": "goal",
                "content": "Objetivo do usuário: passar ou alcançar medicina na faculdade",
                "importance": 9,
                "confidence": 0.9,
                "source": "chat",
            }
        ],
    )
    assert len(second) == 1
    assert second[0].id == first[0].id
    assert second[0].importance == 9

    count_result = await db_session.execute(
        select(func.count())
        .select_from(AIMemory)
        .where(AIMemory.user_id == default_user_id, AIMemory.type == MemoryType.GOAL)
    )
    assert count_result.scalar_one() == 1
