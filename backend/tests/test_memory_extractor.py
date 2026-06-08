"""Tests for memory candidate extraction."""

from app.ai.memory.classifier import classify_message
from app.ai.memory.extractor import extract_memory_candidates


def test_extract_memory_candidates_medicina_goal() -> None:
    text = "Quero passar em Medicina"
    classification = classify_message(text)
    candidates = extract_memory_candidates(text, classification)

    assert candidates
    assert candidates[0]["type"] == "goal"
    assert "medicina" in candidates[0]["content"].lower()
    assert candidates[0]["importance"] >= 7
    assert candidates[0]["confidence"] >= 0.8
