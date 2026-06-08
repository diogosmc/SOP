"""Fase 02 — verificação dos arquivos Docker Compose."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent

COMPOSE_FILE = ROOT / "docker-compose.yml"
INIT_SQL = ROOT / "docker" / "postgres" / "init.sql"
ENV_EXAMPLE = ROOT / ".env.example"


def _load_compose() -> dict:
    with COMPOSE_FILE.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_docker_files_exist() -> None:
    assert COMPOSE_FILE.is_file(), "docker-compose.yml ausente"
    assert INIT_SQL.is_file(), "docker/postgres/init.sql ausente"
    assert ENV_EXAMPLE.is_file(), ".env.example ausente"


def test_init_sql_enables_extensions() -> None:
    content = INIT_SQL.read_text(encoding="utf-8")
    assert "CREATE EXTENSION IF NOT EXISTS vector" in content
    assert 'CREATE EXTENSION IF NOT EXISTS "uuid-ossp"' in content


def test_compose_has_postgres_and_redis() -> None:
    compose = _load_compose()
    services = compose.get("services", {})
    assert "postgres" in services
    assert "redis" in services


def test_compose_postgres_config() -> None:
    pg = _load_compose()["services"]["postgres"]
    assert pg["image"] == "pgvector/pgvector:pg16"
    assert pg["container_name"] == "copiloto_postgres"
    port_mapping = pg["ports"][0]
    assert ":5432" in port_mapping
    assert "5432" in port_mapping
    assert "postgres_data" in pg["volumes"][0]
    assert "healthcheck" in pg
    assert "pg_isready" in pg["healthcheck"]["test"][1]


def test_compose_redis_config() -> None:
    redis = _load_compose()["services"]["redis"]
    assert redis["image"] == "redis:7-alpine"
    assert redis["container_name"] == "copiloto_redis"
    port_mapping = redis["ports"][0]
    assert ":6379" in port_mapping
    assert "6379" in port_mapping
    assert "redis_data" in redis["volumes"][0]
    assert "healthcheck" in redis
    cmd = redis["command"]
    assert "redis-server" in cmd
    assert "--appendonly" in cmd
    assert "yes" in cmd
    assert "--maxmemory" in cmd
    assert "512mb" in cmd
    assert "--maxmemory-policy" in cmd
    assert "allkeys-lru" in cmd


def test_compose_volumes_defined() -> None:
    volumes = _load_compose().get("volumes", {})
    assert "postgres_data" in volumes
    assert "redis_data" in volumes


def test_env_example_has_database_and_redis_vars() -> None:
    content = ENV_EXAMPLE.read_text(encoding="utf-8")
    for var in (
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_DB",
        "POSTGRES_HOST",
        "POSTGRES_PORT",
        "DATABASE_URL",
        "REDIS_HOST",
        "REDIS_PORT",
        "REDIS_URL",
    ):
        assert var in content, f"Variável ausente em .env.example: {var}"
