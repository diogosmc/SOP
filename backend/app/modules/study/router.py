"""Study API routes."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import TTL_DASHBOARD, build_cache_key, get_or_set_json, invalidate_user_cache
from app.core.config import get_settings
from app.core.deps import get_current_user_id, get_db
from app.core.pagination import PaginationParams
from app.core.schemas import APIResponse
from app.modules.study.models import TopicStatus
from app.modules.study.schemas import (
    AIPlanResponse,
    FlashcardCreate,
    FlashcardResponse,
    FlashcardReviewRequest,
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
from app.modules.study.service import StudyService

router = APIRouter(prefix="/study", tags=["study"])


@router.get("/summary", response_model=APIResponse[StudySummary])
async def study_summary(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[StudySummary]:
    service = StudyService(db)
    cache_key = build_cache_key("study:summary", user_id)

    async def load() -> StudySummary:
        return await service.summary(user_id)

    if get_settings().cache_enabled:
        data = await get_or_set_json(cache_key, TTL_DASHBOARD, load)
    else:
        data = await load()
    return APIResponse(data=StudySummary.model_validate(data))


@router.get("/subjects", response_model=APIResponse)
async def list_subjects(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    service = StudyService(db)
    pagination = PaginationParams(page=page, page_size=page_size)
    return APIResponse(data=await service.list_subjects(user_id, pagination))


@router.post("/subjects", response_model=APIResponse[SubjectResponse])
async def create_subject(
    data: SubjectCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[SubjectResponse]:
    service = StudyService(db)
    return APIResponse(data=await service.create_subject(user_id, data))


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


@router.get("/topics", response_model=APIResponse)
async def list_topics(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    subject_id: Optional[uuid.UUID] = None,
    status: Optional[TopicStatus] = None,
    difficulty: Optional[int] = Query(default=None, ge=1, le=5),
    search: Optional[str] = None,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    service = StudyService(db)
    pagination = PaginationParams(page=page, page_size=page_size)
    return APIResponse(
        data=await service.list_topics(user_id, pagination, subject_id, status, difficulty, search)
    )


@router.post("/topics", response_model=APIResponse[TopicResponse])
async def create_topic(
    data: TopicCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[TopicResponse]:
    service = StudyService(db)
    return APIResponse(data=await service.create_topic(user_id, data))


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


@router.post("/topics/{topic_id}/ai-plan", response_model=APIResponse[AIPlanResponse])
async def topic_ai_plan(
    topic_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[AIPlanResponse]:
    service = StudyService(db)
    return APIResponse(data=await service.generate_ai_plan(topic_id, user_id))


@router.get("/flashcards", response_model=APIResponse)
async def list_flashcards(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    topic_id: Optional[uuid.UUID] = None,
    due_only: bool = False,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    service = StudyService(db)
    pagination = PaginationParams(page=page, page_size=page_size)
    return APIResponse(data=await service.list_flashcards(user_id, pagination, topic_id, due_only))


@router.post("/flashcards", response_model=APIResponse[FlashcardResponse])
async def create_flashcard(
    data: FlashcardCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[FlashcardResponse]:
    service = StudyService(db)
    return APIResponse(data=await service.create_flashcard(user_id, data))


@router.patch("/flashcards/{card_id}/review", response_model=APIResponse[FlashcardResponse])
async def review_flashcard(
    card_id: uuid.UUID,
    data: FlashcardReviewRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[FlashcardResponse]:
    service = StudyService(db)
    return APIResponse(data=await service.review_flashcard(card_id, user_id, data.rating))


@router.delete("/flashcards/{card_id}", response_model=APIResponse[None])
async def delete_flashcard(
    card_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[None]:
    service = StudyService(db)
    await service.delete_flashcard(card_id, user_id)
    return APIResponse(data=None)


@router.post("/sessions", response_model=APIResponse[SessionResponse])
async def create_session(
    data: SessionCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[SessionResponse]:
    service = StudyService(db)
    result = await service.create_session(user_id, data)
    await invalidate_user_cache(user_id, "study:summary")
    return APIResponse(data=result)


@router.get("/sessions", response_model=APIResponse)
async def list_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    service = StudyService(db)
    pagination = PaginationParams(page=page, page_size=page_size)
    return APIResponse(data=await service.list_sessions(user_id, pagination))
