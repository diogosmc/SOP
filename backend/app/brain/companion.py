"""Companion AI persona — conversational friend, separate from data collection."""

from __future__ import annotations

import re

from app.brain.schedule_builder import is_tomorrow_list_request
from app.brain.schemas import ConversationContext, MemorySnippet

_GREETING_PREFIXES = (
    "oi",
    "olá",
    "ola",
    "bom dia",
    "boa tarde",
    "boa noite",
    "e aí",
    "e ai",
    "eae",
    "fala",
    "hey",
    "hello",
)


def is_social_greeting(message: str) -> bool:
    normalized = message.strip().lower().rstrip("!?. ")
    if not normalized:
        return False
    return any(
        normalized == prefix or normalized.startswith(f"{prefix} ")
        for prefix in _GREETING_PREFIXES
    )


def greeting_fallback(message: str) -> str:
    lowered = message.strip().lower()
    if "noite" in lowered:
        return (
            "Boa noite! Como você tá chegando nessa noite — mais tranquilo ou a cabeça "
            "ainda acelerada? Se quiser desabafar ou só conversar, tô aqui."
        )
    if "dia" in lowered and "bom" in lowered:
        return (
            "Bom dia! Dormiu razoável? Me conta como tá começando o dia — sem pressa."
        )
    if "tarde" in lowered:
        return "Boa tarde! Como tá sendo o dia até aqui?"
    return (
        "Oi! Tô por aqui. Quer conversar, desabafar ou só trocar ideia sobre o dia?"
    )


def filter_recent_messages_for_context(
    message: str,
    recent: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Drop assistant turns that contradict what the user just corrected."""
    lowered = message.lower()
    combined = " ".join(
        item.get("content", "")
        for item in recent
        if item.get("role") == "user"
    ).lower() + " " + lowered

    deny_auto = bool(
        re.search(
            r"n[aã]o tenho auto|sem auto\s*escola|nao vou na auto|s[oó] na academia",
            combined,
        )
    )
    if not deny_auto:
        return recent

    filtered: list[dict[str, str]] = []
    for item in recent:
        if item.get("role") == "assistant":
            content = item.get("content", "").lower()
            if "autoescola" in content or "auto escola" in content:
                continue
        filtered.append(item)
    return filtered


def filter_memories_for_message(
    message: str,
    snippets: list[MemorySnippet],
) -> list[MemorySnippet]:
    """Drop stale memories the user explicitly contradicted."""
    lowered = message.lower()
    blocked: set[str] = set()

    if re.search(
        r"n[aã]o tenho auto|sem auto\s*escola|nao vou na auto|s[oó] na academia",
        lowered,
    ):
        blocked.update(("autoescola", "auto escola"))

    if not blocked:
        return snippets

    return [
        s
        for s in snippets
        if not any(term in s.content.lower() for term in blocked)
    ]


def _user_correction_hints(context: ConversationContext) -> list[str]:
    """Build explicit hints from recent user messages so the LLM stops repeating mistakes."""
    texts: list[str] = [context.message]
    for item in context.recent_messages[-6:]:
        if item.get("role") == "user":
            texts.append(item.get("content", ""))

    combined = " ".join(texts).lower()
    hints: list[str] = []

    if re.search(
        r"n[aã]o tenho auto|sem auto\s*escola|nao vou na auto|s[oó] na academia",
        combined,
    ):
        hints.append(
            "CORREÇÃO DO DIOGO: amanhã NÃO tem autoescola. Rotina dele inclui trabalho "
            "e/ou academia. Nunca sugira autoescola nem pergunte se quer adiar autoescola."
        )

    if (
        re.search(r"juntar dinheiro|comprar (minha )?moto|meta.*moto", combined)
        and not is_tomorrow_list_request(context.message)
    ):
        hints.append(
            "Meta atual dele: juntar dinheiro (comprar moto). Fale disso de forma prática "
            "e motivadora — não fique só perguntando como ele se sente."
        )

    if re.search(
        r"final do m[eê]s|n[aã]o posso gastar|tudo j[aá] est[aá] pago|sem gastar",
        combined,
    ):
        hints.append(
            "Contexto financeiro: mês apertado, contas pagas, evitando gastos extras até "
            "o fim do mês. Valide isso sem dramatizar nem inventar dívidas."
        )

    if re.search(r"06:20|6:20|07:40|17:40|alarme", combined):
        hints.append(
            "Rotina de amanhã já informada (ex.: acordar ~6h20, trabalho ~7h40–17h40). "
            "Use esses horários se falar de plano — não invente outros."
        )

    return hints


def build_companion_system_prompt(context: ConversationContext) -> str:
    """Friend-style chat — factual, warm, not a repetitive therapist."""
    state = context.state

    parts = [
        "Você é o Copiloto pessoal do Diogo — amigo inteligente no WhatsApp, estilo ChatGPT "
        "casual. Converse de verdade; NÃO seja terapeuta que repete a mesma pergunta.",
        "",
        "Como responder:",
        "• Comece respondendo ao que ele DISSE AGORA (fatos, planos, metas, rotina).",
        "• Valide em 1 frase se couber — depois comente ou ajude de forma prática.",
        "• No máximo UMA pergunta curta por mensagem, e só se natural. "
        "NUNCA termine toda resposta com 'como você se sente?' ou variações.",
        "• Se ele corrigiu algo antes, siga a versão dele — memórias antigas podem estar erradas.",
        "• Não invente compromissos (autoescola, consultas) que ele não mencionou nesta conversa.",
        "• Metas (moto, juntar dinheiro): engaje com entusiasmo real, dicas leves, zero interrogatório.",
        "• Aperto no fim do mês: empatia + 'faz sentido segurar a onda' — sem culpa nem drama.",
        "",
        "Proibido: 'anotei', 'registrei', diagnóstico, mencionar sistema/banco de dados.",
    ]

    for hint in _user_correction_hints(context):
        parts.append(f"IMPORTANTE: {hint}")

    if is_tomorrow_list_request(context.message):
        parts.extend(
            [
                "",
                "PEDIDO ATUAL: listar o dia de AMANHÃ.",
                "Resposta = lista numerada com horários que ele JÁ disse na conversa.",
                "NÃO fale de moto, metas financeiras ou tarefas inventadas.",
            ]
        )
    elif context.primary_goal:
        parts.append(f"Objetivo de longo prazo (referência): {context.primary_goal[:120]}")

    if context.relevant_memories:
        mem = context.relevant_memories[0].content[:100]
        parts.append(
            f"Memória antiga (pode estar desatualizada — mensagem atual vence): {mem}"
        )

    if state.conversation_mode == "apoio":
        parts.append("Tom levemente acolhedor, mas ainda conversacional — não clínico.")

    return "\n".join(parts)
