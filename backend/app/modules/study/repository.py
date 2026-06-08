"""Study repository."""

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import utc_now
from app.modules.study.models import (
    Flashcard,
    ReviewRating,
    StudySession,
    StudySubject,
    StudyTopic,
    TopicStatus,
)
from app.modules.study.schemas import (
    FlashcardCreate,
    SessionCreate,
    SM2State,
    SubjectCreate,
    SubjectUpdate,
    TopicCreate,
    TopicUpdate,
)
from app.modules.study.sm2 import apply_sm2_review


class StudyRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_subject(self, user_id: uuid.UUID, data: SubjectCreate) -> StudySubject:
        subject = StudySubject(user_id=user_id, **data.model_dump())
        self.db.add(subject)
        await self.db.flush()
        await self.db.refresh(subject)
        return subject

    async def get_subject(self, subject_id: uuid.UUID, user_id: uuid.UUID) -> Optional[StudySubject]:
        result = await self.db.execute(
            select(StudySubject).where(StudySubject.id == subject_id, StudySubject.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_subjects(
        self, user_id: uuid.UUID, offset: int = 0, limit: int = 50
    ) -> Tuple[List[StudySubject], int]:
        query = select(StudySubject).where(StudySubject.user_id == user_id).order_by(StudySubject.name)
        count_query = select(func.count()).select_from(StudySubject).where(StudySubject.user_id == user_id)
        result = await self.db.execute(query.offset(offset).limit(limit))
        count = await self.db.execute(count_query)
        return list(result.scalars().all()), count.scalar_one()

    async def update_subject(self, subject: StudySubject, data: SubjectUpdate) -> StudySubject:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(subject, field, value)
        await self.db.flush()
        await self.db.refresh(subject)
        return subject

    async def delete_subject(self, subject: StudySubject) -> None:
        await self.db.delete(subject)
        await self.db.flush()

    async def _subject_owned(self, subject_id: uuid.UUID, user_id: uuid.UUID) -> Optional[StudySubject]:
        return await self.get_subject(subject_id, user_id)

    async def create_topic(self, user_id: uuid.UUID, data: TopicCreate) -> Optional[StudyTopic]:
        subject = await self._subject_owned(data.subject_id, user_id)
        if not subject:
            return None
        topic = StudyTopic(**data.model_dump())
        self.db.add(topic)
        await self.db.flush()
        await self.db.refresh(topic)
        return topic

    async def get_topic(self, topic_id: uuid.UUID, user_id: uuid.UUID) -> Optional[StudyTopic]:
        result = await self.db.execute(
            select(StudyTopic)
            .join(StudySubject, StudyTopic.subject_id == StudySubject.id)
            .where(StudyTopic.id == topic_id, StudySubject.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_topics(
        self,
        user_id: uuid.UUID,
        subject_id: Optional[uuid.UUID] = None,
        status: Optional[TopicStatus] = None,
        difficulty: Optional[int] = None,
        search: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> Tuple[List[StudyTopic], int]:
        query = (
            select(StudyTopic)
            .join(StudySubject, StudyTopic.subject_id == StudySubject.id)
            .where(StudySubject.user_id == user_id)
        )
        count_query = (
            select(func.count())
            .select_from(StudyTopic)
            .join(StudySubject, StudyTopic.subject_id == StudySubject.id)
            .where(StudySubject.user_id == user_id)
        )
        if subject_id:
            query = query.where(StudyTopic.subject_id == subject_id)
            count_query = count_query.where(StudyTopic.subject_id == subject_id)
        if status:
            query = query.where(StudyTopic.status == status)
            count_query = count_query.where(StudyTopic.status == status)
        if difficulty:
            query = query.where(StudyTopic.difficulty == difficulty)
            count_query = count_query.where(StudyTopic.difficulty == difficulty)
        if search:
            pattern = f"%{search}%"
            clause = or_(StudyTopic.title.ilike(pattern), StudyTopic.content.ilike(pattern))
            query = query.where(clause)
            count_query = count_query.where(clause)
        query = query.order_by(StudyTopic.updated_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        count = await self.db.execute(count_query)
        return list(result.scalars().all()), count.scalar_one()

    async def update_topic(self, topic: StudyTopic, data: TopicUpdate) -> StudyTopic:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(topic, field, value)
        await self.db.flush()
        await self.db.refresh(topic)
        return topic

    async def delete_topic(self, topic: StudyTopic) -> None:
        await self.db.delete(topic)
        await self.db.flush()

    async def create_flashcard(self, user_id: uuid.UUID, data: FlashcardCreate) -> Optional[Flashcard]:
        topic = await self.get_topic(data.topic_id, user_id)
        if not topic:
            return None
        card = Flashcard(
            topic_id=data.topic_id,
            front=data.front,
            back=data.back,
            next_review=utc_now(),
            interval_days=0,
            ease_factor=Decimal("2.50"),
            repetitions=0,
        )
        self.db.add(card)
        await self.db.flush()
        await self.db.refresh(card)
        return card

    async def get_flashcard(self, card_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Flashcard]:
        result = await self.db.execute(
            select(Flashcard)
            .join(StudyTopic, Flashcard.topic_id == StudyTopic.id)
            .join(StudySubject, StudyTopic.subject_id == StudySubject.id)
            .where(Flashcard.id == card_id, StudySubject.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_flashcards(
        self,
        user_id: uuid.UUID,
        topic_id: Optional[uuid.UUID] = None,
        due_only: bool = False,
        offset: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Flashcard], int]:
        query = (
            select(Flashcard)
            .join(StudyTopic, Flashcard.topic_id == StudyTopic.id)
            .join(StudySubject, StudyTopic.subject_id == StudySubject.id)
            .where(StudySubject.user_id == user_id)
        )
        count_query = (
            select(func.count())
            .select_from(Flashcard)
            .join(StudyTopic, Flashcard.topic_id == StudyTopic.id)
            .join(StudySubject, StudyTopic.subject_id == StudySubject.id)
            .where(StudySubject.user_id == user_id)
        )
        if topic_id:
            query = query.where(Flashcard.topic_id == topic_id)
            count_query = count_query.where(Flashcard.topic_id == topic_id)
        if due_only:
            now = utc_now()
            due_clause = or_(Flashcard.next_review.is_(None), Flashcard.next_review <= now)
            query = query.where(due_clause)
            count_query = count_query.where(due_clause)
        query = query.order_by(Flashcard.next_review.asc().nullsfirst()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        count = await self.db.execute(count_query)
        return list(result.scalars().all()), count.scalar_one()

    async def review_flashcard(
        self, card: Flashcard, rating: ReviewRating
    ) -> Flashcard:
        state = SM2State(
            interval_days=card.interval_days,
            ease_factor=card.ease_factor,
            repetitions=card.repetitions,
        )
        new_state, next_review = apply_sm2_review(state, rating)
        card.interval_days = new_state.interval_days
        card.ease_factor = new_state.ease_factor
        card.repetitions = new_state.repetitions
        card.next_review = next_review
        await self.db.flush()
        await self.db.refresh(card)
        return card

    async def delete_flashcard(self, card: Flashcard) -> None:
        await self.db.delete(card)
        await self.db.flush()

    async def create_session(self, user_id: uuid.UUID, data: SessionCreate) -> Optional[StudySession]:
        if data.subject_id:
            if not await self._subject_owned(data.subject_id, user_id):
                return None
        if data.topic_id:
            if not await self.get_topic(data.topic_id, user_id):
                return None
        session = StudySession(user_id=user_id, **data.model_dump())
        self.db.add(session)
        await self.db.flush()
        await self.db.refresh(session)
        return session

    async def list_sessions(
        self, user_id: uuid.UUID, offset: int = 0, limit: int = 50
    ) -> Tuple[List[StudySession], int]:
        query = (
            select(StudySession)
            .where(StudySession.user_id == user_id)
            .order_by(StudySession.created_at.desc())
        )
        count_query = select(func.count()).select_from(StudySession).where(StudySession.user_id == user_id)
        result = await self.db.execute(query.offset(offset).limit(limit))
        count = await self.db.execute(count_query)
        return list(result.scalars().all()), count.scalar_one()

    async def summary(self, user_id: uuid.UUID) -> dict:
        now = utc_now()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start_of_week = start_of_day - timedelta(days=start_of_day.weekday())

        subjects = await self.db.execute(
            select(func.count()).select_from(StudySubject).where(StudySubject.user_id == user_id)
        )
        topics = await self.db.execute(
            select(func.count())
            .select_from(StudyTopic)
            .join(StudySubject, StudyTopic.subject_id == StudySubject.id)
            .where(StudySubject.user_id == user_id)
        )
        in_progress = await self.db.execute(
            select(func.count())
            .select_from(StudyTopic)
            .join(StudySubject, StudyTopic.subject_id == StudySubject.id)
            .where(StudySubject.user_id == user_id, StudyTopic.status == TopicStatus.IN_PROGRESS)
        )
        mastered = await self.db.execute(
            select(func.count())
            .select_from(StudyTopic)
            .join(StudySubject, StudyTopic.subject_id == StudySubject.id)
            .where(StudySubject.user_id == user_id, StudyTopic.status == TopicStatus.MASTERED)
        )
        due_cards = await self.db.execute(
            select(func.count())
            .select_from(Flashcard)
            .join(StudyTopic, Flashcard.topic_id == StudyTopic.id)
            .join(StudySubject, StudyTopic.subject_id == StudySubject.id)
            .where(
                StudySubject.user_id == user_id,
                or_(Flashcard.next_review.is_(None), Flashcard.next_review <= now),
            )
        )
        minutes_today = await self.db.execute(
            select(func.coalesce(func.sum(StudySession.duration_minutes), 0)).where(
                StudySession.user_id == user_id,
                StudySession.created_at >= start_of_day,
            )
        )
        minutes_week = await self.db.execute(
            select(func.coalesce(func.sum(StudySession.duration_minutes), 0)).where(
                StudySession.user_id == user_id,
                StudySession.created_at >= start_of_week,
            )
        )

        return {
            "total_subjects": subjects.scalar_one(),
            "total_topics": topics.scalar_one(),
            "topics_in_progress": in_progress.scalar_one(),
            "topics_mastered": mastered.scalar_one(),
            "flashcards_due": due_cards.scalar_one(),
            "minutes_studied_today": int(minutes_today.scalar_one()),
            "minutes_studied_week": int(minutes_week.scalar_one()),
        }
