"""Telegram command handlers."""

from __future__ import annotations

from sqlalchemy import func, select
from telegram import Update
from telegram.ext import ContextTypes

from app.ai.ollama import check_ollama_health
from app.core.config import get_settings
from app.db.redis import check_redis_health
from app.db.session import AsyncSessionLocal, check_database_health
from app.modules.memory.models import AIMemory
from app.modules.memory.service import MemoryService
from app.modules.tasks.models import Task, TaskStatus
from app.modules.users.service import ensure_default_user_exists
from app.telegram.formatter import (
    format_debug_message,
    format_journal_summary,
    format_status_message,
    reply_telegram,
)
from app.telegram.instructor import process_telegram_message
from app.telegram.security import is_user_allowed, is_valid_telegram_user_id


async def _reply_unauthorized(update: Update) -> None:
    if update.message:
        await update.message.reply_text("Acesso não autorizado.")


async def _reply(update: Update, text: str) -> None:
    if update.message:
        await reply_telegram(update.message, text, html=True)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_user_allowed(update.effective_user.id if update.effective_user else None):
        await _reply_unauthorized(update)
        return

    await _reply(
        update,
        "Olá! Eu sou o Copiloto, seu instrutor pessoal.\n\n"
        "Você pode conversar comigo naturalmente — sem comandos complicados. "
        "Conte sobre estudos, treinos, objetivos, tarefas ou como está se sentindo.",
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_user_allowed(update.effective_user.id if update.effective_user else None):
        await _reply_unauthorized(update)
        return

    await _reply(
        update,
        "Exemplos de mensagens naturais:\n"
        "• «Amanhã eu vou ter autoescola»\n"
        "• «Estou desanimado hoje»\n"
        "• «Preciso revisar anatomia amanhã»\n"
        "• «Gastei 20 no lanche»\n"
        "• «Anota que segunda preciso resolver pendências»\n\n"
        "Comandos: /status, /debug, /resumo, /chat <mensagem>",
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_user_allowed(update.effective_user.id if update.effective_user else None):
        await _reply_unauthorized(update)
        return

    api_ok = await check_database_health()
    ollama_ok = await check_ollama_health()
    memory_count = 0
    pending_tasks = 0

    async with AsyncSessionLocal() as db:
        user = await ensure_default_user_exists(db)
        memory_result = await db.execute(
            select(func.count()).select_from(AIMemory).where(AIMemory.user_id == user.id)
        )
        memory_count = memory_result.scalar_one()
        task_result = await db.execute(
            select(func.count())
            .select_from(Task)
            .where(Task.user_id == user.id, Task.status == TaskStatus.PENDING)
        )
        pending_tasks = task_result.scalar_one()
        await db.commit()

    await _reply(
        update,
        format_status_message(
            api_ok=api_ok,
            ollama_ok=ollama_ok,
            memory_count=memory_count,
            pending_tasks=pending_tasks,
        ),
    )


async def cmd_debug(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_user_allowed(update.effective_user.id if update.effective_user else None):
        await _reply_unauthorized(update)
        return

    settings = get_settings()
    db_ok = await check_database_health()
    redis_ok = await check_redis_health()
    ollama_ok = await check_ollama_health()
    memory_count = 0
    pending_tasks = 0
    default_user_name = "—"

    async with AsyncSessionLocal() as db:
        user = await ensure_default_user_exists(db)
        default_user_name = user.name
        memory_result = await db.execute(
            select(func.count()).select_from(AIMemory).where(AIMemory.user_id == user.id)
        )
        memory_count = memory_result.scalar_one()
        task_result = await db.execute(
            select(func.count())
            .select_from(Task)
            .where(Task.user_id == user.id, Task.status == TaskStatus.PENDING)
        )
        pending_tasks = task_result.scalar_one()
        await db.commit()

    from app.main import app

    await _reply(
        update,
        format_debug_message(
            version=app.version,
            api_ok=db_ok,
            db_ok=db_ok,
            redis_ok=redis_ok,
            ollama_ok=ollama_ok,
            telegram_user_ok=is_valid_telegram_user_id(settings.telegram_allowed_user_id),
            default_user_ok=True,
            default_user_name=default_user_name,
            memory_count=memory_count,
            pending_tasks=pending_tasks,
        ),
    )


async def cmd_resumo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_user_allowed(update.effective_user.id if update.effective_user else None):
        await _reply_unauthorized(update)
        return

    async with AsyncSessionLocal() as db:
        user = await ensure_default_user_exists(db)
        journal = await MemoryService(db).get_today_journal(user.id)
        await db.commit()
        await _reply(update, format_journal_summary(journal))


async def cmd_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_user_allowed(update.effective_user.id if update.effective_user else None):
        await _reply_unauthorized(update)
        return

    message = " ".join(context.args).strip() if context.args else ""
    if not message:
        await _reply(
            update,
            "Modo conversa ativo. Envie sua mensagem ou use /chat <mensagem> para falar comigo.",
        )
        return

    async with AsyncSessionLocal() as db:
        user = await ensure_default_user_exists(db)
        reply = await process_telegram_message(db, user.id, message, skip_llm=False)
        await db.commit()
        await _reply(update, reply)
