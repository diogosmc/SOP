"""Tests for Ollama model name helpers."""

from app.ai.model_utils import extract_model_names, find_missing_models, model_is_available


def test_extract_model_names() -> None:
    raw = [{"name": "mistral:7b"}, {"name": "nomic-embed-text:latest"}]
    assert extract_model_names(raw) == ["mistral:7b", "nomic-embed-text:latest"]


def test_model_is_available_with_latest_suffix() -> None:
    installed = ["nomic-embed-text:latest", "mistral:7b"]
    assert model_is_available("nomic-embed-text", installed)
    assert model_is_available("mistral:7b", installed)


def test_find_missing_models() -> None:
    installed = ["qwen2.5:1.5b", "mistral:7b"]
    configured = {"fast": "qwen2.5:1.5b", "main": "mistral:7b", "embed": "nomic-embed-text"}
    missing = find_missing_models(configured, installed)
    assert missing == ["nomic-embed-text"]
