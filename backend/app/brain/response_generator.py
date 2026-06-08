"""Generate conversational responses with LLM or local fallback."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable

from app.ai.ollama import OllamaError, check_ollama_health, ollama_chat
from app.brain.schemas import BrainAction, ConversationContext
from app.brain.state_manager import is_ack_message
from app.core.config import get_settings

logger = logging.getLogger(__name__)

_DEEP_KEYWORDS = (
    "plano completo",
    "planejamento semanal",
    "análise profunda",
    "analise profunda",
    "montar um plano",
    "organizar meu dia",
    "organizar meu dia amanhã",
    "organizar meu dia amanha",
    "reflexão",
    "reflexao",
    "estudo detalhado",
)

_ACK_REPLIES = ("Tudo certo.", "👍", "Beleza.", "Combinado.")


def _pick_ack_reply(message: str) -> str:
    lowered = message.strip().lower()
    if lowered in {"vlw", "valeu", "show"}:
        return "👍"
    return _ACK_REPLIES[0]


def _needs_deep_model(message: str) -> bool:
    lowered = message.lower()
    return any(keyword in lowered for keyword in _DEEP_KEYWORDS)


def _build_system_prompt(context: ConversationContext) -> str:
    state = context.state
    parts = [
        "Você é o Copiloto pessoal do Diogo.",
        "",
        "Seu papel principal é conversar bem.",
        "Seu papel secundário é agir silenciosamente quando fizer sentido.",
        "",
        "Você deve responder como uma IA pessoal parecida com ChatGPT/Claude:",
        "- natural",
        "- direta",
        "- útil",
        "- sem parecer robô de comandos",
        "- sem transformar tudo em tarefa, nota ou lembrete",
        "- lembrando do contexto recente",
        "- usando as memórias relevantes",
        "- ajudando o Diogo a agir sem julgar",
        "",
        "Regras:",
        "1. Responda em português brasileiro.",
        "2. Seja humano, direto e prático.",
        "3. Se a mensagem for emocional, responda com apoio prático.",
        "4. Não diga que é psicólogo, médico ou consultor financeiro.",
        "5. Não faça diagnóstico.",
        "6. Se ações foram executadas, mencione de forma natural.",
        '7. Se o usuário disser "não", "vlw", "ok", responda curto.',
        "8. Não invente dados.",
        '9. Não repita "quer transformar em tarefa, lembrete ou nota?".',
        "10. Só faça perguntas quando ajudarem a continuidade da conversa.",
        "",
        f"Estado atual: mood={state.mood}, energy={state.energy}, "
        f"topic={state.current_topic}, mode={state.conversation_mode}",
    ]
    if context.primary_goal:
        parts.append(f"Objetivo principal: {context.primary_goal}")
    if context.today_journal_summary:
        parts.append(f"Diário hoje: {context.today_journal_summary}")
    if context.important_memories:
        parts.append("Memórias importantes:")
        for mem in context.important_memories[:5]:
            parts.append(f"- [{mem.category}] {mem.content}")
    if context.relevant_memories:
        parts.append("Memórias relevantes:")
        for mem in context.relevant_memories[:5]:
            parts.append(f"- {mem.content}")
    if context.pending_tasks:
        parts.append("Tarefas pendentes: " + "; ".join(context.pending_tasks[:3]))
    if context.upcoming_reminders:
        parts.append("Lembretes próximos: " + "; ".join(context.upcoming_reminders[:3]))
    return "\n".join(parts)


def _local_fallback(
    message: str,
    context: ConversationContext,
    actions: list[BrainAction],
) -> str:
    if context.is_ack or is_ack_message(message):
        return _pick_ack_reply(message)

    intent = context.intent
    state = context.state
    successful = [a for a in actions if a.success and a.action != "none"]
    lowered = message.lower()

    if intent == "appointment":
        title = context.classification.get("entities", {}).get("title", "compromisso")
        return f"Anotei isso como compromisso ({title}). Vou considerar na organização do seu dia."

    if intent in {"study_log", "study_plan"}:
        return "Beleza, registrei isso como estudo. Posso te ajudar a transformar em revisão prática depois."

    if intent == "expense_log":
        if any(a.action == "create_finance_transaction" and a.success for a in successful):
            return "Registrei esse gasto no financeiro."
        return "Registrei esse gasto no diário."

    if intent == "note_creation" and any(a.action == "create_note" and a.success for a in successful):
        return "Anotado."

    if intent == "goal_update":
        return "Objetivo salvo. Vou usar isso para te acompanhar."

    if intent == "emotional_checkin" or (
        intent == "general_chat"
        and (
            state.mood == "desanimado"
            or any(w in lowered for w in ("desanimado", "deitado", "culpado", "cansado"))
        )
    ):
        if state.last_intent == "emotional_checkin" or "deitado" in lowered:
            return (
                "Entendi. Pelo que você falou antes, parece mais um dia de baixa energia "
                "do que falta de vontade.\n\n"
                "Se for descansar hoje, tudo bem. Só tenta escolher uma coisa mínima para "
                "não terminar o dia com sensação de culpa — tipo separar o material de amanhã "
                "ou revisar por 10 minutos."
            )
        return (
            "Entendi. Parece um dia de energia baixa. Vamos simplificar: escolhe só uma "
            "coisa pequena para fazer hoje, nem que seja por 10 minutos. Isso já evita a "
            "sensação de ter perdido o dia inteiro."
        )

    if successful:
        return "Entendi. Já registrei o que fazia sentido. Quer continuar por aqui?"

    if state.last_assistant_message and state.conversation_mode == "apoio":
        return (
            "Entendi. Vou guardar isso como contexto. Se quiser, me diz o que seria "
            "uma vitória mínima hoje — algo pequeno já conta."
        )

    return "Entendi. Vou guardar isso como contexto para te responder melhor nas próximas."


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
    ollama_chat_func: Callable[..., Any] | None = None,
) -> tuple[str, str | None, bool]:
    if context.is_ack or is_ack_message(message):
        return _pick_ack_reply(message), None, True

    fallback = _local_fallback(message, context, actions)

    if not allow_llm:
        return fallback, None, True

    try:
        if not await check_ollama_health():
            return fallback, None, True

        settings = get_settings()
        use_deep = _needs_deep_model(message) and not (
            prefer_speed or settings.telegram_force_fast_model
        )
        model = settings.ollama_model_main if use_deep else settings.ollama_model_fast
        chat_fn = ollama_chat_func or ollama_chat

        messages: list[dict[str, str]] = [
            {"role": "system", "content": _build_system_prompt(context)},
        ]
        for item in context.recent_messages[-8:]:
            messages.append({"role": item["role"], "content": item["content"]})
        action_note = _format_actions_note(actions)
        user_content = message
        if action_note:
            user_content += f"\n\n[Ações executadas silenciosamente: {action_note}]"
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
