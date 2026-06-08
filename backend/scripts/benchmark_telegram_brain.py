"""Run Conversation Brain benchmark and save report."""

from __future__ import annotations

import asyncio
import sys
import uuid
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import app.db.models  # noqa: F401
from app.brain.benchmarks import (
    BENCHMARK_MODES,
    format_benchmark_report,
    run_all_mode_benchmarks,
    save_benchmark_report,
)
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.db.session import AsyncSessionLocal
from app.modules.users.service import ensure_default_user_exists


async def main() -> None:
    settings = get_settings()
    setup_logging(settings.log_level)
    user_id = uuid.UUID(settings.default_user_id)
    report_path = BACKEND_DIR / "reports" / "telegram_brain_benchmark.json"

    async with AsyncSessionLocal() as db:
        await ensure_default_user_exists(db, settings)
        grouped = await run_all_mode_benchmarks(db, user_id)
        await db.commit()

    for mode in BENCHMARK_MODES:
        print(f"\n{'=' * 40}\n{mode.upper()}\n{'=' * 40}")
        print(format_benchmark_report(grouped[mode]))

    save_benchmark_report(grouped, report_path)
    print(f"\nRelatório salvo em: {report_path}")


if __name__ == "__main__":
    asyncio.run(main())
