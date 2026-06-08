"""COPILOTO FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.db.redis import close_redis
from app.db.session import dispose_engine
from app.middleware.error_handler import register_error_handlers
from app.middleware.auth import AuthMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_logger import RequestLoggerMiddleware
from app.modules.ai.router import router as ai_router
from app.modules.auth.router import router as auth_router
from app.modules.chat.router import router as chat_router
from app.modules.finance.router import router as finance_router
from app.modules.habits.router import router as habits_router
from app.modules.memory.router import router as memory_router
from app.modules.notes.router import router as notes_router
from app.modules.reminders.router import router as reminders_router
from app.modules.reports.router import router as reports_router
from app.modules.study.router import router as study_router
from app.modules.workout.router import router as workout_router
from app.modules.tasks.router import router as tasks_router
from app.scheduler.app import start_scheduler, stop_scheduler
from app.telegram.bot import start_telegram_bot, stop_telegram_bot
from app.websocket.chat import router as websocket_chat_router

_logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    setup_logging(settings.log_level)
    try:
        await start_telegram_bot()
    except Exception:
        _logger.exception("telegram_start_failed")
    try:
        await start_scheduler()
    except Exception:
        _logger.exception("scheduler_start_failed")
    yield
    try:
        await stop_scheduler()
    except Exception:
        _logger.exception("scheduler_stop_failed")
    try:
        await stop_telegram_bot()
    except Exception:
        _logger.exception("telegram_stop_failed")
    await close_redis()
    await dispose_engine()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        lifespan=lifespan,
    )

    register_error_handlers(app)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestLoggerMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(AuthMiddleware)

    app.include_router(health_router)
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(tasks_router, prefix="/api/v1")
    app.include_router(habits_router, prefix="/api/v1")
    app.include_router(notes_router, prefix="/api/v1")
    app.include_router(finance_router, prefix="/api/v1")
    app.include_router(study_router, prefix="/api/v1")
    app.include_router(workout_router, prefix="/api/v1")
    app.include_router(reports_router, prefix="/api/v1")
    app.include_router(reminders_router, prefix="/api/v1")
    app.include_router(ai_router, prefix="/api/v1")
    app.include_router(chat_router, prefix="/api/v1")
    app.include_router(memory_router, prefix="/api/v1")
    app.include_router(websocket_chat_router)
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    cfg = get_settings()
    uvicorn.run(
        "app.main:app",
        host=cfg.app_host,
        port=cfg.app_port,
        reload=cfg.debug,
    )
