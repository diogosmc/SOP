"""Request timing and logging middleware."""

import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger

logger = get_logger(__name__)

SENSITIVE_PATHS = ("/auth/login", "/auth/bootstrap-admin")


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        path = request.url.path
        log_path = "[redacted]" if any(s in path for s in SENSITIVE_PATHS) else path

        logger.info(
            "request",
            method=request.method,
            path=log_path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            client=request.client.host if request.client else None,
        )
        response.headers["X-Response-Time"] = f"{duration_ms}ms"
        return response
