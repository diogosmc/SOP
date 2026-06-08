"""Debug endpoints for Conversation Brain."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.brain.benchmarks import DEFAULT_BENCHMARK_MESSAGES, run_benchmark, save_benchmark_report
from app.brain.conversation_manager import process_message
from app.brain.schemas import BrainResult
from app.brain.state_manager import get_or_create_user_state
from app.core.deps import get_current_user_id, get_db
from app.core.schemas import APIResponse

router = APIRouter(prefix="/brain", tags=["brain"])


class BrainTestMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    allow_llm: bool = True
    allow_tools: bool = True


@router.post("/test-message", response_model=APIResponse[BrainResult])
async def test_message(
    payload: BrainTestMessageRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[BrainResult]:
    result = await process_message(
        db,
        user_id,
        payload.message,
        origin="api",
        allow_llm=payload.allow_llm,
        allow_tools=payload.allow_tools,
    )
    await db.commit()
    return APIResponse(data=result)


@router.get("/state")
async def get_brain_state(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[dict]:
    state = await get_or_create_user_state(db, user_id)
    await db.commit()
    return APIResponse(data=state.model_dump())


@router.post("/benchmark")
async def run_brain_benchmark(
    allow_llm: bool = Query(False),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[dict]:
    results = await run_benchmark(
        db,
        user_id,
        DEFAULT_BENCHMARK_MESSAGES,
        allow_llm=allow_llm,
    )
    from pathlib import Path

    report_path = Path(__file__).resolve().parents[2] / "reports" / "telegram_brain_benchmark.json"
    save_benchmark_report(results, report_path)
    return APIResponse(
        data={
            "count": len(results),
            "report_path": str(report_path),
            "results": [item.model_dump() for item in results],
        }
    )
