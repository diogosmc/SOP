"""Chat repository."""

import uuid
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.chat.models import ChatMessage, ChatOrigin, ChatSession, MessageRole


class ChatRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_session(
        self,
        user_id: uuid.UUID,
        origin: ChatOrigin,
        title: Optional[str] = None,
    ) -> ChatSession:
        session = ChatSession(user_id=user_id, origin=origin, title=title)
        self.db.add(session)
        await self.db.flush()
        await self.db.refresh(session)
        return session

    async def get_session(
        self, session_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[ChatSession]:
        result = await self.db.execute(
            select(ChatSession).where(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_sessions(
        self,
        user_id: uuid.UUID,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[ChatSession], int]:
        query = select(ChatSession).where(ChatSession.user_id == user_id)
        count_query = (
            select(func.count()).select_from(ChatSession).where(ChatSession.user_id == user_id)
        )
        query = query.order_by(ChatSession.updated_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        count_result = await self.db.execute(count_query)
        return list(result.scalars().all()), count_result.scalar_one()

    async def update_session_title(self, session: ChatSession, title: str) -> ChatSession:
        session.title = title
        await self.db.flush()
        await self.db.refresh(session)
        return session

    async def delete_session(self, session: ChatSession) -> None:
        await self.db.delete(session)
        await self.db.flush()

    async def create_message(
        self,
        session_id: uuid.UUID,
        role: MessageRole,
        content: str,
        model_used: Optional[str] = None,
        response_time_ms: Optional[int] = None,
    ) -> ChatMessage:
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            model_used=model_used,
            response_time_ms=response_time_ms,
        )
        self.db.add(message)
        await self.db.flush()
        await self.db.refresh(message)
        return message

    async def list_all_messages(self, session_id: uuid.UUID) -> List[ChatMessage]:
        result = await self.db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
        )
        return list(result.scalars().all())

    async def list_messages(
        self, session_id: uuid.UUID, offset: int, limit: int
    ) -> tuple[List[ChatMessage], int]:
        count_result = await self.db.execute(
            select(func.count())
            .select_from(ChatMessage)
            .where(ChatMessage.session_id == session_id)
        )
        total = count_result.scalar_one()
        result = await self.db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all()), total
