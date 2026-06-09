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


def test_tired_defer_study_not_appointment() -> None:
    result = classify_telegram_message(
        "Cheguei em casa agora to cansado acho que vou deixar a faculdade pra amanha"
    )
    assert result["primary_intent"] == "emotional_checkin"
    assert "study_plan" in result["secondary_intents"]
    assert result["primary_intent"] != "appointment"
    assert not result.get("explicit_appointment")


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
                settings.ollama_model_fast = "qwen2.5:1.5b"
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


def test_facul_atrasada_not_study_log() -> None:
    result = classify_telegram_message(
        "To de boa então acho que vou precisar adiantar as materia da facul to atrasadao"
    )
    assert result["primary_intent"] == "planning_request"
    assert result["primary_intent"] != "study_log"


def test_wake_time_not_expense() -> None:
    result = classify_telegram_message(
        "Então o que voce recomenda pra amanha vou ter que acodar 6:20 da manhã"
    )
    assert result["primary_intent"] == "planning_request"
    assert "expense_log" not in result.get("secondary_intents", [])
    assert result["primary_intent"] != "expense_log"
    from app.brain.llm_policy import should_use_llm

    ctx = ConversationContext(
        message=result.get("entities", {}).get("raw_message", ""),
        intent=result["primary_intent"],
        primary_intent=result["primary_intent"],
        secondary_intents=result.get("secondary_intents", []),
        origin="telegram",
    )
    assert should_use_llm(
        "Então o que voce recomenda pra amanha vou ter que acodar 6:20 da manhã",
        ctx,
        "hybrid",
    )


def test_should_use_llm_hybrid_workout_no_llm() -> None:
    context = ConversationContext(
        message="Vou treinar peito hoje",
        intent="workout_log",
        primary_intent="workout_log",
    )
    assert not should_use_llm(context.message, context, "hybrid")


def test_greeting_boa_noite() -> None:
    from app.brain.companion import greeting_fallback, is_social_greeting

    assert is_social_greeting("Boa noite !")
    reply = greeting_fallback("Boa noite !")
    assert "noite" in reply.lower()
    assert "anotei" not in reply.lower()


@pytest.mark.asyncio
async def test_greeting_uses_companion_not_generic(db_session, default_user_id) -> None:
    with patch("app.brain.response_generator.check_ollama_health", new=AsyncMock(return_value=False)):
        result = await process_message(
            db_session,
            default_user_id,
            "Boa noite !",
            origin="telegram",
            allow_llm=True,
            response_mode="hybrid",
        )
    assert "contexto para te responder" not in result.response.lower()
    assert "noite" in result.response.lower() or "aqui" in result.response.lower()


def test_should_use_llm_hybrid_mixed_uses_llm() -> None:
    context = ConversationContext(
        message="Amanha vou levantar cedo pra trabalhar e to com uma preguiça gigante",
        intent="routine_planning",
        primary_intent="routine_planning",
        secondary_intents=["emotional_checkin"],
    )
    assert should_use_llm(context.message, context, "hybrid")


def test_finance_stress_not_appointment() -> None:
    result = classify_telegram_message(
        "Preciso que chegue logo final do mes, esse mes eu nao posso gastar com mais nada"
    )
    assert result["primary_intent"] == "general_chat"
    assert result["primary_intent"] != "appointment"


def test_deny_autoescola_not_appointment() -> None:
    result = classify_telegram_message(
        "Não minha rotina amanha é a seguinte vou levantar 06:20 da manha, "
        "depois vou para o trabalho e vou ficar lá de 07:40 até 17:40 e depois "
        "vou para casa, amanhã eu nao tenho auto escola vou só na academia"
    )
    assert result["primary_intent"] != "appointment"
    assert result["primary_intent"] in {
        "routine_planning",
        "general_chat",
        "workout_log",
        "planning_request",
    }


def test_goal_moto_classification() -> None:
    result = classify_telegram_message("Me sentiria bem, eu quero juntar para comprar minha moto")
    assert result["primary_intent"] == "goal_update"


def test_companion_memory_filter_drops_autoescola() -> None:
    from app.brain.companion import filter_memories_for_message
    from app.brain.schemas import MemorySnippet

    snippets = [
        MemorySnippet(content="Amanhã autoescola às 8h", memory_type="reminder", importance=9),
        MemorySnippet(content="Meta: comprar moto", memory_type="goal", importance=8),
    ]
    filtered = filter_memories_for_message(
        "amanhã eu nao tenho auto escola vou só na academia", snippets
    )
    assert all("autoescola" not in s.content.lower() for s in filtered)
    assert any("moto" in s.content.lower() for s in filtered)


def test_companion_filters_wrong_assistant_turns() -> None:
    from app.brain.companion import filter_recent_messages_for_context

    recent = [
        {"role": "user", "content": "Preciso que chegue logo final do mes"},
        {"role": "assistant", "content": "Amanhã tem autoescola às 8h, não é certo adiar?"},
        {"role": "user", "content": "amanhã eu nao tenho auto escola vou só na academia"},
    ]
    filtered = filter_recent_messages_for_context(recent[-1]["content"], recent)
    assistant_texts = [m["content"] for m in filtered if m["role"] == "assistant"]
    assert not any("autoescola" in t.lower() for t in assistant_texts)


def test_sanitize_strips_repetitive_therapist_questions() -> None:
    from app.brain.response_generator import _sanitize_companion_response

    raw = (
        "Entendi. Você quer juntar dinheiro.\n\n"
        "Como você se sente sobre essas responsabilidades?\n\n"
        "Você tem planos para o próximo mês ou algum objetivo?"
    )
    cleaned = _sanitize_companion_response(raw)
    assert "como você se sente" not in cleaned.lower()
    assert "próximo mês" not in cleaned.lower()
    assert "juntar dinheiro" in cleaned.lower()


def test_list_tomorrow_request_detected() -> None:
    from app.brain.schedule_builder import is_tomorrow_list_request

    assert is_tomorrow_list_request("Listar o que eu vou fazer amanhã")
    assert is_tomorrow_list_request("Liste minhas tarefas para amanhã")
    assert is_tomorrow_list_request("Então liste exatamente o dia de amanhã")
    assert not is_tomorrow_list_request("Amanhã vou trabalhar cedo")


def test_list_tomorrow_builds_from_recent_context() -> None:
    from app.brain.schedule_builder import build_tomorrow_schedule_reply

    context = ConversationContext(
        message="Então liste exatamente o dia de amanhã",
        recent_messages=[
            {
                "role": "user",
                "content": (
                    "Não po amanha eu vou levantar 06:20 da manha e ir pra trabalho "
                    "de 07:40 até 17:40 e depois vou na academia"
                ),
            },
        ],
    )
    reply = build_tomorrow_schedule_reply(context)
    assert "06:20" in reply
    assert "07:40" in reply
    assert "17:40" in reply
    assert "Academia" in reply
    assert "moto" not in reply.lower()


def test_list_tomorrow_skips_llm_in_hybrid() -> None:
    context = ConversationContext(
        message="Listar o que eu vou fazer amanhã",
        intent="planning_request",
        primary_intent="planning_request",
    )
    assert not should_use_llm(context.message, context, "hybrid")
