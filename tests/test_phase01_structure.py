"""Fase 01 — verificação da estrutura do projeto."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REQUIRED_DIRS = [
    "backend",
    "frontend",
    "scripts",
    "docs",
    "tests",
    "backups",
]

REQUIRED_FILES = [
    "README.md",
    ".gitignore",
    ".env.example",
    "docker-compose.yml",
]


def test_required_directories_exist() -> None:
    for name in REQUIRED_DIRS:
        path = ROOT / name
        assert path.is_dir(), f"Diretório ausente: {name}"


def test_required_files_exist() -> None:
    for name in REQUIRED_FILES:
        path = ROOT / name
        assert path.is_file(), f"Arquivo ausente: {name}"


def test_gitignore_covers_env_and_cache() -> None:
    content = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert ".env" in content
    assert "__pycache__" in content
    assert "node_modules" in content
