"""Application configuration via environment variables."""

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]
BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(BACKEND_DIR / ".env", ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "COPILOTO"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = False
    sqlalchemy_echo: bool = False
    database_url: str = Field(
        default="postgresql+asyncpg://copiloto:change_me_secure_password@localhost:5432/copiloto"
    )
    redis_url: str = "redis://localhost:6379/0"
    log_level: str = "INFO"
    timezone: str = "America/Sao_Paulo"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model_fast: str = "qwen3:4b"
    ollama_model_main: str = "mistral:7b"
    ollama_model_embed: str = "nomic-embed-text"
    ollama_context_size: int = 4096
    ollama_keep_alive: str = "5m"
    ollama_timeout_seconds: float = 45.0
    cache_enabled: bool = True
    single_user_mode: bool = True
    default_user_id: str = "00000000-0000-4000-a000-000000000001"
    auth_enabled: bool = False
    jwt_secret_key: str = Field(
        default="change_me_jwt_secret_key_min_32_chars",
        description="Replace in production",
    )
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 30
    cookie_secure: bool = False
    rate_limit_enabled: bool = True
    telegram_enabled: bool = False
    telegram_bot_token: str = ""
    telegram_allowed_user_id: str = ""
    scheduler_enabled: bool = False
    checkin_morning_time: str = "07:00"
    checkin_noon_time: str = "12:00"
    checkin_evening_time: str = "18:00"
    checkin_night_time: str = "22:00"
    daily_summary_time: str = "23:00"
    weekly_summary_day: str = "sunday"
    weekly_summary_time: str = "20:00"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, value: str | List[str]) -> str:
        if isinstance(value, list):
            return ",".join(value)
        return value

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
