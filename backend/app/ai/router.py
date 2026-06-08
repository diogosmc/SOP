"""Model selection helpers for Ollama."""

from app.core.config import get_settings

_SIMPLE_COMMANDS = frozenset(
    {
        "ok",
        "sim",
        "não",
        "nao",
        "obrigado",
        "thanks",
        "listar",
        "list",
        "status",
        "help",
        "ajuda",
    }
)

_COMPLEX_KEYWORDS = frozenset(
    {
        "analis",
        "analysis",
        "analyze",
        "planej",
        "plan",
        "planning",
        "estudo",
        "study",
        "financ",
        "finance",
        "treino",
        "workout",
        "emocion",
        "emotional",
        "rag",
        "relatório",
        "relatorio",
        "report",
        "estratég",
        "strategy",
        "compar",
        "explain",
        "explic",
        "detalh",
        "detail",
    }
)

_SHORT_MESSAGE_LIMIT = 80
_LONG_MESSAGE_LIMIT = 400


def choose_model(
    message: str,
    force_deep: bool = False,
    force_fast: bool = False,
) -> dict[str, str]:
    """Choose fast or main Ollama model based on message content and flags."""
    settings = get_settings()
    normalized = message.strip().lower()

    if force_fast and force_deep:
        force_deep = False

    if force_fast:
        return {
            "model": settings.ollama_model_fast,
            "reason": "force_fast enabled",
            "complexity": "simple",
        }

    if force_deep:
        return {
            "model": settings.ollama_model_main,
            "reason": "force_deep enabled",
            "complexity": "complex",
        }

    if not normalized:
        return {
            "model": settings.ollama_model_fast,
            "reason": "empty message defaults to fast model",
            "complexity": "simple",
        }

    if normalized in _SIMPLE_COMMANDS:
        return {
            "model": settings.ollama_model_fast,
            "reason": "simple command detected",
            "complexity": "simple",
        }

    if any(keyword in normalized for keyword in _COMPLEX_KEYWORDS):
        return {
            "model": settings.ollama_model_main,
            "reason": "complex topic keyword detected",
            "complexity": "complex",
        }

    if len(normalized) > _LONG_MESSAGE_LIMIT:
        return {
            "model": settings.ollama_model_main,
            "reason": "long message requires deeper reasoning",
            "complexity": "complex",
        }

    if len(normalized) <= _SHORT_MESSAGE_LIMIT:
        return {
            "model": settings.ollama_model_fast,
            "reason": "short message defaults to fast model",
            "complexity": "simple",
        }

    return {
        "model": settings.ollama_model_fast,
        "reason": "default fast model for general messages",
        "complexity": "simple",
    }
