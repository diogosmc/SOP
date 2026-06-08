"""Robust Telegram Instructor pipeline — Jarvis mode."""

from __future__ import annotations

import asyncio
import logging
import re
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Callable
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.memory.classifier import classify_message
from app.ai.memory.consolidator import consolidate_memories
from app.ai.memory.extractor import extract_memory_candidates
from app.ai.memory.journal import update_daily_journal_from_message
from app.ai.ollama import OllamaError, check_ollama_health, ollama_chat
from app.core.config import get_settings
from app.modules.finance.models import TransactionType
from app.modules.finance.schemas import TransactionCreate
from app.modules.finance.service import FinanceService
from app.modules.notes.schemas import NoteCreate
from app.modules.notes.service import NoteService
from app.modules.reminders.schemas import ReminderCreate
from app.modules.reminders.service import ReminderService
from app.modules.tasks.schemas import TaskCreate
from app.modules.tasks.service import TaskService
from app.modules.users.service import ensure_default_user_exists
from app.telegram.formatter import format_telegram_reply

logger = logging.getLogger(__name__)

TELEGRAM_LLM_TIMEOUT_SECONDS = 15.0

_SAVE_INTENTS = frozenset(
    {
        "appointment",
        "study_log",
        "study_plan",
        "workout_log",
        "expense_log",
        "emotional_checkin",
        "goal_update",
        "habit_log",
        "task_creation",
        "note_creation",
        "reminder_creation",
    }
)

_APPOINTMENT_MARKERS = (
    "auto escola",
    "autoescola",
    "consulta",
    "compromisso",
    "reunião",
    "reuniao",
    "prova",
    "entrevista",
)

_NOTE_PREFIXES = ("anota que ", "anotar que ", "anota: ", "anotar: ")

_TASK_PREFIXES = (
    "preciso fazer ",
    "tenho que ",
    "preciso entregar ",
    "tenho que entregar ",
    "lembrar de ",
    "criar tarefa ",
    "nova tarefa ",
)


def _local_today() -> date:
    tz = ZoneInfo(get_settings().timezone)
    return datetime.now(tz).date()


def _parse_relative_datetime(text: str) -> datetime | None:
    lowered = text.lower()
    tz = ZoneInfo(get_settings().timezone)
    today = _local_today()

    if "amanhã" in lowered or "amanha" in lowered:
        target = today + timedelta(days=1)
        return datetime(target.year, target.month, target.day, 9, 0, tzinfo=tz)
    if "hoje" in lowered:
        return datetime(today.year, today.month, today.day, 18, 0, tzinfo=tz)
    return None


def _extract_appointment_title(text: str) -> str:
    lowered = text.lower()
    if "auto escola" in lowered or "autoescola" in lowered:
        return "Autoescola"
    for marker in ("vou ter ", "tenho ", "vou na ", "vou no ", "vou à ", "vou a "):
        if marker in lowered:
            idx = lowered.index(marker) + len(marker)
            title = text[idx:].strip(" .,;")
            if title:
                return title[:100].capitalize()
    return text[:80].strip(" .") or "Compromisso"


def _extract_note_content(text: str) -> tuple[str, str]:
    lowered = text.lower().strip()
    for prefix in _NOTE_PREFIXES:
        if lowered.startswith(prefix):
            content = text[len(prefix) :].strip(" .")
            title = content[:80] or "Nota"
            return title, content
    return text[:80] or "Nota", text


def _extract_task_title(text: str) -> str:
    lowered = text.lower().strip()
    for prefix in _TASK_PREFIXES:
        if lowered.startswith(prefix):
            return text[len(prefix) :].strip(" .")[:500]
    return text.strip()[:500]


def _coerce_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    return None


