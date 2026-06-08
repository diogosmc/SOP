"""Study service."""

import uuid
from typing import Any, Awaitable, Callable, Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.ollama import OllamaError, ollama_chat
from app.core.pagination import PaginatedResponse, PaginationParams
from app.modules.study.models import ReviewRating, TopicStatus
from app.modules.study.repository import StudyRepository
from app.modules.study.schemas import (
    AIPlanResponse,
    FlashcardCreate,
    FlashcardResponse,
    SessionCreate,
    SessionResponse,
    StudySummary,
    SubjectCreate,
    SubjectResponse,
    SubjectUpdate,
    TopicCreate,
    TopicResponse,
    TopicUpdate,
)

OllamaChatFunc = Callable[..., Awaitable[dict[str, Any]]]


class StudyService:
    def __init__(
        self,
        db: AsyncSession,
        ollama_chat_func: Optional[OllamaChatFunc] = None,
    ) -> None:
        self.repo = StudyRepository(db)
        self._ollama_chat = ollama_chat_func or ollama_chat

    async def create_subject(self, user_id: uuid.UUID, data: SubjectCreate) -> SubjectResponse:
        subject = await self.repo.create_subject(user_id, data)
        return SubjectResponse.model_validate(subject)

    async def get_subject(self, subject_id: uuid.UUID, user_id: uuid.UUID) -> SubjectResponse:
        subject = await self.repo.get_subject(subject_id, user_id)
        if not subject:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
        return SubjectResponse.model_validate(subject)

    async def list_subjects(
        self, user_id: uuid.UUID, pagination: PaginationParams
    ) -> PaginatedResponse[SubjectResponse]:
        items, total = await self.repo.list_subjects(user_id, pagination.offset, pagination.page_size)
        return PaginatedResponse.create(
            [SubjectResponse.model_validate(s) for s in items],
            total,
            pagination.page,
            pagination.page_size,
        )

    async def update_subject(
        self, subject_id: uuid.UUID, user_id: uuid.UUID, data: SubjectUpdate
    ) -> SubjectResponse:
        subject = await self.repo.get_subject(subject_id, user_id)
        if not subject:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
        updated = await self.repo.update_subject(subject, data)
        return SubjectResponse.model_validate(updated)

    async def delete_subject(self, subject_id: uuid.UUID, user_id: uuid.UUID) -> None:
        subject = await self.repo.get_subject(subject_id, user_id)
        if not subject:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
        await self.repo.delete_subject(subject)

    async def create_topic(self, user_id: uuid.UUID, data: TopicCreate) -> TopicResponse:
        topic = await self.repo.create_topic(user_id, data)
        if not topic:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
        return TopicResponse.model_validate(topic)

    async def get_topic(self, topic_id: uuid.UUID, user_id: uuid.UUID) -> TopicResponse:
        topic = await self.repo.get_topic(topic_id, user_id)
        if not topic:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")
        return TopicResponse.model_validate(topic)

    async def list_topics(
        self,
        user_id: uuid.UUID,
        pagination: PaginationParams,
        subject_id: Optional[uuid.UUID] = None,
        status_filter: Optional[TopicStatus] = None,
        difficulty: Optional[int] = None,
        search: Optional[str] = None,
    ) -> PaginatedResponse[TopicResponse]:
        items, total = await self.repo.list_topics(
            user_id, subject_id, status_filter, difficulty, search, pagination.offset, pagination.page_size
        )
        return PaginatedResponse.create(
            [TopicResponse.model_validate(t) for t in items],
            total,
            pagination.page,
            pagination.page_size,
        )

    async def update_topic(
        self, topic_id: uuid.UUID, user_id: uuid.UUID, data: TopicUpdate
    ) -> TopicResponse:
        topic = await self.repo.get_topic(topic_id, user_id)
        if not topic:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")
        updated = await self.repo.update_topic(topic, data)
        return TopicResponse.model_validate(updated)

    async def delete_topic(self, topic_id: uuid.UUID, user_id: uuid.UUID) -> None:
        topic = await self.repo.get_topic(topic_id, user_id)
        if not topic:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")
        await self.repo.delete_topic(topic)

    async def create_flashcard(self, user_id: uuid.UUID, data: FlashcardCreate) -> FlashcardResponse:
        card = await self.repo.create_flashcard(user_id, data)
        if not card:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")
        return FlashcardResponse.model_validate(card)

    async def list_flashcards(
        self,
        user_id: uuid.UUID,
        pagination: PaginationParams,
        topic_id: Optional[uuid.UUID] = None,
        due_only: bool = False,
    ) -> PaginatedResponse[FlashcardResponse]:
        items, total = await self.repo.list_flashcards(
            user_id, topic_id, due_only, pagination.offset, pagination.page_size
        )
        return PaginatedResponse.create(
            [FlashcardResponse.model_validate(c) for c in items],
            total,
            pagination.page,
            pagination.page_size,
        )

    async def review_flashcard(
        self, card_id: uuid.UUID, user_id: uuid.UUID, rating: ReviewRating
    ) -> FlashcardResponse:
        card = await self.repo.get_flashcard(card_id, user_id)
        if not card:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flashcard not found")
        updated = await self.repo.review_flashcard(card, rating)
        return FlashcardResponse.model_validate(updated)

    async def delete_flashcard(self, card_id: uuid.UUID, user_id: uuid.UUID) -> None:
        card = await self.repo.get_flashcard(card_id, user_id)
        if not card:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flashcard not found")
        await self.repo.delete_flashcard(card)

    async def create_session(self, user_id: uuid.UUID, data: SessionCreate) -> SessionResponse:
        session = await self.repo.create_session(user_id, data)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject or topic not found")
        return SessionResponse.model_validate(session)

    async def list_sessions(
        self, user_id: uuid.UUID, pagination: PaginationParams
    ) -> PaginatedResponse[SessionResponse]:
        items, total = await self.repo.list_sessions(user_id, pagination.offset, pagination.page_size)
        return PaginatedResponse.create(
            [SessionResponse.model_validate(s) for s in items],
            total,
            pagination.page,
            pagination.page_size,
        )

    async def summary(self, user_id: uuid.UUID) -> StudySummary:
        data = await self.repo.summary(user_id)
        return StudySummary(**data)

    async def generate_ai_plan(self, topic_id: uuid.UUID, user_id: uuid.UUID) -> AIPlanResponse:
        topic = await self.repo.get_topic(topic_id, user_id)
        if not topic:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")

        content = topic.content or "(sem conteúdo detalhado)"
        messages = [
            {
                "role": "system",
                "content": (
                    "Você é um coach de estudos para vestibulares/ENEM. "
                    "Crie planos objetivos em português com seções: objetivos, cronograma sugerido, "
                    "técnicas de revisão e checklist. Use markdown simples."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Título do tópico: {topic.title}\n"
                    f"Dificuldade (1-5): {topic.difficulty}\n"
                    f"Conteúdo/notas:\n{content}\n\n"
                    "Gere um plano de estudo prático para dominar este tópico."
                ),
            },
        ]

        try:
            result = await self._ollama_chat(messages)
            plan_text = result.get("message", {}).get("content", "") or str(result)
        except OllamaError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"IA indisponível: {exc}",
            ) from exc

        return AIPlanResponse(topic_id=topic_id, plan=plan_text)
