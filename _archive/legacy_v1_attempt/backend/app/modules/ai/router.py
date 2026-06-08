"""AI module API routes."""

from typing import Any

from fastapi import APIRouter

from app.ai.ollama import OllamaClient
from app.core.schemas import APIResponse

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/health")
async def ai_health() -> APIResponse[dict[str, Any]]:
    """Check Ollama connectivity and list available models."""
    client = OllamaClient()
    healthy = await client.health()
    models: list[dict[str, Any]] = []

    if healthy:
        models = await client.list_models()

    return APIResponse(
        data={
            "healthy": healthy,
            "models": models,
        }
    )