def _extract_expense_details(text: str, entities: dict[str, Any]) -> tuple[Decimal, str, str]:
    amount = entities.get("amount")
    if amount is None:
        match = re.search(r"(?:r\$\s*)?(\d+(?:[.,]\d{1,2})?)", text, re.IGNORECASE)
        if match:
            amount = float(match.group(1).replace(",", "."))
    if amount is None:
        amount = 0

    lowered = text.lower()
    category = "outros"
    for keyword, cat in (
        ("lanche", "alimentação"),
        ("almoço", "alimentação"),
        ("almoco", "alimentação"),
        ("jantar", "alimentação"),
        ("mercado", "alimentação"),
        ("uber", "transporte"),
        ("ônibus", "transporte"),
        ("onibus", "transporte"),
        ("gasolina", "transporte"),
    ):
        if keyword in lowered:
            category = cat
            break

    description = text.strip()[:500] or "Gasto registrado"
    return Decimal(str(amount)), category, description


def classify_telegram_message(text: str) -> dict[str, Any]:
    """Classify a Telegram message with Jarvis-oriented rules."""
    result = classify_message(text)
    normalized = text.strip()
    lowered = normalized.lower()
    entities = dict(result.get("entities") or {})

    if any(lowered.startswith(prefix) for prefix in _NOTE_PREFIXES):
        title, content = _extract_note_content(normalized)
        result.update(
            {
                "intent": "note_creation",
                "categories": ["note"],
                "should_save_memory": True,
                "entities": {**entities, "title": title, "content": content},
            }
        )
        return result

    if "revisar" in lowered or "preciso revisar" in lowered:
        title = _extract_task_title(normalized) if "preciso" in lowered else normalized
        result.update(
            {
                "intent": "study_plan",
                "categories": ["study"],
                "should_save_memory": True,
                "entities": {
                    **entities,
                    "title": title,
                    "remind_at": _parse_relative_datetime(normalized),
                },
            }
        )
        return result

    if any(marker in lowered for marker in _APPOINTMENT_MARKERS) or (
        ("amanhã" in lowered or "amanha" in lowered)
        and any(word in lowered for word in ("vou", "tenho"))
    ):
        result.update(
            {
                "intent": "appointment",
                "categories": ["routine", "appointment"],
                "should_save_memory": True,
                "entities": {
                    **entities,
                    "title": _extract_appointment_title(normalized),
                    "remind_at": _parse_relative_datetime(normalized),
                },
            }
        )
        return result

    if result.get("intent") == "task_creation":
        result["should_save_memory"] = True
        result["entities"] = {**entities, "title": _extract_task_title(normalized)}
        if "amanhã" in lowered or "amanha" in lowered:
            result["entities"]["remind_at"] = _parse_relative_datetime(normalized)
        return result

    if result.get("intent") == "emotional_checkin":
        result["should_save_memory"] = True
        return result

    if result.get("intent") == "expense_log":
        amount, category, description = _extract_expense_details(normalized, entities)
        result["should_save_memory"] = True
        result["entities"] = {
            **entities,
            "amount": float(amount),
            "category": category,
            "description": description,
        }
        return result

    if result.get("intent") == "study_log":
        result["should_save_memory"] = True
        return result

    if result.get("intent") == "general_chat" and len(normalized) >= 12:
        result["should_save_memory"] = True
        result["categories"] = ["context"]

    return result


async def _rollback_safe(db: AsyncSession) -> None:
    try:
        await db.rollback()
    except Exception:
        pass


async def _safe_save_memory(
    db: AsyncSession,
    user_id: uuid.UUID,
    text: str,
    classification: dict[str, Any],
) -> bool:
    intent = classification.get("intent", "general_chat")
    if not classification.get("should_save_memory") and intent not in _SAVE_INTENTS:
        return False
    try:
        await update_daily_journal_from_message(user_id, text, classification, db)
        candidates = extract_memory_candidates(text, classification)
        if candidates:
            await consolidate_memories(db, user_id, candidates)
        return True
    except Exception:
        await _rollback_safe(db)
        logger.exception(
            "telegram_memory_save_failed user_id=%s intent=%s",
            user_id,
            intent,
        )
        return False


async def _safe_create_task(
    db: AsyncSession,
    user_id: uuid.UUID,
    title: str,
    *,
    due_date: datetime | None = None,
    category: str | None = None,
) -> bool:
    try:
        await TaskService(db).create(
            user_id,
            TaskCreate(
                title=title,
                due_date=_coerce_datetime(due_date),
                category=category,
            ),
        )
        return True
    except Exception:
        await _rollback_safe(db)
        logger.exception("telegram_task_create_failed user_id=%s title=%s", user_id, title)
        return False


