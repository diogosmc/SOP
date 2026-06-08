"""Basic configuration tests."""

from app.core.config import get_settings


def test_settings_load() -> None:
    settings = get_settings()
    assert settings.app_name == "COPILOTO"
    assert settings.ollama_fast_model
    assert settings.database_url.startswith("postgresql")


def test_cors_origins_list() -> None:
    settings = get_settings()
    assert isinstance(settings.cors_origins_list, list)
