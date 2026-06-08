"""Auth API routes with HttpOnly cookie tokens."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.deps import get_current_user_id, get_db
from app.core.schemas import APIResponse
from app.core.security import (
    TOKEN_TYPE_REFRESH,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.modules.auth.schemas import (
    BootstrapAdminRequest,
    BootstrapAvailableResponse,
    LoginRequest,
    LoginResponse,
    UserResponse,
)
from app.modules.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"


def _set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
    settings: Settings,
) -> None:
    response.set_cookie(
        key=ACCESS_COOKIE,
        value=access_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=settings.jwt_access_token_expire_minutes * 60,
        path="/",
    )
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=refresh_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=settings.jwt_refresh_token_expire_days * 86400,
        path="/",
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(key=ACCESS_COOKIE, path="/")
    response.delete_cookie(key=REFRESH_COOKIE, path="/")


@router.get("/bootstrap-available", response_model=APIResponse[BootstrapAvailableResponse])
async def bootstrap_available(
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> APIResponse[BootstrapAvailableResponse]:
    service = AuthService(db)
    return APIResponse(
        data=BootstrapAvailableResponse(
            available=await service.bootstrap_available(),
            auth_enabled=settings.auth_enabled,
        )
    )


@router.post("/bootstrap-admin", response_model=APIResponse[LoginResponse])
async def bootstrap_admin(
    data: BootstrapAdminRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> APIResponse[LoginResponse]:
    service = AuthService(db)
    user = await service.bootstrap_admin(data)
    access = create_access_token(str(user.id), settings)
    refresh = create_refresh_token(str(user.id), settings)
    _set_auth_cookies(response, access, refresh, settings)
    return APIResponse(
        data=LoginResponse(
            user=UserResponse.model_validate(user),
            access_token=access,
        )
    )


@router.post("/login", response_model=APIResponse[LoginResponse])
async def login(
    data: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> APIResponse[LoginResponse]:
    service = AuthService(db)
    user = await service.authenticate(data)
    access = create_access_token(str(user.id), settings)
    refresh = create_refresh_token(str(user.id), settings)
    _set_auth_cookies(response, access, refresh, settings)
    return APIResponse(
        data=LoginResponse(
            user=UserResponse.model_validate(user),
            access_token=access,
        )
    )


@router.post("/logout", response_model=APIResponse[None])
async def logout(response: Response) -> APIResponse[None]:
    _clear_auth_cookies(response)
    return APIResponse(data=None)


@router.post("/refresh", response_model=APIResponse[None])
async def refresh_token(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> APIResponse[None]:
    token = request.cookies.get(REFRESH_COOKIE)
    if not token:
        _clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )

    payload = decode_token(token, settings, expected_type=TOKEN_TYPE_REFRESH)
    if not payload or not payload.get("sub"):
        _clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id = uuid.UUID(payload["sub"])
    service = AuthService(db)
    user = await service.get_user_by_id(user_id)
    if user is None or not user.is_active:
        _clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    access = create_access_token(str(user.id), settings)
    refresh = create_refresh_token(str(user.id), settings)
    _set_auth_cookies(response, access, refresh, settings)
    return APIResponse(data=None)


@router.get("/me", response_model=APIResponse[UserResponse])
async def get_me(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[UserResponse]:
    service = AuthService(db)
    return APIResponse(data=await service.get_me(user_id))