async def _safe_create_reminder(
    db: AsyncSession,
    user_id: uuid.UUID,
    title: str,
    remind_at: datetime,
) -> bool:
    try:
        await ReminderService(db).create(
            user_id,
            ReminderCreate(title=title, remind_at=remind_at),
        )
        return True
    except Exception:
        await _rollback_safe(db)
        logger.exception("telegram_reminder_create_failed user_id=%s title=%s", user_id, title)
        return False


async def _safe_create_note(
    db: AsyncSession,
    user_id: uuid.UUID,
    title: str,
    content: str,
) -> bool:
    try:
        await NoteService(db).create(
            user_id,
            NoteCreate(title=title, content=content, tags=["telegram"]),
        )
        return True
    except Exception:
        await _rollback_safe(db)
        logger.exception("telegram_note_create_failed user_id=%s title=%s", user_id, title)
        return False


async def _safe_create_expense(
    db: AsyncSession,
    user_id: uuid.UUID,
    text: str,
    entities: dict[str, Any],
) -> bool:
    try:
        amount, category, description = _extract_expense_details(text, entities)
        if amount <= 0:
            return False
        await FinanceService(db).create(
            user_id,
            TransactionCreate(
                description=description,
                amount=amount,
                type=TransactionType.EXPENSE,
                category=category,
                transaction_date=_local_today(),
            ),
        )
        return True
    except Exception:
        await _rollback_safe(db)
        logger.exception("telegram_expense_create_failed user_id=%s", user_id)
        return False


async def _execute_tools(
    db: AsyncSession,
    user_id: uuid.UUID,
    text: str,
    classification: dict[str, Any],
) -> str | None:
    intent = classification.get("intent", "general_chat")
    entities = classification.get("entities") or {}

    if intent == "appointment":
        title = entities.get("title", "Compromisso")
        remind_at = _coerce_datetime(entities.get("remind_at"))
        task_ok = await _safe_create_task(
            db, user_id, title, due_date=remind_at, category="compromisso"
        )
        reminder_ok = False
        if remind_at:
            reminder_ok = await _safe_create_reminder(db, user_id, title, remind_at)
        when = "amanhã" if remind_at else "em breve"
        if task_ok or reminder_ok:
            return (
                f"Anotei: {when} você tem {title.lower()}. "
                "Quer que eu também organize seu dia em torno disso?"
            )
        return (
            f"Entendi. Registrei como contexto do seu dia. "
            f"{when.capitalize()} você tem {title.lower()} — posso te lembrar ou ajudar a organizar o resto do dia."
        )

    if intent == "study_plan":
        title = entities.get("title", text[:80])
        remind_at = _coerce_datetime(entities.get("remind_at"))
        task_ok = await _safe_create_task(
            db, user_id, title, due_date=remind_at, category="estudo"
        )
        if task_ok:
            return "Boa. Registrei como estudo e criei uma tarefa. Posso transformar isso em revisão ou lembrete."
        return "Boa. Registrei como estudo. Posso transformar isso em revisão, flashcards ou tarefa."

    if intent == "task_creation":
        title = entities.get("title") or _extract_task_title(text)
        remind_at = _coerce_datetime(entities.get("remind_at"))
        if await _safe_create_task(db, user_id, title, due_date=remind_at):
            return f"Tarefa criada: «{title}»."
        return "Entendi. Registrei como contexto. Quer que eu transforme isso em tarefa, lembrete ou nota?"

    if intent == "note_creation":
        title = entities.get("title", "Nota")
        content = entities.get("content", text)
        if await _safe_create_note(db, user_id, title, content):
            return f"Anotado: «{title}»."
        return "Entendi. Registrei como contexto. Posso salvar como nota se quiser."

    if intent == "expense_log":
        if await _safe_create_expense(db, user_id, text, entities):
            amount = entities.get("amount", "")
            return f"Registrei o gasto de R$ {amount} no financeiro e no diário."
        return "Registrei o gasto na memória e no diário."

    if intent == "study_log":
        title = "Registro de estudo"
        if "python" in text.lower():
            title = "Estudo: Python"
        if await _safe_create_note(db, user_id, title, text):
            return "Boa. Registrei como estudo. Posso transformar isso em revisão, flashcards ou tarefa."
        return "Boa. Registrei como estudo. Posso transformar isso em revisão, flashcards ou tarefa."

    if intent == "workout_log":
        return "Registrei seu treino na memória e no diário."

    if intent == "habit_log":
        return "Anotado na memória e no diário."

    if intent == "goal_update":
        return "Objetivo salvo na memória. Vou usar isso para te acompanhar."

    if intent == "emotional_checkin":
        return (
            "Entendi. Vamos simplificar: escolha só uma tarefa pequena agora para recuperar o controle. "
            "Registrei como você está se sentindo no diário."
        )

    return None


