"""Model selection helpers for Ollama."""

from typing import Optional, Union

from app.core.config import get_settings
from app.modules.chat.models import ChatMode

_FAST_COMPLEXITY = frozenset({"low", "fast", "simple", "quick", "command"})
_MAIN_COMPLEXITY = frozenset(
    {"high", "main", "complex", "analysis", "planning", "rag", "report", "medium"}
)
_FAST_MODES = frozenset({ChatMode.GENERAL, ChatMode.PRODUCTIVITY})


def select_model(
    complexity: str = "low",
    *,
    mode: Optional[Union[ChatMode, str]] = None,
    message: Optional[str] = None,
) -> str:
    """Choose the fast or main Ollama model based on complexity, mode, or message length."""
    settings = get_settings()

    if mode is not None:
        chat_mode = mode if isinstance(mode, ChatMode) else ChatMode(mode)
        if chat_mode in _FAST_MODES and (message is None or len(message) < 200):
            return settings.ollama_fast_model
        if chat_mode in (ChatMode.STUDY, ChatMode.FINANCE):
            return settings.ollama_main_model

    if message and len(message) > 400:
        return settings.ollama_main_model

    normalized = complexity.lower().strip()
    if normalized in _FAST_COMPLEXITY:
        return settings.ollama_fast_model
    if normalized in _MAIN_COMPLEXITY:
        return settings.ollama_main_model

    return settings.ollama_fast_model