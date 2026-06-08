"""Authentication service."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.modules.auth.schemas import BootstrapAdminRequest, LoginRequest, UserResponse
from app.modules.users.models import User


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_user_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def has_password_user(self) -> bool:
        result = await self.db.execute(
            select(func.count()).select_from(User).where(User.hashed_password.isnot(None))
        )
        return result.scalar_one() > 0

    async def bootstrap_available(self) -> bool:
        return not await self.has_password_user()

    async def bootstrap_admin(self, data: BootstrapAdminRequest) -> User:
        if await self.has_password_user():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bootstrap admin is no longer available",
            )
        existing = await self.get_user_by_email(data.email)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )
        user = User(
            name=data.name,
            email=data.email,
            hashed_password=hash_password(data.password),
            is_active=True,
            is_admin=True,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def authenticate(self, data: LoginRequest) -> User:
        user = await self.get_user_by_email(data.email)
        if user is None or not verify_password(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive",
            )
        return user

    async def get_me(self, user_id: uuid.UUID) -> UserResponse:
        user = await self.get_user_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return UserResponse.model_validate(user)
