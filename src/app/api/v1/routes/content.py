"""HTTP endpoints for learning content delivery and transcript retrieval."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.common import ApiResponse
from app.api.v1.schemas.content import (
    ItemContentResponse,
    TranscriptResponse,
    TranscriptSearchResult,
)
from app.api.v1.services import content_service
from app.constants import messages
from app.db.session import get_db_session

router = APIRouter(tags=["Content & Transcripts"])

_CONTENT_NOT_FOUND_RESPONSES: dict[int | str, dict[str, str]] = {
    404: {"description": messages.RESOURCE_NOT_FOUND},
}


@router.get(
    "/items/{item_id}/content",
    summary="Get section item content",
    description="Returns polymorphic content for a section item (video streaming metadata or markdown text).",
    status_code=status.HTTP_200_OK,
    response_model=ApiResponse[ItemContentResponse],
    responses=_CONTENT_NOT_FOUND_RESPONSES,
)
async def get_item_content_endpoint(
    item_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[ItemContentResponse]:
    """Retrieve learning content payload for a section item."""
    content = await content_service.get_item_content(session, item_id=item_id)
    return ApiResponse(
        data=content,
        message="Item content retrieved successfully.",
    )


@router.get(
    "/items/{item_id}/transcript",
    summary="Get lecture transcript",
    description="Retrieves full spoken transcript and timed cues for a video lecture.",
    status_code=status.HTTP_200_OK,
    response_model=ApiResponse[TranscriptResponse],
    responses=_CONTENT_NOT_FOUND_RESPONSES,
)
async def get_item_transcript_endpoint(
    item_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    language: Annotated[str, Query(description="Target language code.")] = "en",
) -> ApiResponse[TranscriptResponse]:
    """Retrieve transcript with timed subtitle cues."""
    transcript = await content_service.get_item_transcript(
        session, item_id=item_id, language_code=language
    )
    return ApiResponse(
        data=transcript,
        message="Transcript retrieved successfully.",
    )


@router.get(
    "/transcripts/search",
    summary="Search transcripts full-text",
    description="Searches all lecture transcripts using PostgreSQL GIN index and returns ranked matches.",
    status_code=status.HTTP_200_OK,
    response_model=ApiResponse[list[TranscriptSearchResult]],
)
async def search_transcripts_endpoint(
    query: Annotated[
        str, Query(min_length=1, description="Keywords to search in transcripts.")
    ],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    course_id: Annotated[
        uuid.UUID | None, Query(description="Optional course filter.")
    ] = None,
    limit: Annotated[int, Query(ge=1, le=50, description="Max search results.")] = 10,
) -> ApiResponse[list[TranscriptSearchResult]]:
    """Execute full-text keyword search across lecture transcripts."""
    results = await content_service.search_transcripts(
        session, query=query, course_id=course_id, limit=limit
    )
    return ApiResponse(
        data=results,
        message="Transcript search executed successfully.",
    )
