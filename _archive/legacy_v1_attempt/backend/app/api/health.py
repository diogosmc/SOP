"""Health check endpoints."""

from typing import Any, Dict

import httpx
from fastapi import APIRouter

from app.core.config import get_settings
from app.core.schemas import APIResponse
from app.db.redis import check_redis
from app.db.session import check_database

router = APIRouter(tags=["health"])


async def check_ollama() -> bool:
    settings = get_settings()
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.ollama_base_url}/api/tags")
            return resp.status_code == 200
    except Exception:
        return False


@router.get("/health")
async def root_health() -> APIResponse[Dict[str, Any]]:
    return APIResponse(data={"status": "ok", "service": "copiloto"})


@router.get("/api/v1/health")
async def detailed_health() -> APIResponse[Dict[str, bool]]:
    db_ok = await check_database()
    redis_ok = await check_redis()
    ollama_ok = await check_ollama()
    return APIResponse(
        data={
            "api": True,
            "database": db_ok,
            "redis": redis_ok,
            "ollama": ollama_ok,
            "telegram": get_settings().telegram_enabled,
        }
    )
