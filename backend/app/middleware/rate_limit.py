"""Redis-backed rate limiting middleware."""

import logging

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import get_settings
from app.core.schemas import APIError, ErrorResponse
from app.db.redis import get_redis_client

logger = logging.getLogger(__name__)

DEFAULT_LIMIT = 120
DEFAULT_WINDOW = 60

STRICT_LIMITS: dict[str, tuple[int, int]] = {
    "/api/v1/auth/login": (10, 60),
    "/api/v1/auth/bootstrap-admin": (5, 300),
    "/api/v1/chat/message": (40, 60),
}

EXEMPT_PREFIXES = ("/health", "/docs", "/openapi.json", "/redoc")


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        settings = get_settings()
        if not settings.rate_limit_enabled:
            return await call_next(request)

        path = request.url.path
        if any(path.startswith(prefix) for prefix in EXEMPT_PREFIXES):
            return await call_next(request)

        limit, window = STRICT_LIMITS.get(path, (DEFAULT_LIMIT, DEFAULT_WINDOW))
        client_ip = request.client.host if request.client else "unknown"
        key = f"rate_limit:{client_ip}:{request.method}:{path}"

        try:
            redis = get_redis_client()
            count = await redis.incr(key)
            if count == 1:
                await redis.expire(key, window)
            if count > limit:
                return JSONResponse(
                    status_code=429,
                    content=ErrorResponse(
                        error=APIError(message="Too many requests. Please try again later.")
                    ).model_dump(),
                )
        except Exception:
            logger.warning("rate_limit_redis_unavailable", extra={"path": path})

        return await call_next(request)
