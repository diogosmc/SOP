"""Application configuration via environment variables."""

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "COPILOTO"
    app_env: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    single_user_mode: bool = True

    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: str = "http://localhost:5173"

    database_url: str = Field(
        default="postgresql+asyncpg://copiloto:change_me@localhost:5432/copiloto"
    )
    redis_url: str = "redis://localhost:6379/0"

    ollama_base_url: str = "http://localhost:11434"
    ollama_fast_model: str = "llama3.2:3b"
    ollama_main_model: str = "mistral:7b-instruct"
    ollama_embed_model: str = "nomic-embed-text"
    ollama_timeout: float = 120.0
    ollama_max_loaded_models: int = 1

    telegram_bot_token: str = ""
    telegram_allowed_user_id: str = ""
    telegram_enabled: bool = False

    jwt_secret: str = "change_me_jwt_secret_min_32_chars"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    scheduler_enabled: bool = True
    checkin_morning: str = "07:00"
    checkin_noon: str = "12:00"
    checkin_evening: str = "18:00"
    checkin_night: str = "22:00"
    daily_summary_time: str = "23:00"
    weekly_summary_day: int = 6
    weekly_summary_time: str = "20:00"

    cache_dashboard_ttl: int = 60
    cache_reports_ttl: int = 300
    cache_insights_ttl: int = 900

    rag_chunk_min: int = 500
    rag_chunk_max: int = 900
    rag_chunk_overlap: int = 100
    rag_top_k: int = 5

    default_user_id: str = "00000000-0000-0000-0000-000000000001"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, v: str | List[str]) -> str:
        if isinstance(v, list):
            return ",".join(v)
        return v

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
