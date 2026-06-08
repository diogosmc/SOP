"""Alembic configuration tests."""

from pathlib import Path

import pytest
from alembic.config import Config

BACKEND_DIR = Path(__file__).resolve().parents[1]


def test_alembic_ini_exists() -> None:
    assert (BACKEND_DIR / "alembic.ini").is_file()


def test_alembic_env_exists() -> None:
    assert (BACKEND_DIR / "alembic" / "env.py").is_file()


def test_alembic_versions_exist() -> None:
    versions = BACKEND_DIR / "alembic" / "versions"
    assert versions.is_dir()
    migrations = list(versions.glob("*.py"))
    assert migrations, "Nenhuma migration encontrada"


def test_alembic_config_loads_database_url() -> None:
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    from app.core.config import get_settings

    get_settings.cache_clear()
    settings = get_settings()
    cfg.set_main_option("sqlalchemy.url", settings.database_url)
    url = cfg.get_main_option("sqlalchemy.url")
    assert url is not None
    assert url.startswith("postgresql")


@pytest.mark.integration
def test_alembic_upgrade_and_downgrade() -> None:
    """Requires PostgreSQL via Docker."""
    import subprocess

    result_up = subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=BACKEND_DIR,
        capture_output=True,
        text=True,
    )
    assert result_up.returncode == 0, result_up.stderr

    result_down = subprocess.run(
        ["alembic", "downgrade", "base"],
        cwd=BACKEND_DIR,
        capture_output=True,
        text=True,
    )
    assert result_down.returncode == 0, result_down.stderr

    result_up_again = subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=BACKEND_DIR,
        capture_output=True,
        text=True,
    )
    assert result_up_again.returncode == 0, result_up_again.stderr


@pytest.mark.integration
def test_postgres_extensions_and_users_table() -> None:
    """Requires PostgreSQL via Docker after migration."""
    import asyncio

    from sqlalchemy import text

    from app.db.session import engine

    async def _check() -> None:
        async with engine.connect() as conn:
            ext_result = await conn.execute(
                text(
                    "SELECT extname FROM pg_extension "
                    "WHERE extname IN ('vector', 'uuid-ossp')"
                )
            )
            extensions = {row[0] for row in ext_result.fetchall()}
            assert "vector" in extensions
            assert "uuid-ossp" in extensions

            table_result = await conn.execute(
                text(
                    "SELECT EXISTS ("
                    "SELECT 1 FROM information_schema.tables "
                    "WHERE table_name = 'users'"
                    ")"
                )
            )
            assert table_result.scalar() is True

    asyncio.run(_check())
