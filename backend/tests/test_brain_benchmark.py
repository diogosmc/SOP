"""Tests for brain benchmarks."""

from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from app.brain.benchmarks import (
    DEFAULT_BENCHMARK_MESSAGES,
    format_benchmark_report,
    run_benchmark,
    save_benchmark_report,
)
from app.brain.schemas import BenchmarkResult


@pytest.mark.asyncio
async def test_run_benchmark_messages(db_session, default_user_id, tmp_path: Path) -> None:
    async def fake_process(db, user_id, message, **kwargs):
        from app.brain.schemas import BrainResult

        return BrainResult(response=f"OK: {message[:20]}", used_fallback=True)

    results = await run_benchmark(
        db_session,
        default_user_id,
        ["Estou desanimado hoje", "Não vlw"],
        process_func=fake_process,
    )
    assert len(results) == 2
    assert all(r.status == "OK" for r in results)
    assert "algo deu errado" not in results[0].response.lower()


def test_benchmark_report_format() -> None:
    report = format_benchmark_report(
        [
            BenchmarkResult(
                message="Teste",
                total_ms=500,
                first_response_ms=100,
                response="Resposta",
                status="OK",
            )
        ]
    )
    assert "Mensagem: Teste" in report
    assert "Status: OK" in report


def test_save_benchmark_report(tmp_path: Path) -> None:
    path = tmp_path / "benchmark.json"
    save_benchmark_report(
        [BenchmarkResult(message="x", total_ms=1, first_response_ms=1)],
        path,
    )
    assert path.exists()
