"""Settings loading tests."""

from app.core.config import Settings, get_settings


def test_settings_load_defaults() -> None:
    settings = Settings()
    assert settings.app_name == "COPILOTO"
    assert settings.app_host == "0.0.0.0"
    assert settings.app_port == 8000
    assert settings.database_url.startswith("postgresql+asyncpg://")
    assert settings.redis_url.startswith("redis://")
    assert settings.timezone == "America/Sao_Paulo"
    assert settings.ollama_base_url == "http://localhost:11434"
    assert settings.sqlalchemy_echo is False


def test_settings_cached_singleton() -> None:
    get_settings.cache_clear()
    first = get_settings()
    second = get_settings()
    assert first is second


def test_cors_origins_list() -> None:
    settings = Settings(cors_origins="http://a.test,http://b.test")
    assert settings.cors_origins_list == ["http://a.test", "http://b.test"]
