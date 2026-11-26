"""Application service for content delivery and lecture transcript operations."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.content import (
    ItemContentResponse,
    TextContentResponse,
    TranscriptResponse,
    TranscriptSearchResult,
    VideoContentResponse,
)
from app.constants import messages
from app.constants.enums import ContentComponentType
from app.core.exceptions import NotFoundError, TranscriptNotFoundError
from app.core.logging import get_logger
from app.db.repositories.content_repository import (
    get_text_content_by_item,
    get_transcript_by_language,
    get_video_content_by_item,
    search_transcripts_fulltext,
)

logger = get_logger(__name__)


async def get_item_content(
    session: AsyncSession,
    *,
    item_id: uuid.UUID,
) -> ItemContentResponse:
    """Retrieve polymorphic learning content for a section item.

    Args:
        session: Active database session.
        item_id: Section item UUID.

    Returns:
        ItemContentResponse containing video or text details.

    Raises:
        NotFoundError: If section item does not exist or has no content.
    """
    video = await get_video_content_by_item(session, section_item_id=item_id)
    text = await get_text_content_by_item(session, section_item_id=item_id)

    if not video and not text:
        logger.warning("item_content_not_found", item_id=str(item_id))
        raise NotFoundError(messages.CONTENT_NOT_FOUND)

    if video:
        return ItemContentResponse(
            item_id=item_id,
            title="Video Lecture",
            content_type=ContentComponentType.VIDEO,
            video=VideoContentResponse(
                id=video.id,
                section_item_id=video.section_item_id,
                video_url=video.video_url,
                youtube_video_id=video.youtube_video_id,
                duration_seconds=video.duration_seconds,
                thumbnail_url=video.thumbnail_url,
            ),
            text=None,
        )

    assert text is not None
    return ItemContentResponse(
        item_id=item_id,
        title="Reading Material",
        content_type=ContentComponentType.TEXT,
        video=None,
        text=TextContentResponse(
            id=text.id,
            section_item_id=text.section_item_id,
            body_markdown=text.body_markdown,
            estimated_read_time_seconds=text.estimated_read_time_seconds,
        ),
    )


async def get_item_transcript(
    session: AsyncSession,
    *,
    item_id: uuid.UUID,
    language_code: str = "en",
) -> TranscriptResponse:
    """Retrieve full lecture transcript for a video section item.

    Args:
        session: Active database session.
        item_id: Section item UUID.
        language_code: Target language code.

    Returns:
        TranscriptResponse with full text and timed cues.

    Raises:
        TranscriptNotFoundError: If item has no video or transcript.
    """
    video = await get_video_content_by_item(session, section_item_id=item_id)
    if not video:
        logger.warning("transcript_video_not_found", item_id=str(item_id))
        raise TranscriptNotFoundError(messages.TRANSCRIPT_NOT_FOUND)

    transcript = await get_transcript_by_language(
        session, video_content_id=video.id, language_code=language_code
    )
    if not transcript:
        logger.warning(
            "transcript_language_not_found",
            item_id=str(item_id),
            video_id=str(video.id),
            language=language_code,
        )
        raise TranscriptNotFoundError(messages.TRANSCRIPT_NOT_FOUND)

    return TranscriptResponse(
        id=transcript.id,
        video_content_id=transcript.video_content_id,
        language_code=transcript.language_code,
        full_text=transcript.full_text,
        timed_cues=transcript.timed_cues or [],
        vtt_content=transcript.vtt_content,
    )


async def search_transcripts(
    session: AsyncSession,
    *,
    query: str,
    course_id: uuid.UUID | None = None,
    limit: int = 10,
) -> list[TranscriptSearchResult]:
    """Execute PostgreSQL full-text search across transcripts.

    Args:
        session: Active database session.
        query: User search query terms.
        course_id: Optional course filter.
        limit: Maximum results to return.

    Returns:
        List of TranscriptSearchResult matches.
    """
    matches = await search_transcripts_fulltext(
        session, query_text=query, course_id=course_id, limit=limit
    )
    logger.info(
        "transcript_search_executed",
        query=query,
        course_id=str(course_id) if course_id else None,
        results_count=len(matches),
    )

    results: list[TranscriptSearchResult] = []
    for transcript, rank in matches:
        snippet = (
            transcript.full_text[:200] + "..."
            if len(transcript.full_text) > 200
            else transcript.full_text
        )
        results.append(
            TranscriptSearchResult(
                transcript_id=transcript.id,
                video_content_id=transcript.video_content_id,
                language_code=transcript.language_code,
                snippet=snippet,
                rank=round(float(rank), 4),
            )
        )
    return results
