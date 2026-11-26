"""HTTP endpoints for learner progress and video playback tracking."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.common import ApiResponse
from app.api.v1.schemas.progress import (
    CourseProgressResponse,
    ItemProgressResponse,
    PlaybackUpdateRequest,
)
from app.api.v1.services import progress_service
from app.constants import messages
from app.core.security import Caller, get_current_caller
from app.db.session import get_db_session

router = APIRouter(prefix="/progress", tags=["Learner Progress"])

_NOT_FOUND_RESPONSES: dict[int | str, dict[str, str]] = {
    401: {"description": messages.UNAUTHORIZED_ACCESS},
    404: {"description": messages.RESOURCE_NOT_FOUND},
}


@router.get(
    "/courses/{course_id}",
    summary="Get course progress",
    description="Returns aggregated completion metrics and per-module breakdown for the authenticated learner.",
    status_code=status.HTTP_200_OK,
    response_model=ApiResponse[CourseProgressResponse],
    responses=_NOT_FOUND_RESPONSES,
)
async def get_course_progress_endpoint(
    course_id: uuid.UUID,
    caller: Annotated[Caller, Depends(get_current_caller)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[CourseProgressResponse]:
    """Retrieve learner progress metrics for a given course."""
    progress = await progress_service.get_course_progress(
        session, caller=caller, course_id=course_id
    )
    return ApiResponse(
        data=progress,
        message="Course progress retrieved successfully.",
    )


@router.post(
    "/items/{item_id}/playback",
    summary="Update playback position",
    description="Updates video playback position seconds and optionally marks the item completed.",
    status_code=status.HTTP_200_OK,
    response_model=ApiResponse[ItemProgressResponse],
    responses=_NOT_FOUND_RESPONSES,
)
async def update_playback_endpoint(
    item_id: uuid.UUID,
    payload: PlaybackUpdateRequest,
    caller: Annotated[Caller, Depends(get_current_caller)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[ItemProgressResponse]:
    """Update video playback progress."""
    progress = await progress_service.update_playback(
        session, caller=caller, item_id=item_id, payload=payload
    )
    return ApiResponse(
        data=progress,
        message="Playback position updated successfully.",
    )


@router.post(
    "/items/{item_id}/complete",
    summary="Mark item completed",
    description="Idempotently marks a section item as completed by the learner.",
    status_code=status.HTTP_200_OK,
    response_model=ApiResponse[ItemProgressResponse],
    responses=_NOT_FOUND_RESPONSES,
)
async def mark_item_completed_endpoint(
    item_id: uuid.UUID,
    caller: Annotated[Caller, Depends(get_current_caller)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[ItemProgressResponse]:
    """Mark a section item as completed."""
    progress = await progress_service.mark_item_completed(
        session, caller=caller, item_id=item_id
    )
    return ApiResponse(
        data=progress,
        message="Item marked as completed successfully.",
    )
