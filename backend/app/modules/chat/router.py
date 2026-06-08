"""Chat API routes."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_id, get_db
from app.core.pagination import PaginationParams
from app.core.schemas import APIResponse
from app.modules.chat.schemas import (
    ChatMessageRequest,
    ChatMessageResult,
    ChatMessageResponse,
)
from app.modules.chat.service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/message", response_model=APIResponse[ChatMessageResult])
async def send_message(
    data: ChatMessageRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[ChatMessageResult]:
    service = ChatService(db)
    return APIResponse(data=await service.send_message(user_id, data))


@router.get("/sessions", response_model=APIResponse)
async def list_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    service = ChatService(db)
    pagination = PaginationParams(page=page, page_size=page_size)
    return APIResponse(data=await service.list_sessions(user_id, pagination))


@router.get("/sessions/{session_id}/messages", response_model=APIResponse)
async def list_session_messages(
    session_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    service = ChatService(db)
    pagination = PaginationParams(page=page, page_size=page_size)
    return APIResponse(data=await service.list_messages(session_id, user_id, pagination))


@router.delete("/sessions/{session_id}", response_model=APIResponse[None])
async def delete_session(
    session_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[None]:
    service = ChatService(db)
    await service.delete_session(session_id, user_id)
    return APIResponse(data=None)
