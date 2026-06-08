"""Tests for HOTFIX V1.5.1 — hybrid LLM, mixed classification, streaming."""

from __future__ import annotations

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.brain.benchmarks import BENCHMARK_MODES, run_all_mode_benchmarks, run_benchmark
from app.brain.conversation_manager import process_message
from app.brain.llm_policy import should_use_llm
from app.brain.ollama_warmup import warmup_ollama_fast_model
from app.brain.response_generator import generate_response
from app.brain.schemas import BrainAction, ConversationContext, ConversationState
from app.brain.state_manager import reset_user_state, update_state_from_message
from app.brain.telegram_streamer import stream_telegram_response
from app.telegram.instructor import classify_telegram_message


def test_mixed_work_preguica_classification() -> None:
    result = classify_telegram_message(
        "Amanha vou levantar cedo pra trabalhar e to com uma preguiça gigante"
    )
    assert result["primary_intent"] == "routine_planning"
    assert "emotional_checkin" in result["secondary_intents"]
    assert result["intent"] == "routine_planning"


@pytest.mark.asyncio
async def test_workout_after_desanimado_uses_workout_fallback(db_session, default_user_id) -> None:
    c1 = classify_telegram_message("Estou desanimado hoje")
    await update_state_from_message(
        db_session, default_user_id, "Estou desanimado hoje", c1["intent"], c1
    )
    message = "Vou treinar peito hoje"
    c2 = classify_telegram_message(message)
    state = await update_state_from_message(
        db_session, default_user_id, message, c2["intent"], c2
    )
    assert state.mood is None
    assert state.current_topic == "treino"

    context = ConversationContext(
        message=message,
        classification=c2,
        intent=c2["intent"],
        primary_intent=c2["primary_intent"],
        secondary_intents=c2.get("secondary_intents", []),
        state=state,
    )
    response, _, used_fallback = await generate_response(
        message, context, [BrainAction(action="create_workout_log", success=True)], allow_llm=False
    )
    assert "treino" in response.lower()
    assert "energia baixa" not in response.lower()
    assert used_fallback


@pytest.mark.asyncio
async def test_fallback_only_never_calls_llm() -> None:
    context = ConversationContext(
        message="Como organizar meu dia amanhã?",
        intent="planning_request",
        primary_intent="planning_request",
    )
    with patch("app.brain.response_generator.check_ollama_health", new=AsyncMock(return_value=True)):
        with patch("app.brain.response_generator.ollama_chat", new=AsyncMock()) as mock_chat:
            response, model, used_fallback = await generate_response(
                context.message,
                context,
                [],
                allow_llm=True,
                response_mode="fallback_only",
            )
    mock_chat.assert_not_called()
    assert model is None
    assert used_fallback
    assert response


@pytest.mark.asyncio
async def test_hybrid_general_chat_calls_llm() -> None:
    context = ConversationContext(
        message="Me conta uma ideia pra relaxar hoje à noite",
        intent="general_chat",
        primary_intent="general_chat",
        origin="telegram",
    )
    mock_result = {"message": {"content": "Ouve uma música calma e desliga as telas."}}
    with patch("app.brain.response_generator.check_ollama_health", new=AsyncMock(return_value=True)):
        with patch(
            "app.brain.response_generator.ollama_chat",
            new=AsyncMock(return_value=mock_result),
        ) as mock_chat:
            response, model, used_fallback = await generate_response(
                context.message,
                context,
                [],
                allow_llm=True,
                response_mode="hybrid",
            )
    mock_chat.assert_called_once()
    assert model is not None
    assert not used_fallback
    assert "música" in response.lower() or "telas" in response.lower()


@pytest.mark.asyncio
async def test_hybrid_llm_timeout_uses_fallback() -> None:
    context = ConversationContext(
        message="Estou desanimado hoje",
        intent="emotional_checkin",
        primary_intent="emotional_checkin",
        origin="telegram",
    )

    async def slow_chat(*_args, **_kwargs):
        await asyncio.sleep(10)
        return {"message": {"content": "nunca"}}

    with patch("app.brain.response_generator.check_ollama_health", new=AsyncMock(return_value=True)):
        with patch("app.brain.response_generator.ollama_chat", new=slow_chat):
            with patch("app.brain.response_generator.get_settings") as mock_settings:
                settings = mock_settings.return_value
                settings.telegram_response_mode = "hybrid"
                settings.telegram_llm_timeout_seconds = 0.1
                settings.telegram_force_fast_model = True
                settings.ollama_model_fast = "qwen3:4b"
                settings.telegram_recent_messages_limit = 6
                response, model, used_fallback = await generate_response(
                    context.message,
                    context,
                    [],
                    allow_llm=True,
                    response_mode="hybrid",
                )
    assert used_fallback
    assert model is None
    assert "energia" in response.lower() or "entendi" in response.lower()


@pytest.mark.asyncio
async def test_warmup_offline_does_not_raise() -> None:
    with patch(
        "app.brain.ollama_warmup.ollama_generate",
        new=AsyncMock(side_effect=RuntimeError("offline")),
    ):
        result = await warmup_ollama_fast_model()
    assert result is False


@pytest.mark.asyncio
async def test_streamer_first_ms_is_elapsed() -> None:
    telegram_message = MagicMock()
    sent = MagicMock()
    sent.edit_text = AsyncMock()

    async def slow_reply(*_args, **_kwargs):
        await asyncio.sleep(0.05)
        return sent

    telegram_message.reply_text = AsyncMock(side_effect=slow_reply)

    async def factory():
        from app.brain.schemas import BrainResult

        return BrainResult(response="Resposta rápida", used_fallback=True)

    with patch("app.brain.telegram_streamer.get_settings") as mock_settings:
        settings = mock_settings.return_value
        settings.telegram_streaming_enabled = False
        settings.telegram_llm_timeout_seconds = 8.0

        start = time.perf_counter()
        await stream_telegram_response(telegram_message, factory)
        elapsed = int((time.perf_counter() - start) * 1000)

    assert telegram_message.reply_text.await_count == 1
    assert elapsed < 5000


@pytest.mark.asyncio
async def test_benchmark_generates_three_modes(db_session, default_user_id) -> None:
    async def fake_process(db, user_id, message, **kwargs):
        from app.brain.schemas import BrainResult

        return BrainResult(
            response=f"OK: {message[:20]}",
            used_fallback=kwargs.get("response_mode") == "fallback_only",
            used_llm=kwargs.get("response_mode") == "llm_only",
            intent="general_chat",
        )

    grouped = await run_all_mode_benchmarks(
        db_session,
        default_user_id,
        ["Estou desanimado hoje", "Não vlw"],
        process_func=fake_process,
    )
    assert set(grouped.keys()) == set(BENCHMARK_MODES)
    for mode, results in grouped.items():
        assert len(results) == 2
        assert all(r.mode == mode for r in results)


def test_should_use_llm_hybrid_workout_no_llm() -> None:
    context = ConversationContext(
        message="Vou treinar peito hoje",
        intent="workout_log",
        primary_intent="workout_log",
    )
    assert not should_use_llm(context.message, context, "hybrid")


def test_should_use_llm_hybrid_mixed_uses_llm() -> None:
    context = ConversationContext(
        message="Amanha vou levantar cedo pra trabalhar e to com uma preguiça gigante",
        intent="routine_planning",
        primary_intent="routine_planning",
        secondary_intents=["emotional_checkin"],
    )
    assert should_use_llm(context.message, context, "hybrid")
