"""Tests for rule-based message classifier."""

from app.ai.memory.classifier import classify_message


def test_classify_message_study() -> None:
    result = classify_message("Tenho dificuldade em física")
    assert result["intent"] == "study_log"
    assert "study" in result["categories"]
    assert result["should_save_memory"] is True


def test_classify_message_expense() -> None:
    result = classify_message("Gastei 25 no almoço")
    assert result["intent"] == "expense_log"
    assert "finance" in result["categories"]
    assert result["entities"].get("amount") == 25.0


def test_classify_message_workout() -> None:
    result = classify_message("Treinei pernas na academia hoje")
    assert result["intent"] == "workout_log"
    assert "workout" in result["categories"]


def test_classify_message_emotional() -> None:
    result = classify_message("Estou desanimado hoje")
    assert result["intent"] == "emotional_checkin"
    assert "emotional" in result["categories"]
