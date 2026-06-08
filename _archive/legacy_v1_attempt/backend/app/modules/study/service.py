"""Study service."""

import json
import uuid
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.ollama import OllamaClient, OllamaError
from app.ai.router import select_model
from app.core.pagination import PaginatedResponse, PaginationParams
from app.modules.study.models import TopicStatus
from app.modules.study.repository import StudyRepository
from app.modules.study.schemas import (
    FlashcardCreate,
    FlashcardResponse,
    FlashcardUpdate,
    PlanWithAIRequest,
    PlanWithAIResponse,
    StudySessionCreate,
    StudySessionResponse,
    SubjectCreate,
    SubjectResponse,
    SubjectUpdate,
    TopicCreate,
    TopicResponse,
    TopicUpdate,
)


def _extract_ollama_content(response: dict[str, Any]) -> str:
    message = response.get("message")
    if isinstance(message, dict):
        content = message.get("content")
        if isinstance(content, str):
            return content
    response_text = response.get("response")
    if isinstance(response_text, str):
        return response_text
    return ""


def _parse_study_plan(content: str) -> dict[str, Any]:
    text = content.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [line for line in lines if not line.strip().startswith("```")]
        text = "\n".join(lines).strip()
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    return {"raw_plan": content, "steps": []}


class StudyService:
    def __init__(self, db: AsyncSession, ollama: Optional[OllamaClient] = None) -> None:
        self.repo = StudyRepository(db)
        self.ollama = ollama or OllamaClient()

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
        subject = await self.repo.get_subject(data.subject_id, user_id)
        if not subject:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
        topic = await self.repo.create_topic(user_id, data)
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
    ) -> PaginatedResponse[TopicResponse]:
        items, total = await self.repo.list_topics(
            user_id, subject_id, status_filter, pagination.offset, pagination.page_size
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

    async def plan_with_ai(
        self, topic_id: uuid.UUID, user_id: uuid.UUID, data: PlanWithAIRequest
    ) -> PlanWithAIResponse:
        topic = await self.repo.get_topic(topic_id, user_id)
        if not topic:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")

        subject = await self.repo.get_subject(topic.subject_id, user_id)
        subject_name = subject.name if subject else "Unknown"

        prompt = (
            f"Create a structured study plan for the topic '{topic.title}' "
            f"in subject '{subject_name}'."
        )
        if topic.notes:
            prompt += f"\nNotes: {topic.notes}"
        if data.focus_areas:
            prompt += f"\nFocus areas: {data.focus_areas}"
        if data.available_hours:
            prompt += f"\nAvailable hours per week: {data.available_hours}"
        prompt += (
            "\nReturn ONLY valid JSON with keys: overview, objectives (array), "
            "weekly_schedule (array of {week, topics, hours}), resources (array), "
            "milestones (array)."
        )

        model = select_model("planning")
        system = (
            "You are a study planning assistant. Respond with valid JSON only, no markdown."
        )

        try:
            response = await self.ollama.generate(model, prompt, system=system)
            content = _extract_ollama_content(response)
            study_plan = _parse_study_plan(content)
        except OllamaError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"AI service error: {exc}",
            ) from exc

        updated = await self.repo.update_topic(
            topic, TopicUpdate(study_plan=study_plan, status=TopicStatus.IN_PROGRESS)
        )
        return PlanWithAIResponse(topic_id=updated.id, study_plan=updated.study_plan or study_plan)

    async def create_flashcard(
        self, user_id: uuid.UUID, data: FlashcardCreate
    ) -> FlashcardResponse:
        topic = await self.repo.get_topic(data.topic_id, user_id)
        if not topic:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")
        flashcard = await self.repo.create_flashcard(user_id, data)
        return FlashcardResponse.model_validate(flashcard)

    async def get_flashcard(self, flashcard_id: uuid.UUID, user_id: uuid.UUID) -> FlashcardResponse:
        flashcard = await self.repo.get_flashcard(flashcard_id, user_id)
        if not flashcard:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flashcard not found")
        return FlashcardResponse.model_validate(flashcard)

    async def list_flashcards(
        self,
        user_id: uuid.UUID,
        pagination: PaginationParams,
        topic_id: Optional[uuid.UUID] = None,
    ) -> PaginatedResponse[FlashcardResponse]:
        items, total = await self.repo.list_flashcards(
            user_id, topic_id, pagination.offset, pagination.page_size
        )
        return PaginatedResponse.create(
            [FlashcardResponse.model_validate(f) for f in items],
            total,
            pagination.page,
            pagination.page_size,
        )

    async def update_flashcard(
        self, flashcard_id: uuid.UUID, user_id: uuid.UUID, data: FlashcardUpdate
    ) -> FlashcardResponse:
        flashcard = await self.repo.get_flashcard(flashcard_id, user_id)
        if not flashcard:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flashcard not found")
        updated = await self.repo.update_flashcard(flashcard, data)
        return FlashcardResponse.model_validate(updated)

    async def delete_flashcard(self, flashcard_id: uuid.UUID, user_id: uuid.UUID) -> None:
        flashcard = await self.repo.get_flashcard(flashcard_id, user_id)
        if not flashcard:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flashcard not found")
        await self.repo.delete_flashcard(flashcard)

    async def log_session(
        self, user_id: uuid.UUID, data: StudySessionCreate
    ) -> StudySessionResponse:
        if data.topic_id:
            topic = await self.repo.get_topic(data.topic_id, user_id)
            if not topic:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")
        session = await self.repo.create_session(user_id, data)
        return StudySessionResponse.model_validate(session)

    async def list_sessions(
        self,
        user_id: uuid.UUID,
        pagination: PaginationParams,
        topic_id: Optional[uuid.UUID] = None,
    ) -> PaginatedResponse[StudySessionResponse]:
        items, total = await self.repo.list_sessions(
            user_id, topic_id, pagination.offset, pagination.page_size
        )
        return PaginatedResponse.create(
            [StudySessionResponse.model_validate(s) for s in items],
            total,
            pagination.page,
            pagination.page_size,
        )
