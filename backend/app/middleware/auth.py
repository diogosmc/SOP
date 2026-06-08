"""JWT authentication middleware."""

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import get_settings
from app.core.schemas import APIError, ErrorResponse
from app.core.security import TOKEN_TYPE_ACCESS, decode_token

ACCESS_COOKIE = "access_token"

PUBLIC_EXACT = {
    "/health",
    "/openapi.json",
    "/redoc",
}

PUBLIC_PREFIXES = (
    "/docs",
    "/api/v1/debug",
    "/api/v1/ai/health",
    "/api/v1/ai/models",
    "/api/v1/auth/login",
    "/api/v1/auth/logout",
    "/api/v1/auth/bootstrap-admin",
    "/api/v1/auth/refresh",
    "/api/v1/auth/bootstrap-available",
)


def _is_public_path(path: str) -> bool:
    if path in PUBLIC_EXACT:
        return True
    if any(path.startswith(prefix) for prefix in PUBLIC_PREFIXES):
        return True
    if path.endswith("/health"):
        return True
    return False


def _extract_user_id(request: Request) -> None:
    token = request.cookies.get(ACCESS_COOKIE)
    if not token:
        return
    payload = decode_token(token, get_settings(), expected_type=TOKEN_TYPE_ACCESS)
    if payload and payload.get("sub"):
        request.state.user_id = payload["sub"]


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        settings = get_settings()
        path = request.url.path

        if not settings.auth_enabled:
            _extract_user_id(request)
            return await call_next(request)

        if _is_public_path(path):
            _extract_user_id(request)
            return await call_next(request)

        _extract_user_id(request)

        if path.startswith("/api/v1") and not getattr(request.state, "user_id", None):
            return JSONResponse(
                status_code=401,
                content=ErrorResponse(
                    error=APIError(message="Not authenticated")
                ).model_dump(),
            )

        return await call_next(request)
