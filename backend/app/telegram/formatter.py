"""Telegram message formatting helpers."""

from __future__ import annotations

import html
import re
from typing import Any

_BOLD_RE = re.compile(r"\*\*(.+?)\*\*", re.DOTALL)
_ITALIC_RE = re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", re.DOTALL)
_CODE_RE = re.compile(r"`([^`]+)`")


def truncate_paragraphs(text: str, max_paragraphs: int = 3) -> str:
    """Limit reply length to at most N paragraphs."""
    normalized = text.strip()
    if not normalized:
        return ""
    paragraphs = [part.strip() for part in normalized.split("\n\n") if part.strip()]
    if len(paragraphs) <= max_paragraphs:
        return normalized
    return "\n\n".join(paragraphs[:max_paragraphs])


def format_telegram_reply(text: str) -> str:
    """Plain Telegram reply text (no parse mode)."""
    return truncate_paragraphs(text)[:4000]


def markdown_to_telegram_html(text: str) -> str:
    """Convert simple **bold**, *italic* and `code` to Telegram HTML."""
    if not text:
        return ""

    placeholders: list[str] = []

    def _stash(match: re.Match[str], tag: str) -> str:
        inner = html.escape(match.group(1), quote=False)
        token = f"\x00FMT{len(placeholders)}\x00"
        placeholders.append(f"<{tag}>{inner}</{tag}>")
        return token

    working = html.escape(text, quote=False)
    working = _BOLD_RE.sub(lambda m: _stash(m, "b"), working)
    working = _ITALIC_RE.sub(lambda m: _stash(m, "i"), working)
    working = _CODE_RE.sub(lambda m: _stash(m, "code"), working)

    for idx, replacement in enumerate(placeholders):
        working = working.replace(f"\x00FMT{idx}\x00", replacement)
    return working


def telegram_reply_kwargs(text: str, *, html: bool = True) -> dict[str, Any]:
    """Build kwargs for reply_text / edit_text with optional HTML formatting."""
    plain = format_telegram_reply(text)
    if not html:
        return {"text": plain}
    return {"text": markdown_to_telegram_html(plain), "parse_mode": "HTML"}


async def reply_telegram(message: Any, text: str, *, html: bool = True) -> Any:
    """Send reply; fall back to plain text if HTML parsing fails."""
    kwargs = telegram_reply_kwargs(text, html=html)
    try:
        return await message.reply_text(**kwargs)
    except Exception:
        return await message.reply_text(format_telegram_reply(text))


async def edit_telegram(message: Any, text: str, *, html: bool = True) -> None:
    """Edit message; fall back to plain text if HTML parsing fails."""
    kwargs = telegram_reply_kwargs(text, html=html)
    try:
        await message.edit_text(**kwargs)
    except Exception:
        await message.edit_text(format_telegram_reply(text))


def format_status_message(
    *,
    api_ok: bool,
    ollama_ok: bool,
    memory_count: int,
    pending_tasks: int,
) -> str:
    api_label = "ok" if api_ok else "indisponível"
    ollama_label = "online" if ollama_ok else "offline"
    return format_telegram_reply(
        f"Status do Copiloto:\n"
        f"• API: {api_label}\n"
        f"• Ollama: {ollama_label}\n"
        f"• Memórias: {memory_count}\n"
        f"• Tarefas pendentes: {pending_tasks}"
    )


def format_debug_message(
    *,
    version: str,
    api_ok: bool,
    db_ok: bool,
    redis_ok: bool,
    ollama_ok: bool,
    telegram_user_ok: bool,
    default_user_ok: bool,
    default_user_name: str,
    memory_count: int,
    pending_tasks: int,
) -> str:
    return format_telegram_reply(
        f"Debug COPILOTO v{version}\n"
        f"• API: {'ok' if api_ok else 'erro'}\n"
        f"• DB: {'ok' if db_ok else 'erro'}\n"
        f"• Redis: {'ok' if redis_ok else 'offline'}\n"
        f"• Ollama: {'online' if ollama_ok else 'offline'}\n"
        f"• Telegram user autorizado: {'sim' if telegram_user_ok else 'não'}\n"
        f"• Default user: {'ok' if default_user_ok else 'ausente'} ({default_user_name})\n"
        f"• Memórias: {memory_count}\n"
        f"• Tarefas pendentes: {pending_tasks}"
    )


def format_journal_summary(journal) -> str:
    """Format today's journal for /resumo."""
    parts: list[str] = ["Resumo de hoje:"]
    if journal.summary:
        parts.append(f"Geral: {journal.summary}")
    if journal.mood_score is not None:
        parts.append(f"Humor: {journal.mood_score}/10")
    if journal.study_summary:
        parts.append(f"Estudos: {journal.study_summary}")
    if journal.workout_summary:
        parts.append(f"Treino: {journal.workout_summary}")
    if journal.finance_summary:
        parts.append(f"Finanças: {journal.finance_summary}")
    if journal.habit_summary:
        parts.append(f"Hábitos: {journal.habit_summary}")
    if len(parts) == 1:
        parts.append("Ainda não há registros hoje. Converse comigo naturalmente.")
    return format_telegram_reply("\n\n".join(parts))
