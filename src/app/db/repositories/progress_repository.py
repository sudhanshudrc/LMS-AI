"""Queries for progress tracking: `user_module_completions` and `user_item_completions`."""

import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import CompletionStatus
from app.db.models.progress import UserItemCompletion, UserModuleCompletion


async def get_user_module_completion(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    module_id: uuid.UUID,
) -> UserModuleCompletion | None:
    """Retrieve completion state of a specific module for a user.

    Args:
        session: Active database session.
        user_id: User UUID.
        module_id: Module UUID.

    Returns:
        UserModuleCompletion entity if found, None otherwise.
    """
    stmt = select(UserModuleCompletion).where(
        UserModuleCompletion.user_id == user_id,
        UserModuleCompletion.module_id == module_id,
    )
    return await session.scalar(stmt)


async def get_user_item_completion(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    section_item_id: uuid.UUID,
) -> UserItemCompletion | None:
    """Retrieve item-level completion and playback resume position.

    Args:
        session: Active database session.
        user_id: User UUID.
        section_item_id: SectionItem UUID.

    Returns:
        UserItemCompletion entity if found, None otherwise.
    """
    stmt = select(UserItemCompletion).where(
        UserItemCompletion.user_id == user_id,
        UserItemCompletion.section_item_id == section_item_id,
    )
    return await session.scalar(stmt)


async def upsert_user_module_completion(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    module_id: uuid.UUID,
    status: CompletionStatus,
    progress_percentage: Decimal,
) -> None:
    """Idempotently insert or update user module completion progress.

    Args:
        session: Active database session.
        user_id: User UUID.
        module_id: Module UUID.
        status: Current completion status.
        progress_percentage: Metric from 0.00 to 100.00.
    """
    stmt = (
        insert(UserModuleCompletion)
        .values(
            user_id=user_id,
            module_id=module_id,
            status=status,
            progress_percentage=progress_percentage,
        )
        .on_conflict_do_update(
            constraint="uq_user_module",
            set_={
                "status": status,
                "progress_percentage": progress_percentage,
            },
        )
    )
    await session.execute(stmt)


async def save_playback_position(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    section_item_id: uuid.UUID,
    playback_position_seconds: int,
    status: CompletionStatus = CompletionStatus.IN_PROGRESS,
) -> None:
    """Idempotently save video playback resume position.

    Args:
        session: Active database session.
        user_id: User UUID.
        section_item_id: SectionItem UUID.
        playback_position_seconds: Current seconds mark.
        status: Optional completion status update.
    """
    stmt = (
        insert(UserItemCompletion)
        .values(
            user_id=user_id,
            section_item_id=section_item_id,
            last_playback_position_seconds=playback_position_seconds,
            status=status,
        )
        .on_conflict_do_update(
            constraint="uq_user_section_item",
            set_={
                "last_playback_position_seconds": playback_position_seconds,
                "status": status,
            },
        )
    )
    await session.execute(stmt)
