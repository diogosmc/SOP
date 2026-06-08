"""JWT authentication middleware — reads access token from HttpOnly cookie."""

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import get_settings
from app.core.security import TOKEN_TYPE_ACCESS, decode_token

PUBLIC_PREFIXES = (
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/auth/login",
    "/auth/refresh",
    "/api/v1/auth/login",
    "/api/v1/auth/refresh",
)


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        path = request.url.path
        if any(path == prefix or path.startswith(f"{prefix}/") for prefix in PUBLIC_PREFIXES):
            return await call_next(request)
        if path.endswith("/health"):
            return await call_next(request)

        token = request.cookies.get("access_token")
        if token:
            payload = decode_token(token, get_settings(), expected_type=TOKEN_TYPE_ACCESS)
            if payload and payload.get("sub"):
                request.state.user_id = payload["sub"]

        return await call_next(request)
