"""Benchmark utilities for Conversation Brain."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.brain.conversation_manager import process_message
from app.brain.schemas import BenchmarkResult

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
]


async def run_benchmark(
    db: AsyncSession,
    user_id: Any,
    messages: list[str] | None = None,
    *,
    allow_llm: bool = False,
    process_func: Callable[..., Any] | None = None,
) -> list[BenchmarkResult]:
    runner = process_func or process_message
    items = messages or DEFAULT_BENCHMARK_MESSAGES
    results: list[BenchmarkResult] = []

    for text in items:
        started = time.perf_counter()
        first_ms = 0
        status = "OK"
        error = None
        try:
            first_ms = int((time.perf_counter() - started) * 1000)
            brain_result = await runner(
                db,
                user_id,
                text,
                origin="benchmark",
                allow_llm=allow_llm,
            )
            total_ms = int((time.perf_counter() - started) * 1000)
            results.append(
                BenchmarkResult(
                    message=text,
                    total_ms=total_ms,
                    first_response_ms=first_ms,
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
                    total_ms=total_ms,
                    first_response_ms=first_ms,
                    status="ERROR",
                    error=str(exc),
                )
            )
    return results


def format_benchmark_report(results: list[BenchmarkResult]) -> str:
    lines: list[str] = []
    for item in results:
        lines.append(f"Mensagem: {item.message}")
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


def save_benchmark_report(results: list[BenchmarkResult], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [item.model_dump() for item in results]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
