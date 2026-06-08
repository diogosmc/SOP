"""Debug endpoints (development)."""

from typing import Any

from fastapi import APIRouter, Request
from starlette.routing import Route

from app.core.config import get_settings
from app.core.schemas import APIResponse

router = APIRouter(prefix="/debug", tags=["debug"])


def _collect_routes(app) -> list[str]:
    paths: set[str] = set()
    for route in app.routes:
        if isinstance(route, Route) and route.path:
            paths.add(route.path)
    return sorted(paths)


@router.get("/routes")
async def list_routes(request: Request) -> APIResponse[list[str]]:
    """List registered HTTP routes (no sensitive data)."""
    settings = get_settings()
    if not settings.debug and settings.app_env.lower() not in ("development", "dev", "local"):
        return APIResponse(data=[])

    app = request.app
    return APIResponse(data=_collect_routes(app))
