"""AI module API routes."""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.ai.ollama import OllamaError, check_ollama_health, list_models
from app.ai.router import choose_model
from app.core.config import get_settings
from app.core.schemas import APIResponse

router = APIRouter(prefix="/ai", tags=["ai"])


class RouteTestRequest(BaseModel):
    message: str = Field(min_length=1)
    force_deep: bool = False
    force_fast: bool = False


@router.get("/health")
async def ai_health() -> APIResponse[dict[str, Any]]:
    """Check Ollama connectivity and list available models."""
    settings = get_settings()
    data: dict[str, Any] = {
        "ollama": False,
        "base_url": settings.ollama_base_url,
        "models": [],
    }

    healthy = await check_ollama_health()
    if not healthy:
        data["error"] = "Ollama is unreachable"
        return APIResponse(data=data)

    data["ollama"] = True
    try:
        data["models"] = await list_models()
    except OllamaError as exc:
        data["error"] = str(exc)

    return APIResponse(data=data)


@router.get("/models")
async def ai_models() -> APIResponse[dict[str, Any]]:
    """List models installed in Ollama."""
    settings = get_settings()
    if not await check_ollama_health():
        return APIResponse(
            data={
                "ollama": False,
                "base_url": settings.ollama_base_url,
                "models": [],
                "error": "Ollama is unreachable",
            }
        )

    try:
        models = await list_models()
    except OllamaError as exc:
        return APIResponse(
            data={
                "ollama": False,
                "base_url": settings.ollama_base_url,
                "models": [],
                "error": str(exc),
            }
        )

    return APIResponse(
        data={
            "ollama": True,
            "base_url": settings.ollama_base_url,
            "models": models,
        }
    )


@router.post("/route-test")
async def ai_route_test(body: RouteTestRequest) -> APIResponse[dict[str, str]]:
    """Test model routing logic without calling Ollama."""
    return APIResponse(
        data=choose_model(
            body.message,
            force_deep=body.force_deep,
            force_fast=body.force_fast,
        )
    )
