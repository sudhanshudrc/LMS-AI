"""Application service for learner progress tracking and completion calculations."""

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.progress import (
    CourseProgressResponse,
    ItemProgressResponse,
    ModuleProgressResponse,
    PlaybackUpdateRequest,
)
from app.constants import messages
from app.constants.enums import CompletionStatus
from app.core.exceptions import CourseNotFoundError, NotFoundError
from app.core.logging import get_logger
from app.core.security import Caller

logger = get_logger(__name__)
from app.db.models.curriculum import Module, Section, SectionItem
from app.db.models.progress import UserItemCompletion
from app.db.repositories.course_repository import find_course_by_id
from app.db.repositories.progress_repository import (
    get_user_item_completion,
)


async def update_playback(
    session: AsyncSession,
    *,
    caller: Caller,
    item_id: uuid.UUID,
    payload: PlaybackUpdateRequest,
) -> ItemProgressResponse:
    """Save video playback resume position and optionally mark item completed.

    Args:
        session: Active database session.
        caller: Authenticated learner.
        item_id: Section item UUID.
        payload: Playback position and completion intent.

    Returns:
        Updated ItemProgressResponse.

    Raises:
        NotFoundError: If section item does not exist.
    """
    item = await session.get(SectionItem, item_id)
    if not item:
        raise NotFoundError(messages.SECTION_ITEM_NOT_FOUND)

    status = (
        CompletionStatus.COMPLETED
        if payload.mark_completed
        else CompletionStatus.IN_PROGRESS
    )
    completed_at = datetime.now(UTC) if payload.mark_completed else None

    # Upsert with completed_at handling
    stmt = (
        insert(UserItemCompletion)
        .values(
            user_id=caller.user_id,
            section_item_id=item_id,
            last_playback_position_seconds=payload.position_seconds,
            status=status,
            completed_at=completed_at,
        )
        .on_conflict_do_update(
            constraint="uq_user_section_item",
            set_={
                "last_playback_position_seconds": payload.position_seconds,
                "status": status,
                "completed_at": func.coalesce(
                    UserItemCompletion.completed_at, completed_at
                ),
                "last_activity_at": func.now(),
            },
        )
    )
    await session.execute(stmt)
    await session.commit()

    record = await get_user_item_completion(
        session, user_id=caller.user_id, section_item_id=item_id
    )
    assert record is not None

    logger.info(
        "item_marked_completed",
        user_id=str(caller.user_id),
        item_id=str(item_id),
        status=CompletionStatus.COMPLETED.value,
    )

    return ItemProgressResponse(
        section_item_id=record.section_item_id,
        status=record.status,
        last_playback_position_seconds=record.last_playback_position_seconds,
        is_completed=record.is_completed,
        completed_at=record.completed_at,
        last_activity_at=record.last_activity_at,
    )


async def mark_item_completed(
    session: AsyncSession,
    *,
    caller: Caller,
    item_id: uuid.UUID,
) -> ItemProgressResponse:
    """Idempotently mark a section item as completed.

    Args:
        session: Active database session.
        caller: Authenticated learner.
        item_id: Section item UUID.

    Returns:
        ItemProgressResponse confirming completion.

    Raises:
        NotFoundError: If section item does not exist.
    """
    item = await session.get(SectionItem, item_id)
    if not item:
        raise NotFoundError(messages.SECTION_ITEM_NOT_FOUND)

    now = datetime.now(UTC)
    stmt = (
        insert(UserItemCompletion)
        .values(
            user_id=caller.user_id,
            section_item_id=item_id,
            status=CompletionStatus.COMPLETED,
            completed_at=now,
        )
        .on_conflict_do_update(
            constraint="uq_user_section_item",
            set_={
                "status": CompletionStatus.COMPLETED,
                "completed_at": func.coalesce(UserItemCompletion.completed_at, now),
                "last_activity_at": func.now(),
            },
        )
    )
    await session.execute(stmt)
    await session.commit()

    record = await get_user_item_completion(
        session, user_id=caller.user_id, section_item_id=item_id
    )
    assert record is not None

    logger.info(
        "item_marked_completed",
        user_id=str(caller.user_id),
        item_id=str(item_id),
        status=CompletionStatus.COMPLETED.value,
    )

    return ItemProgressResponse(
        section_item_id=record.section_item_id,
        status=record.status,
        last_playback_position_seconds=record.last_playback_position_seconds,
        is_completed=record.is_completed,
        completed_at=record.completed_at,
        last_activity_at=record.last_activity_at,
    )


async def get_course_progress(
    session: AsyncSession,
    *,
    caller: Caller,
    course_id: uuid.UUID,
) -> CourseProgressResponse:
    """Compute aggregated course completion metrics for the learner.

    Args:
        session: Active database session.
        caller: Authenticated learner.
        course_id: Course UUID.

    Returns:
        CourseProgressResponse with completion metrics.

    Raises:
        CourseNotFoundError: If course does not exist.
    """
    course = await find_course_by_id(session, course_id=course_id)
    if not course:
        raise CourseNotFoundError()

    # Query total items in course
    items_stmt = (
        select(SectionItem.id, Module.id.label("module_id"))
        .join(Section, SectionItem.section_id == Section.id)
        .join(Module, Section.module_id == Module.id)
        .where(Module.course_id == course_id)
    )
    items_result = await session.execute(items_stmt)
    course_items = items_result.all()
    total_items = len(course_items)

    if total_items == 0:
        return CourseProgressResponse(
            course_id=course_id,
            total_items=0,
            completed_items=0,
            overall_percentage=Decimal("0.00"),
            modules=[],
        )

    item_ids = [item[0] for item in course_items]

    # Query completed items by user
    completed_stmt = select(UserItemCompletion.section_item_id).where(
        UserItemCompletion.user_id == caller.user_id,
        UserItemCompletion.section_item_id.in_(item_ids),
        UserItemCompletion.status == CompletionStatus.COMPLETED,
    )
    completed_result = await session.execute(completed_stmt)
    completed_item_ids = {row[0] for row in completed_result.all()}
    completed_count = len(completed_item_ids)

    overall_pct = (Decimal(completed_count) / Decimal(total_items) * 100).quantize(
        Decimal("0.01")
    )

    # Group items by module to calculate per-module progress
    module_items_map: dict[uuid.UUID, list[uuid.UUID]] = {}
    for item_id, mod_id in course_items:
        module_items_map.setdefault(mod_id, []).append(item_id)

    module_responses: list[ModuleProgressResponse] = []
    for mod_id, m_item_ids in module_items_map.items():
        m_total = len(m_item_ids)
        m_completed = sum(
            1 for m_item_id in m_item_ids if m_item_id in completed_item_ids
        )
        m_pct = (
            (Decimal(m_completed) / Decimal(m_total) * 100).quantize(Decimal("0.01"))
            if m_total > 0
            else Decimal("0.00")
        )

        m_status = CompletionStatus.NOT_STARTED
        if m_completed == m_total and m_total > 0:
            m_status = CompletionStatus.COMPLETED
        elif m_completed > 0:
            m_status = CompletionStatus.IN_PROGRESS

        module_responses.append(
            ModuleProgressResponse(
                module_id=mod_id,
                status=m_status,
                progress_percentage=m_pct,
                completed_at=None,
            )
        )

    return CourseProgressResponse(
        course_id=course_id,
        total_items=total_items,
        completed_items=completed_count,
        overall_percentage=overall_pct,
        modules=module_responses,
    )
