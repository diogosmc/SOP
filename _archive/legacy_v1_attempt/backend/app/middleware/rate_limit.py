"""Simple Redis-backed rate limiting middleware."""

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import get_settings
from app.core.schemas import APIError, ErrorResponse
from app.db.redis import get_redis_client

DEFAULT_LIMIT = 120
WINDOW_SECONDS = 60

EXEMPT_PREFIXES = ("/health", "/docs", "/openapi.json", "/redoc")


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        limit: int = DEFAULT_LIMIT,
        window_seconds: int = WINDOW_SECONDS,
    ) -> None:
        super().__init__(app)
        self.limit = limit
        self.window_seconds = window_seconds

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        path = request.url.path
        if any(path.startswith(prefix) for prefix in EXEMPT_PREFIXES):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        key = f"rate_limit:{client_ip}:{request.method}:{path}"

        try:
            redis = get_redis_client()
            count = await redis.incr(key)
            if count == 1:
                await redis.expire(key, self.window_seconds)
            if count > self.limit:
                return JSONResponse(
                    status_code=429,
                    content=ErrorResponse(
                        error=APIError(
                            code="RATE_LIMIT_EXCEEDED",
                            message="Too many requests. Please try again later.",
                        )
                    ).model_dump(),
                )
        except Exception:
            if not get_settings().debug:
                pass

        return await call_next(request)
