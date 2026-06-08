"""Ollama model name helpers."""

from __future__ import annotations

from typing import Any


def extract_model_names(models: list[dict[str, Any]]) -> list[str]:
    """Return model name strings from Ollama /api/tags payload."""
    names: list[str] = []
    for item in models:
        name = item.get("name") or item.get("model")
        if isinstance(name, str) and name:
            names.append(name)
    return names


def model_is_available(configured: str, installed: list[str]) -> bool:
    """Match configured name against installed names (supports :latest suffix)."""
    if not configured:
        return False
    if configured in installed:
        return True

    configured_base = configured.split(":")[0]
    for name in installed:
        if name == configured:
            return True
        if name.startswith(f"{configured_base}:"):
            return True
        if name.split(":")[0] == configured_base:
            return True
    return False


def find_missing_models(configured: dict[str, str], installed: list[str]) -> list[str]:
    """Return configured model names that are not installed."""
    missing: list[str] = []
    for name in configured.values():
        if name and not model_is_available(name, installed):
            missing.append(name)
    return missing
