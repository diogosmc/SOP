"""Telegram message formatting helpers."""

from __future__ import annotations


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
    """Format a short Telegram reply in Portuguese."""
    return truncate_paragraphs(text)[:4000]


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
