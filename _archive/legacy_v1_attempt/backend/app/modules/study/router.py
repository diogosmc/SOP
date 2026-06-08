"""Study API routes."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_id, get_db
from app.core.pagination import PaginationParams
from app.core.schemas import APIResponse
from app.modules.study.models import TopicStatus
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
from app.modules.study.service import StudyService

router = APIRouter(prefix="/study", tags=["study"])


@router.post("/subjects", response_model=APIResponse[SubjectResponse])
async def create_subject(
    data: SubjectCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[SubjectResponse]:
    service = StudyService(db)
    return APIResponse(data=await service.create_subject(user_id, data))


@router.get("/subjects", response_model=APIResponse)
async def list_subjects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    service = StudyService(db)
    pagination = PaginationParams(page=page, page_size=page_size)
    return APIResponse(data=await service.list_subjects(user_id, pagination))


@router.get("/subjects/{subject_id}", response_model=APIResponse[SubjectResponse])
async def get_subject(
    subject_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[SubjectResponse]:
    service = StudyService(db)
    return APIResponse(data=await service.get_subject(subject_id, user_id))


@router.patch("/subjects/{subject_id}", response_model=APIResponse[SubjectResponse])
async def update_subject(
    subject_id: uuid.UUID,
    data: SubjectUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[SubjectResponse]:
    service = StudyService(db)
    return APIResponse(data=await service.update_subject(subject_id, user_id, data))


@router.delete("/subjects/{subject_id}", response_model=APIResponse[None])
async def delete_subject(
    subject_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[None]:
    service = StudyService(db)
    await service.delete_subject(subject_id, user_id)
    return APIResponse(data=None)


@router.post("/topics", response_model=APIResponse[TopicResponse])
async def create_topic(
    data: TopicCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[TopicResponse]:
    service = StudyService(db)
    return APIResponse(data=await service.create_topic(user_id, data))


@router.get("/topics", response_model=APIResponse)
async def list_topics(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    subject_id: Optional[uuid.UUID] = None,
    status: Optional[TopicStatus] = None,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    service = StudyService(db)
    pagination = PaginationParams(page=page, page_size=page_size)
    return APIResponse(data=await service.list_topics(user_id, pagination, subject_id, status))


@router.get("/topics/{topic_id}", response_model=APIResponse[TopicResponse])
async def get_topic(
    topic_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[TopicResponse]:
    service = StudyService(db)
    return APIResponse(data=await service.get_topic(topic_id, user_id))


@router.patch("/topics/{topic_id}", response_model=APIResponse[TopicResponse])
async def update_topic(
    topic_id: uuid.UUID,
    data: TopicUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[TopicResponse]:
    service = StudyService(db)
    return APIResponse(data=await service.update_topic(topic_id, user_id, data))


@router.delete("/topics/{topic_id}", response_model=APIResponse[None])
async def delete_topic(
    topic_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[None]:
    service = StudyService(db)
    await service.delete_topic(topic_id, user_id)
    return APIResponse(data=None)


@router.post("/topics/{topic_id}/plan-with-ai", response_model=APIResponse[PlanWithAIResponse])
async def plan_topic_with_ai(
    topic_id: uuid.UUID,
    data: PlanWithAIRequest = PlanWithAIRequest(),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PlanWithAIResponse]:
    service = StudyService(db)
    return APIResponse(data=await service.plan_with_ai(topic_id, user_id, data))


@router.post("/flashcards", response_model=APIResponse[FlashcardResponse])
async def create_flashcard(
    data: FlashcardCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[FlashcardResponse]:
    service = StudyService(db)
    return APIResponse(data=await service.create_flashcard(user_id, data))


@router.get("/flashcards", response_model=APIResponse)
async def list_flashcards(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    topic_id: Optional[uuid.UUID] = None,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    service = StudyService(db)
    pagination = PaginationParams(page=page, page_size=page_size)
    return APIResponse(data=await service.list_flashcards(user_id, pagination, topic_id))


@router.get("/flashcards/{flashcard_id}", response_model=APIResponse[FlashcardResponse])
async def get_flashcard(
    flashcard_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[FlashcardResponse]:
    service = StudyService(db)
    return APIResponse(data=await service.get_flashcard(flashcard_id, user_id))


@router.patch("/flashcards/{flashcard_id}", response_model=APIResponse[FlashcardResponse])
async def update_flashcard(
    flashcard_id: uuid.UUID,
    data: FlashcardUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[FlashcardResponse]:
    service = StudyService(db)
    return APIResponse(data=await service.update_flashcard(flashcard_id, user_id, data))


@router.delete("/flashcards/{flashcard_id}", response_model=APIResponse[None])
async def delete_flashcard(
    flashcard_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[None]:
    service = StudyService(db)
    await service.delete_flashcard(flashcard_id, user_id)
    return APIResponse(data=None)


@router.post("/sessions", response_model=APIResponse[StudySessionResponse])
async def log_study_session(
    data: StudySessionCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[StudySessionResponse]:
    service = StudyService(db)
    return APIResponse(data=await service.log_session(user_id, data))


@router.get("/sessions", response_model=APIResponse)
async def list_study_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    topic_id: Optional[uuid.UUID] = None,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    service = StudyService(db)
    pagination = PaginationParams(page=page, page_size=page_size)
    return APIResponse(data=await service.list_sessions(user_id, pagination, topic_id))
