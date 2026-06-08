"""Health check endpoints."""

import asyncio
from typing import Any, Dict

from fastapi import APIRouter
from pydantic import BaseModel

from app.db.redis import check_redis_health
from app.db.session import check_database_health

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    success: bool = True
    data: Dict[str, Any]


@router.get("/health", response_model=HealthResponse)
async def root_health() -> HealthResponse:
    return HealthResponse(data={"status": "ok", "service": "copiloto"})


@router.get("/api/v1/health", response_model=HealthResponse)
async def detailed_health() -> HealthResponse:
    database_ok, redis_ok = await asyncio.gather(
        check_database_health(),
        check_redis_health(),
    )
    return HealthResponse(
        data={
            "api": True,
            "database": database_ok,
            "redis": redis_ok,
        }
    )
