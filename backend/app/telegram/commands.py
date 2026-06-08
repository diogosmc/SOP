"""Telegram command handlers."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from telegram import Update
from telegram.ext import ContextTypes

from app.ai.ollama import check_ollama_health
from app.core.config import get_settings
from app.db.session import AsyncSessionLocal, check_database_health
from app.modules.memory.models import AIMemory
from app.modules.memory.service import MemoryService
from app.modules.tasks.models import Task, TaskStatus
from app.telegram.formatter import format_journal_summary, format_status_message, format_telegram_reply
from app.telegram.security import is_user_allowed
from app.telegram.tools import handle_chat_fallback


async def _reply_unauthorized(update: Update) -> None:
    if update.message:
        await update.message.reply_text("Acesso não autorizado.")


async def _reply(update: Update, text: str) -> None:
    if update.message:
        await update.message.reply_text(format_telegram_reply(text))


def _app_user_id() -> uuid.UUID:
    return uuid.UUID(get_settings().default_user_id)


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
        "• «Quero passar em Medicina»\n"
        "• «Estudei Python por 1 hora»\n"
        "• «Gastei 20 no lanche»\n"
        "• «Vou treinar pernas hoje»\n"
        "• «Preciso fazer revisão de física»\n"
        "• «Estou desanimado hoje»\n\n"
        "Comandos: /status, /resumo, /chat <mensagem>",
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_user_allowed(update.effective_user.id if update.effective_user else None):
        await _reply_unauthorized(update)
        return

    user_id = _app_user_id()
    api_ok = await check_database_health()
    ollama_ok = await check_ollama_health()
    memory_count = 0
    pending_tasks = 0

    async with AsyncSessionLocal() as db:
        memory_result = await db.execute(
            select(func.count()).select_from(AIMemory).where(AIMemory.user_id == user_id)
        )
        memory_count = memory_result.scalar_one()
        task_result = await db.execute(
            select(func.count())
            .select_from(Task)
            .where(Task.user_id == user_id, Task.status == TaskStatus.PENDING)
        )
        pending_tasks = task_result.scalar_one()

    await _reply(
        update,
        format_status_message(
            api_ok=api_ok,
            ollama_ok=ollama_ok,
            memory_count=memory_count,
            pending_tasks=pending_tasks,
        ),
    )


async def cmd_resumo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_user_allowed(update.effective_user.id if update.effective_user else None):
        await _reply_unauthorized(update)
        return

    user_id = _app_user_id()
    async with AsyncSessionLocal() as db:
        journal = await MemoryService(db).get_today_journal(user_id)
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

    user_id = _app_user_id()
    async with AsyncSessionLocal() as db:
        reply = await handle_chat_fallback(db, user_id, message)
        await db.commit()
        await _reply(update, reply)
