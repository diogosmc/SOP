"""Benchmark utilities for Conversation Brain."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.brain.conversation_manager import process_message
from app.brain.schemas import BenchmarkResult
from app.brain.state_manager import reset_user_state

DEFAULT_BENCHMARK_MESSAGES = [
    "Estou desanimado hoje",
    "Ah sei lá, tô afim de ficar deitado",
    "Não vlw",
    "Amanhã tenho autoescola às 8",
    "Preciso revisar anatomia amanhã",
    "Gastei 20 no lanche",
    "Anota que segunda preciso resolver pendências",
    "Quero organizar meu dia amanhã",
    "Me ajuda a montar um plano de estudo rápido",
    "Hoje não fiz nada e tô me sentindo culpado",
    "Tenho prova semana que vem",
    "Vou treinar peito hoje",
    "Amanha vou levantar cedo pra trabalhar e to com uma preguiça gigante",
]

BENCHMARK_MODES = ("fallback_only", "hybrid", "llm_only")


async def run_benchmark(
    db: AsyncSession,
    user_id: Any,
    messages: list[str] | None = None,
    *,
    mode: str = "fallback_only",
    allow_llm: bool | None = None,
    process_func: Callable[..., Any] | None = None,
) -> list[BenchmarkResult]:
    runner = process_func or process_message
    items = messages or DEFAULT_BENCHMARK_MESSAGES
    results: list[BenchmarkResult] = []
    use_llm = allow_llm if allow_llm is not None else mode != "fallback_only"

    for text in items:
        started = time.perf_counter()
        first_ms = 0
        status = "OK"
        error = None
        try:
            await reset_user_state(db, user_id)
            first_ms = int((time.perf_counter() - started) * 1000)
            brain_result = await runner(
                db,
                user_id,
                text,
                origin="benchmark",
                allow_llm=use_llm,
                response_mode=mode,
            )
            total_ms = int((time.perf_counter() - started) * 1000)

            from app.brain.classifier import classify_message

            classification = classify_message(text)
            primary = classification.get("primary_intent") or classification.get(
                "intent", brain_result.intent
            )
            secondary = list(classification.get("secondary_intents") or [])

            results.append(
                BenchmarkResult(
                    message=text,
                    mode=mode,
                    total_ms=total_ms,
                    first_response_ms=first_ms,
                    primary_intent=primary,
                    secondary_intents=secondary,
                    model_used=brain_result.model_used,
                    used_fallback=brain_result.used_fallback,
                    used_llm=brain_result.used_llm,
                    actions=[
                        a.action for a in brain_result.actions if a.action != "none"
                    ],
                    response=brain_result.response[:500],
                    status=status,
                    error=error,
                )
            )
            await db.commit()
        except Exception as exc:
            await db.rollback()
            total_ms = int((time.perf_counter() - started) * 1000)
            results.append(
                BenchmarkResult(
                    message=text,
                    mode=mode,
                    total_ms=total_ms,
                    first_response_ms=first_ms,
                    status="ERROR",
                    error=str(exc),
                )
            )
    return results


async def run_all_mode_benchmarks(
    db: AsyncSession,
    user_id: Any,
    messages: list[str] | None = None,
    *,
    process_func: Callable[..., Any] | None = None,
) -> dict[str, list[BenchmarkResult]]:
    grouped: dict[str, list[BenchmarkResult]] = {}
    for mode in BENCHMARK_MODES:
        grouped[mode] = await run_benchmark(
            db,
            user_id,
            messages=messages,
            mode=mode,
            process_func=process_func,
        )
    return grouped


def format_benchmark_report(results: list[BenchmarkResult]) -> str:
    lines: list[str] = []
    mode = results[0].mode if results else "unknown"
    lines.append(f"Modo: {mode}")
    lines.append("")
    for item in results:
        lines.append(f"Mensagem: {item.message}")
        lines.append(f"Intenção: {item.primary_intent}")
        if item.secondary_intents:
            lines.append(f"Secundárias: {', '.join(item.secondary_intents)}")
        lines.append(f"Tempo: {item.total_ms / 1000:.1f}s")
        lines.append(f"Modelo: {item.model_used or 'fallback'}")
        lines.append(f"Fallback: {str(item.used_fallback).lower()}")
        lines.append(f"Ações: {', '.join(item.actions) if item.actions else 'none'}")
        lines.append(f"Resposta: {item.response[:200]}")
        lines.append(f"Status: {item.status}")
        if item.error:
            lines.append(f"Erro: {item.error}")
        lines.append("")
    return "\n".join(lines)


def save_benchmark_report(
    results: list[BenchmarkResult] | dict[str, list[BenchmarkResult]],
    path: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(results, dict):
        payload = {mode: [item.model_dump() for item in items] for mode, items in results.items()}
    else:
        payload = [item.model_dump() for item in results]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
