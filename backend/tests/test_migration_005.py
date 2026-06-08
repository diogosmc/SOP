"""Integration tests for migration 005_workout_models."""

import subprocess
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]


@pytest.mark.integration
def test_alembic_upgrade_downgrade_cycle() -> None:
    upgrade = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND_DIR,
        capture_output=True,
        text=True,
    )
    assert upgrade.returncode == 0, upgrade.stderr or upgrade.stdout

    downgrade = subprocess.run(
        [sys.executable, "-m", "alembic", "downgrade", "-1"],
        cwd=BACKEND_DIR,
        capture_output=True,
        text=True,
    )
    assert downgrade.returncode == 0, downgrade.stderr or downgrade.stdout

    reupgrade = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND_DIR,
        capture_output=True,
        text=True,
    )
    assert reupgrade.returncode == 0, reupgrade.stderr or reupgrade.stdout
