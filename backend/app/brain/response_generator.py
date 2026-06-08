"""Generate conversational responses with LLM or local fallback."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable

from app.ai.ollama import OllamaError, check_ollama_health, ollama_chat
from app.brain.llm_policy import should_use_llm
from app.brain.schemas import BrainAction, ConversationContext
from app.brain.state_manager import is_ack_message
from app.core.config import get_settings

logger = logging.getLogger(__name__)

_ACK_REPLIES = ("Tudo certo.", "👍", "Beleza.", "Combinado.")


def _pick_ack_reply(message: str) -> str:
    lowered = message.strip().lower()
    if lowered in {"vlw", "valeu", "show", "não vlw", "nao vlw"}:
        return "👍"
    return _ACK_REPLIES[0]


def _build_telegram_system_prompt(context: ConversationContext) -> str:
    state = context.state
    primary = context.primary_intent or context.intent
    secondary = context.secondary_intents or []
    parts = [
        "Você é o Copiloto pessoal do Diogo. Responda em português brasileiro, "
        "de forma natural, direta e prática — sem parecer robô de comandos.",
        f"Intenção: {primary}"
        + (f" (também: {', '.join(secondary)})" if secondary else "")
        + f". Estado: mood={state.mood}, mode={state.conversation_mode}.",
        "Se a mensagem misturar rotina e emoção, aborde os dois. "
        "Se for treino ou tarefa clara, seja objetivo. "
        "Respostas curtas para acks. Não invente dados.",
    ]
    if context.today_journal_summary:
        parts.append(f"Diário hoje: {context.today_journal_summary[:200]}")
    if context.relevant_memories:
        mem = context.relevant_memories[0].content[:150]
        parts.append(f"Memória relevante: {mem}")
    return "\n".join(parts)


def _build_system_prompt(context: ConversationContext) -> str:
    if context.origin in ("telegram", "benchmark"):
        return _build_telegram_system_prompt(context)
    state = context.state
    parts = [
        "Você é o Copiloto pessoal do Diogo.",
        f"Estado: mood={state.mood}, energy={state.energy}, "
        f"topic={state.current_topic}, mode={state.conversation_mode}",
    ]
    if context.primary_goal:
        parts.append(f"Objetivo: {context.primary_goal}")
    return "\n".join(parts)


def _local_fallback(
    message: str,
    context: ConversationContext,
    actions: list[BrainAction],
) -> str:
    if context.is_ack or is_ack_message(message):
        return _pick_ack_reply(message)

    primary = context.primary_intent or context.intent
    secondary = context.secondary_intents or []
    state = context.state
    successful = [a for a in actions if a.success and a.action != "none"]
    lowered = message.lower()

    if primary == "workout_log":
        return (
            "Boa. Registrei seu treino. Foca na execução hoje — "
            "depois a gente ajusta volume e descanso se precisar."
        )

    if primary == "routine_planning" and "emotional_checkin" in secondary:
        return (
            "Entendi: amanhã você quer levantar cedo pra trabalhar, mas tá com preguiça agora.\n\n"
            "Prepara hoje o que puder — roupa, alarme, café pronto — pra amanhã não depender de motivação. "
            "E agora, descansa sem culpa se precisar."
        )

    if primary == "routine_planning":
        return (
            "Anotei sua rotina de amanhã. Prepara hoje o que puder — roupa, alarme, "
            "lista curta — pra facilitar acordar cedo."
        )

    if primary == "planning_request":
        return (
            "Vamos simplificar: 1 prioridade principal, 1 tarefa leve e 1 coisa que já "
            "deixa amanhã mais fácil (roupa, material, alarme)."
        )

    if primary == "appointment":
        title = context.classification.get("entities", {}).get("title", "compromisso")
        return f"Anotei isso como compromisso ({title}). Vou considerar na organização do seu dia."

    if primary in {"study_log", "study_plan"}:
        return "Beleza, registrei isso como estudo. Posso te ajudar a transformar em revisão prática depois."

    if primary == "expense_log":
        if any(a.action == "create_finance_transaction" and a.success for a in successful):
            return "Registrei esse gasto no financeiro."
        return "Registrei esse gasto no diário."

    if primary == "note_creation" and any(a.action == "create_note" and a.success for a in successful):
        return "Anotado."

    if primary == "goal_update":
        return "Objetivo salvo. Vou usar isso para te acompanhar."

    if primary == "emotional_checkin" or (
        primary == "general_chat"
        and state.conversation_mode == "apoio"
        and primary != "workout_log"
    ):
        if "deitado" in lowered or state.last_intent == "emotional_checkin":
            return (
                "Entendi. Parece mais um dia de baixa energia do que falta de vontade.\n\n"
                "Se for descansar hoje, tudo bem. Escolhe uma coisa mínima pra não terminar "
                "o dia com culpa — separar material de amanhã ou 10 min de revisão."
            )
        return (
            "Entendi. Parece um dia de energia baixa. Vamos simplificar: escolhe só uma "
            "coisa pequena hoje, nem que seja por 10 minutos."
        )

    if primary == "general_chat" and state.conversation_mode == "apoio":
        return "Quer desabafar um pouco ou prefere uma ação mínima pra hoje?"

    if successful:
        return "Entendi. Já registrei o que fazia sentido. Quer continuar por aqui?"

    return "Entendi. Vou guardar isso como contexto para te responder melhor nas próximas."


def generate_fast_fallback(
    message: str,
    context: ConversationContext,
    actions: list[BrainAction] | None = None,
) -> str:
    """Lightweight fallback for streamer timeout without LLM."""
    return _local_fallback(message, context, actions or [])


def _format_actions_note(actions: list[BrainAction]) -> str:
    labels = []
    for action in actions:
        if action.success and action.action != "none":
            labels.append(action.action)
    return ", ".join(labels)


async def generate_response(
    message: str,
    context: ConversationContext,
    actions: list[BrainAction],
    *,
    prefer_speed: bool = True,
    allow_llm: bool = True,
    response_mode: str | None = None,
    ollama_chat_func: Callable[..., Any] | None = None,
) -> tuple[str, str | None, bool]:
    if context.is_ack or is_ack_message(message):
        return _pick_ack_reply(message), None, True

    fallback = _local_fallback(message, context, actions)
    settings = get_settings()
    mode = response_mode or settings.telegram_response_mode

    if mode == "fallback_only" or not allow_llm:
        return fallback, None, True

    if not should_use_llm(message, context, mode):
        return fallback, None, True

    try:
        if not await check_ollama_health():
            return fallback, None, True

        use_fast = (
            prefer_speed
            or settings.telegram_force_fast_model
            or context.origin in ("telegram", "benchmark")
        )
        model = settings.ollama_model_fast if use_fast else settings.ollama_model_main
        chat_fn = ollama_chat_func or ollama_chat

        messages: list[dict[str, str]] = [
            {"role": "system", "content": _build_system_prompt(context)},
        ]
        recent_limit = (
            settings.telegram_recent_messages_limit
            if context.origin in ("telegram", "benchmark")
            else 8
        )
        for item in context.recent_messages[-recent_limit:]:
            messages.append({"role": item["role"], "content": item["content"]})
        action_note = _format_actions_note(actions)
        user_content = message
        if action_note:
            user_content += f"\n\n[Ações executadas: {action_note}]"
        messages.append({"role": "user", "content": user_content})

        result = await asyncio.wait_for(
            chat_fn(messages, model=model),
            timeout=settings.telegram_llm_timeout_seconds,
        )
        content = (result.get("message") or {}).get("content", "").strip()
        if content:
            return content, model, False
    except (OllamaError, asyncio.TimeoutError, Exception):
        logger.exception("brain_llm_failed")

    return fallback, None, True
