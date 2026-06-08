"""Study repository."""

import uuid
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.study.models import Flashcard, StudySession, StudySubject, StudyTopic, TopicStatus
from app.modules.study.schemas import (
    FlashcardCreate,
    FlashcardUpdate,
    StudySessionCreate,
    SubjectCreate,
    SubjectUpdate,
    TopicCreate,
    TopicUpdate,
)


class StudyRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # --- Subjects ---

    async def create_subject(self, user_id: uuid.UUID, data: SubjectCreate) -> StudySubject:
        subject = StudySubject(user_id=user_id, **data.model_dump())
        self.db.add(subject)
        await self.db.flush()
        await self.db.refresh(subject)
        return subject

    async def get_subject(
        self, subject_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[StudySubject]:
        result = await self.db.execute(
            select(StudySubject).where(
                StudySubject.id == subject_id, StudySubject.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def list_subjects(
        self, user_id: uuid.UUID, offset: int = 0, limit: int = 20
    ) -> Tuple[List[StudySubject], int]:
        query = (
            select(StudySubject)
            .where(StudySubject.user_id == user_id)
            .order_by(StudySubject.sort_order, StudySubject.name)
            .offset(offset)
            .limit(limit)
        )
        count_query = (
            select(func.count()).select_from(StudySubject).where(StudySubject.user_id == user_id)
        )
        result = await self.db.execute(query)
        count_result = await self.db.execute(count_query)
        return list(result.scalars().all()), count_result.scalar_one()

    async def update_subject(self, subject: StudySubject, data: SubjectUpdate) -> StudySubject:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(subject, field, value)
        await self.db.flush()
        await self.db.refresh(subject)
        return subject

    async def delete_subject(self, subject: StudySubject) -> None:
        await self.db.delete(subject)
        await self.db.flush()

    # --- Topics ---

    async def create_topic(self, user_id: uuid.UUID, data: TopicCreate) -> StudyTopic:
        topic = StudyTopic(user_id=user_id, **data.model_dump())
        self.db.add(topic)
        await self.db.flush()
        await self.db.refresh(topic)
        return topic

    async def get_topic(self, topic_id: uuid.UUID, user_id: uuid.UUID) -> Optional[StudyTopic]:
        result = await self.db.execute(
            select(StudyTopic).where(StudyTopic.id == topic_id, StudyTopic.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_topics(
        self,
        user_id: uuid.UUID,
        subject_id: Optional[uuid.UUID] = None,
        status: Optional[TopicStatus] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[StudyTopic], int]:
        filters = [StudyTopic.user_id == user_id]
        if subject_id:
            filters.append(StudyTopic.subject_id == subject_id)
        if status:
            filters.append(StudyTopic.status == status)

        query = (
            select(StudyTopic)
            .where(*filters)
            .order_by(StudyTopic.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        count_query = select(func.count()).select_from(StudyTopic).where(*filters)
        result = await self.db.execute(query)
        count_result = await self.db.execute(count_query)
        return list(result.scalars().all()), count_result.scalar_one()

    async def update_topic(self, topic: StudyTopic, data: TopicUpdate) -> StudyTopic:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(topic, field, value)
        await self.db.flush()
        await self.db.refresh(topic)
        return topic

    async def delete_topic(self, topic: StudyTopic) -> None:
        await self.db.delete(topic)
        await self.db.flush()

    # --- Flashcards ---

    async def create_flashcard(self, user_id: uuid.UUID, data: FlashcardCreate) -> Flashcard:
        flashcard = Flashcard(user_id=user_id, **data.model_dump())
        self.db.add(flashcard)
        await self.db.flush()
        await self.db.refresh(flashcard)
        return flashcard

    async def get_flashcard(
        self, flashcard_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[Flashcard]:
        result = await self.db.execute(
            select(Flashcard).where(Flashcard.id == flashcard_id, Flashcard.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_flashcards(
        self,
        user_id: uuid.UUID,
        topic_id: Optional[uuid.UUID] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Flashcard], int]:
        filters = [Flashcard.user_id == user_id]
        if topic_id:
            filters.append(Flashcard.topic_id == topic_id)

        query = (
            select(Flashcard)
            .where(*filters)
            .order_by(Flashcard.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        count_query = select(func.count()).select_from(Flashcard).where(*filters)
        result = await self.db.execute(query)
        count_result = await self.db.execute(count_query)
        return list(result.scalars().all()), count_result.scalar_one()

    async def update_flashcard(self, flashcard: Flashcard, data: FlashcardUpdate) -> Flashcard:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(flashcard, field, value)
        await self.db.flush()
        await self.db.refresh(flashcard)
        return flashcard

    async def delete_flashcard(self, flashcard: Flashcard) -> None:
        await self.db.delete(flashcard)
        await self.db.flush()

    # --- Sessions ---

    async def create_session(self, user_id: uuid.UUID, data: StudySessionCreate) -> StudySession:
        session = StudySession(user_id=user_id, **data.model_dump())
        self.db.add(session)
        await self.db.flush()
        await self.db.refresh(session)
        return session

    async def get_session(
        self, session_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[StudySession]:
        result = await self.db.execute(
            select(StudySession).where(
                StudySession.id == session_id, StudySession.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def list_sessions(
        self,
        user_id: uuid.UUID,
        topic_id: Optional[uuid.UUID] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[StudySession], int]:
        filters = [StudySession.user_id == user_id]
        if topic_id:
            filters.append(StudySession.topic_id == topic_id)

        query = (
            select(StudySession)
            .where(*filters)
            .order_by(StudySession.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        count_query = select(func.count()).select_from(StudySession).where(*filters)
        result = await self.db.execute(query)
        count_result = await self.db.execute(count_query)
        return list(result.scalars().all()), count_result.scalar_one()