def _local_fallback(
    classification: dict[str, Any],
    text: str,
    *,
    memory_saved: bool,
    tool_reply: str | None,
) -> str:
    if tool_reply:
        return tool_reply

    intent = classification.get("intent", "general_chat")
    entities = classification.get("entities") or {}

    if intent == "appointment":
        title = entities.get("title", "compromisso")
        return (
            f"Entendi. Registrei como contexto do seu dia. "
            f"Amanhã você tem {title.lower()} — posso te lembrar ou ajudar a organizar o resto do dia."
        )

    if intent == "emotional_checkin":
        return (
            "Entendi. Vamos simplificar: escolha só uma tarefa pequena agora para recuperar o controle."
        )

    if intent in {"study_log", "study_plan"}:
        return "Boa. Registrei como estudo. Posso transformar isso em revisão, flashcards ou tarefa."

    if intent == "expense_log":
        return "Registrei o gasto na memória e no diário."

    if memory_saved:
        return "Entendi. Registrei como contexto. Quer que eu transforme isso em tarefa, lembrete ou nota?"

    return "Entendi. Registrei como contexto. Quer que eu transforme isso em tarefa, lembrete ou nota?"


async def _try_llm_reply(
    text: str,
    *,
    ollama_chat_func: Callable[..., Any] | None = None,
) -> str | None:
    try:
        if not await check_ollama_health():
            return None

        settings = get_settings()
        chat_fn = ollama_chat_func or ollama_chat
        messages = [
            {
                "role": "system",
                "content": (
                    "Você é o Copiloto, assistente pessoal estilo Jarvis. "
                    "Responda em português, de forma curta e prática (máximo 3 frases)."
                ),
            },
            {"role": "user", "content": text},
        ]
        result = await asyncio.wait_for(
            chat_fn(messages, model=settings.ollama_model_fast),
            timeout=TELEGRAM_LLM_TIMEOUT_SECONDS,
        )
        content = (result.get("message") or {}).get("content", "").strip()
        return content or None
    except (OllamaError, asyncio.TimeoutError, Exception):
        logger.exception("telegram_llm_failed")
        return None


async def process_telegram_message(
    db: AsyncSession,
    user_id: uuid.UUID,
    text: str,
    *,
    classify_func: Callable[[str], dict[str, Any]] | None = None,
    ollama_chat_func: Callable[..., Any] | None = None,
    skip_llm: bool = False,
) -> str:
    """Backward-compatible wrapper around Conversation Brain."""
    from app.brain.conversation_manager import process_message as brain_process

    if classify_func is not None:
        classification = classify_func(text)
        intent = classification.get("intent", "general_chat")
        tool_reply = await _execute_tools(db, user_id, text, classification)
        memory_saved = await _safe_save_memory(db, user_id, text, classification)
        if tool_reply:
            return format_telegram_reply(tool_reply)
        if not skip_llm and intent in {"general_chat", "question"}:
            llm_reply = await _try_llm_reply(text, ollama_chat_func=ollama_chat_func)
            if llm_reply:
                return format_telegram_reply(llm_reply)
        return format_telegram_reply(
            _local_fallback(classification, text, memory_saved=memory_saved, tool_reply=tool_reply)
        )

    result = await brain_process(
        db,
        user_id,
        text,
        origin="telegram",
        prefer_speed=True,
        allow_tools=True,
        allow_llm=not skip_llm,
        ollama_chat_func=ollama_chat_func,
    )
    return result.response
