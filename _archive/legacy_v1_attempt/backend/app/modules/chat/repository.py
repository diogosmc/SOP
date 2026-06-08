"""Chat session and message persistence."""

import uuid
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.chat.models import ChatMessage, ChatMode, ChatSession, MessageRole


class ChatRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_session(
        self,
        user_id: uuid.UUID,
        mode: ChatMode = ChatMode.GENERAL,
        title: Optional[str] = None,
    ) -> ChatSession:
        session = ChatSession(user_id=user_id, mode=mode, title=title)
        self.db.add(session)
        await self.db.flush()
        await self.db.refresh(session)
        return session

    async def get_session(
        self, session_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[ChatSession]:
        result = await self.db.execute(
            select(ChatSession).where(
                ChatSession.id == session_id, ChatSession.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def list_sessions(
        self, user_id: uuid.UUID, offset: int = 0, limit: int = 20
    ) -> Tuple[List[ChatSession], int]:
        query = (
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .order_by(ChatSession.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        count_query = (
            select(func.count())
            .select_from(ChatSession)
            .where(ChatSession.user_id == user_id)
        )
        result = await self.db.execute(query)
        count_result = await self.db.execute(count_query)
        return list(result.scalars().all()), count_result.scalar_one()

    async def create_message(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
        role: MessageRole,
        content: str,
        model: Optional[str] = None,
        tokens: Optional[int] = None,
        metadata: Optional[dict] = None,
    ) -> ChatMessage:
        message = ChatMessage(
            session_id=session_id,
            user_id=user_id,
            role=role,
            content=content,
            model=model,
            tokens=tokens,
            metadata_=metadata,
        )
        self.db.add(message)
        await self.db.flush()
        await self.db.refresh(message)
        return message

    async def list_messages(
        self, session_id: uuid.UUID, user_id: uuid.UUID
    ) -> List[ChatMessage]:
        result = await self.db.execute(
            select(ChatMessage)
            .where(
                ChatMessage.session_id == session_id,
                ChatMessage.user_id == user_id,
            )
            .order_by(ChatMessage.created_at.asc())
        )
        return list(result.scalars().all())

    async def update_session(
        self,
        session: ChatSession,
        *,
        title: Optional[str] = None,
        model_used: Optional[str] = None,
        increment_messages: int = 0,
    ) -> ChatSession:
        if title is not None:
            session.title = title
        if model_used is not None:
            session.model_used = model_used
        if increment_messages:
            session.message_count += increment_messages
        await self.db.flush()
        await self.db.refresh(session)
        return session
