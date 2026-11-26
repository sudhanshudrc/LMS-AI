"""Queries for content items: `item_video_contents`, `item_text_contents`, and `video_transcripts`."""

import uuid
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.content import ItemTextContent, ItemVideoContent, VideoTranscript
from app.db.models.curriculum import Module, Section, SectionItem


async def get_video_content_by_item(
    session: AsyncSession,
    *,
    section_item_id: uuid.UUID,
) -> ItemVideoContent | None:
    """Find video content record by its parent section item ID.

    Args:
        session: Active database session.
        section_item_id: Section item UUID.

    Returns:
        ItemVideoContent entity if found, None otherwise.
    """
    stmt = select(ItemVideoContent).where(
        ItemVideoContent.section_item_id == section_item_id,
    )
    return await session.scalar(stmt)


async def get_text_content_by_item(
    session: AsyncSession,
    *,
    section_item_id: uuid.UUID,
) -> ItemTextContent | None:
    """Find text reading content record by its parent section item ID.

    Args:
        session: Active database session.
        section_item_id: Section item UUID.

    Returns:
        ItemTextContent entity if found, None otherwise.
    """
    stmt = select(ItemTextContent).where(
        ItemTextContent.section_item_id == section_item_id,
    )
    return await session.scalar(stmt)


async def get_transcript_by_language(
    session: AsyncSession,
    *,
    video_content_id: uuid.UUID,
    language_code: str = "en",
) -> VideoTranscript | None:
    """Retrieve video transcript for a specific language code.

    Args:
        session: Active database session.
        video_content_id: Video content entity UUID.
        language_code: ISO language code (e.g. 'en').

    Returns:
        VideoTranscript entity if found, None otherwise.
    """
    stmt = select(VideoTranscript).where(
        VideoTranscript.video_content_id == video_content_id,
        VideoTranscript.language_code == language_code,
    )
    return await session.scalar(stmt)


async def search_transcripts_fulltext(
    session: AsyncSession,
    *,
    query_text: str,
    course_id: uuid.UUID | None = None,
    limit: int = 10,
) -> Sequence[tuple[VideoTranscript, float]]:
    """Search video transcripts using PostgreSQL GIN full-text search.

    Args:
        session: Active database session.
        query_text: Plain text search terms.
        course_id: Optional course filter to restrict search scope.
        limit: Max results to return.

    Returns:
        Sequence of (VideoTranscript, rank) tuples sorted by match rank.
    """
    ts_query = func.plainto_tsquery("english", query_text)
    ts_vector = func.to_tsvector("english", VideoTranscript.full_text)
    rank = func.ts_rank(ts_vector, ts_query).label("rank")

    stmt = (
        select(VideoTranscript, rank)
        .join(ItemVideoContent, VideoTranscript.video_content_id == ItemVideoContent.id)
        .join(SectionItem, ItemVideoContent.section_item_id == SectionItem.id)
        .join(Section, SectionItem.section_id == Section.id)
        .join(Module, Section.module_id == Module.id)
        .where(ts_vector.op("@@")(ts_query))
    )
    if course_id is not None:
        stmt = stmt.where(Module.course_id == course_id)

    stmt = stmt.order_by(rank.desc()).limit(limit)
    res = await session.execute(stmt)
    return res.all()
