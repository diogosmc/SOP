"""Build structured tomorrow schedule replies from conversation context."""

from __future__ import annotations

import re

from app.brain.schemas import ConversationContext

_LIST_TOMORROW_RE = re.compile(
    r"(list(ar|e)|liste|me\s+lista|agenda|cronograma|hor[aá]rio).{0,50}(amanh|dia\s+de\s+amanh|tarefas)|"
    r"(amanh|dia\s+de\s+amanh).{0,50}(listar|liste|fazer|agenda|programa|tarefas)|"
    r"o\s+que\s+(eu\s+)?vou\s+fazer\s+amanh|"
    r"list(ar|e)\s+(minhas\s+)?tarefas\s+(para\s+)?amanh|"
    r"liste?\s+exatamente\s+(o\s+)?dia",
    re.IGNORECASE,
)

_TIME_RE = re.compile(r"\b(\d{1,2})[:h](\d{2})\b", re.IGNORECASE)

_DENY_AUTO_RE = re.compile(
    r"n[aã]o tenho auto|sem auto\s*escola|nao vou na auto|s[oó] na academia",
    re.IGNORECASE,
)


def is_tomorrow_list_request(message: str) -> bool:
    return bool(_LIST_TOMORROW_RE.search(message.strip()))


def _user_text_blob(context: ConversationContext) -> str:
    parts = [context.message]
    for item in context.recent_messages:
        if item.get("role") == "user":
            parts.append(item.get("content", ""))
    return " ".join(parts).lower()


def _find_time(text: str, hour: int, minute: int) -> str | None:
    patterns = (
        f"{hour:02d}:{minute:02d}",
        f"{hour}:{minute:02d}",
        f"{hour}h{minute:02d}",
        f"{hour}h",
    )
    for p in patterns:
        if p in text:
            return f"{hour:02d}:{minute:02d}"
    return None


def _extract_known_blocks(text: str) -> list[tuple[str, str]]:
    """Return (sort_key, line) pairs for a chronological day list."""
    blocks: list[tuple[str, str]] = []
    deny_auto = bool(_DENY_AUTO_RE.search(text))

    wake = _find_time(text, 6, 20) or ("06:20" if re.search(r"06:20|6:20|6h20", text) else None)
    if wake or re.search(r"acordar|alarme|levantar", text):
        blocks.append((wake or "06:00", f"**{wake or '06:20'}** — Acordar (alarme)"))

    work_start = _find_time(text, 7, 40)
    work_end = _find_time(text, 17, 40)
    if work_start or re.search(r"\btrabalh", text):
        if work_start and work_end:
            blocks.append(
                (work_start, f"**{work_start}–{work_end}** — Trabalho")
            )
        elif work_start:
            blocks.append((work_start, f"**{work_start}** — Trabalho"))
        else:
            blocks.append(("07:40", "**Manhã** — Trabalho"))

    if re.search(r"\bacademia\b", text) and not deny_auto:
        blocks.append(("18:00", "**Noite** — Academia"))
    elif deny_auto and re.search(r"\bacademia\b", text):
        blocks.append(("18:00", "**Noite** — Academia (sem autoescola)"))

    if re.search(r"\bauto\s*escola\b|\bautoescola\b", text) and not deny_auto:
        blocks.append(("08:00", "**08:00** — Autoescola"))

    return blocks


def build_tomorrow_schedule_reply(context: ConversationContext) -> str:
    """Structured day list from user-stated facts + pending items."""
    text = _user_text_blob(context)
    blocks = _extract_known_blocks(text)

    extras: list[str] = []
    seen_extra: set[str] = set()
    deny_auto = bool(_DENY_AUTO_RE.search(text))

    for reminder in context.upcoming_reminders[:5]:
        label = reminder.strip()
        if deny_auto and "autoescola" in label.lower():
            continue
        key = label.lower()
        if key in seen_extra:
            continue
        seen_extra.add(key)
        extras.append(f"• {label}")

    for task in context.pending_tasks[:5]:
        label = task.strip()
        key = label.lower()
        if key in seen_extra:
            continue
        seen_extra.add(key)
        extras.append(f"• {label}")

    if not blocks and not extras:
        return (
            "Ainda não tenho sua rotina de amanhã montada.\n\n"
            "Me conta em uma mensagem: que horas acorda, horário do trabalho "
            "e o que mais entra no dia (academia, faculdade, etc.) que eu listo certinho."
        )

    lines = ["**Amanhã — seu dia:**", ""]
    seen: set[str] = set()
    idx = 1
    for _sort, line in sorted(blocks, key=lambda x: x[0]):
        if line in seen:
            continue
        seen.add(line)
        lines.append(f"{idx}. {line}")
        idx += 1

    if extras:
        lines.append("")
        lines.append("**Também no radar:**")
        lines.extend(extras)

    lines.append("")
    lines.append("Quer ajustar algum horário ou incluir mais alguma coisa?")
    return "\n".join(lines)
