"""Generate conversational responses with LLM or local fallback."""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any, Callable

from app.ai.ollama import OllamaError, check_ollama_health, ollama_chat
from app.brain.companion import (
    build_companion_system_prompt,
    filter_recent_messages_for_context,
    greeting_fallback,
    is_social_greeting,
)
from app.brain.schedule_builder import build_tomorrow_schedule_reply, is_tomorrow_list_request
from app.brain.llm_policy import _has_finance_keyword, should_use_llm
from app.brain.schemas import BrainAction, ConversationContext
from app.brain.state_manager import is_ack_message
from app.core.config import get_settings

logger = logging.getLogger(__name__)

def _strip_think_blocks(text: str) -> str:
    return text.strip()


_THERAPIST_PATTERNS = (
    re.compile(r"como você se sente[^.?!\n]*\?", re.IGNORECASE),
    re.compile(r"como você se sentiria[^.?!\n]*\?", re.IGNORECASE),
    re.compile(r"você tem planos para o próximo mês[^.?!\n]*\?", re.IGNORECASE),
)


def _sanitize_companion_response(text: str) -> str:
    """Remove repetitive therapist-style trailing questions from small models."""
    cleaned = text.strip()
    for pattern in _THERAPIST_PATTERNS:
        cleaned = pattern.sub("", cleaned).strip()
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = re.sub(r"[ \t]+\n", "\n", cleaned)
    return cleaned.strip()

_ACK_REPLIES = ("Tudo certo.", "👍", "Beleza.", "Combinado.")


def _pick_ack_reply(message: str) -> str:
    lowered = message.strip().lower()
    if lowered in {"vlw", "valeu", "show", "não vlw", "nao vlw"}:
        return "👍"
    return _ACK_REPLIES[0]


def _build_telegram_system_prompt(context: ConversationContext) -> str:
    return build_companion_system_prompt(context)


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

    if is_social_greeting(message):
        return greeting_fallback(message)

    if is_tomorrow_list_request(message):
        return build_tomorrow_schedule_reply(context)

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

    if primary == "routine_planning" and re.search(
        r"06:20|6:20|07:40|17:40|alarme|academia",
        lowered,
    ):
        return (
            "Rotina anotada — acordar cedo, trabalho o dia todo e academia depois. "
            "Parece puxado mas é bem definido. Prepara roupa e alarme hoje pra "
            "não depender de motivação amanhã."
        )

    if primary == "routine_planning":
        return (
            "Anotei sua rotina de amanhã. Prepara hoje o que puder — roupa, alarme, "
            "lista curta — pra facilitar acordar cedo."
        )

    if primary == "planning_request" or (
        primary == "routine_planning" and any(w in lowered for w in ("acord", "6:", "7:", "5:"))
    ):
        return (
            "Pra acordar 6h20 e ainda pegar faculdade atrasada, eu iria no mínimo viável:\n\n"
            "• Deitar o quanto antes\n"
            "• Deixar roupa/mochila prontas\n"
            "• Amanhã: 1 matéria prioritária só — 45 a 60 min focados, sem tentar recuperar tudo\n\n"
            "Quer que eu te ajude a escolher qual matéria atacar primeiro?"
        )

    if primary == "planning_request" or (
        primary in {"study_log", "study_plan"}
        and any(w in lowered for w in ("adiantar", "atrasad", "facul", "materia", "matéria"))
    ):
        return (
            "Faz sentido querer adiantar — ficar atrasado incomoda mesmo.\n\n"
            "Sem se punir: escolhe uma matéria que mais pesa ou que tem entrega mais perto. "
            "Amanhã, bloco curto de foco já quebra a sensação de atraso.\n\n"
            "Qual matéria tá te pesando mais agora?"
        )

    if primary in {"study_log", "study_plan"}:
        return (
            "Entendi. O que você quer priorizar primeiro — uma matéria específica "
            "ou montar um plano leve pro amanhã?"
        )

    if primary == "expense_log" and _has_finance_keyword(message):
        if any(a.action == "create_finance_transaction" and a.success for a in successful):
            return "Anotado — vi esse gasto."
        return "Entendi o gasto."

    if primary == "appointment":
        title = context.classification.get("entities", {}).get("title", "compromisso")
        if context.classification.get("explicit_appointment"):
            return f"Beleza, anotei {title}. Te ajudo a encaixar isso no dia."
        return (
            "Entendi. Me conta mais — é algo com horário marcado ou só algo que você "
            "tá pensando em fazer?"
        )

    if primary == "emotional_checkin" and "study_plan" in secondary:
        return (
            "Chegar em casa cansado pesa mesmo. Empurrar a faculdade pra amanhã faz sentido — "
            "descansa hoje sem culpa. Amanhã a gente vê o que encaixa, no seu ritmo."
        )

    if primary == "general_chat" and "emotional_checkin" in secondary:
        return (
            "Entendi. Parece que o dia bateu forte. Quer desabafar um pouco ou prefere "
            "só descansar agora?"
        )

    if primary == "note_creation" and any(a.action == "create_note" and a.success for a in successful):
        return "Anotado."

    if primary == "goal_update" or any(
        w in lowered for w in ("comprar moto", "juntar dinheiro", "juntar para")
    ):
        if "moto" in lowered:
            return (
                "Comprar a moto é um objetivo concreto — dá pra sentir o progresso. "
                "Segurar os gastos esse mês encaixa com isso. Quanto você já tem guardado "
                "ou quer bater até quando?"
            )
        return (
            "Faz sentido focar em juntar agora. O que te ajuda mais — valor fixo por mês "
            "ou cortar algum gasto específico?"
        )

    if any(w in lowered for w in ("final do mes", "final do mês", "nao posso gastar", "tudo pago", "tudo ja esta pago", "tudo já está pago")):
        return (
            "Fim de mês apertado é chato, mas se as contas já estão pagas você tá jogando "
            "certo — é só segurar até virar o mês. Mais alguns dias e alivia."
        )

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

    if primary == "general_chat":
        return (
            "Me conta — como você tá agora? Pode ser sobre o dia, faculdade, "
            "cansaço ou o que tiver na cabeça."
        )

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
        recent = filter_recent_messages_for_context(
            message, context.recent_messages[-recent_limit:]
        )
        for item in recent:
            messages.append({"role": item["role"], "content": item["content"]})
        messages.append({"role": "user", "content": message})

        llm_timeout = settings.telegram_llm_timeout_seconds
        http_timeout = llm_timeout + 1.0
        chat_options = {"num_predict": 280, "temperature": 0.75}
        if context.origin in ("telegram", "benchmark"):
            result = await asyncio.wait_for(
                chat_fn(
                    messages,
                    model=model,
                    timeout_seconds=http_timeout,
                    options=chat_options,
                ),
                timeout=llm_timeout,
            )
        else:
            result = await chat_fn(messages, model=model)

        content = _sanitize_companion_response(
            _strip_think_blocks((result.get("message") or {}).get("content", ""))
        )
        if content:
            return content, model, False
    except asyncio.TimeoutError:
        logger.warning(
            "brain_llm_timeout origin=%s timeout_s=%s",
            context.origin,
            settings.telegram_llm_timeout_seconds,
        )
    except OllamaError as exc:
        logger.warning("brain_llm_failed origin=%s error=%s", context.origin, exc)
    except Exception:
        logger.exception("brain_llm_unexpected")

    return fallback, None, True
