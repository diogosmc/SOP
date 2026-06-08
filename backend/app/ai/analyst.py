"""Optional AI analyst for reports insights."""

from __future__ import annotations

import json
from typing import Any, Awaitable, Callable, List

from app.ai.ollama import OllamaError, ollama_chat

OllamaChatFunc = Callable[..., Awaitable[dict[str, Any]]]


async def generate_ai_insights(
    context: dict[str, Any],
    ollama_chat_func: OllamaChatFunc | None = None,
) -> List[str]:
    chat = ollama_chat_func or ollama_chat
    prompt = (
        "Analise os dados abaixo e gere de 3 a 6 insights curtos em português, "
        "como bullets objetivos sobre produtividade, estudos, treino, finanças e hábitos. "
        "Não dê conselhos médicos. Responda apenas com JSON: {\"insights\": [\"...\"]}.\n\n"
        f"Dados: {json.dumps(context, ensure_ascii=False, default=str)}"
    )
    try:
        result = await chat(
            messages=[
                {"role": "system", "content": "Você é um analista pessoal. Responda só JSON válido."},
                {"role": "user", "content": prompt},
            ]
        )
        content = result.get("message", {}).get("content", "") if isinstance(result, dict) else ""
        text = content.strip()
        if text.startswith("```"):
            lines = [line for line in text.split("\n") if not line.strip().startswith("```")]
            text = "\n".join(lines).strip()
        parsed = json.loads(text)
        if isinstance(parsed, dict) and isinstance(parsed.get("insights"), list):
            return [str(item) for item in parsed["insights"] if item][:8]
    except (OllamaError, json.JSONDecodeError, TypeError, ValueError):
        return []
    return []
