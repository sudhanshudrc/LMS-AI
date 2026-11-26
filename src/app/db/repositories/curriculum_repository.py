"""Queries for the curriculum tables: `modules`, `sections`, and `section_items`."""

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.curriculum import Module, Section, SectionItem


async def get_course_tree(
    session: AsyncSession,
    *,
    course_id: uuid.UUID,
) -> Sequence[Module]:
    """Retrieve full curriculum hierarchy for a course with sections and items eager-loaded.

    Args:
        session: Active database session.
        course_id: Course UUID.

    Returns:
        Ordered sequence of Modules with eager-loaded Sections and Items.
    """
    stmt = (
        select(Module)
        .where(Module.course_id == course_id, Module.is_published.is_(True))
        .options(
            selectinload(
                Module.sections.and_(Section.is_published.is_(True))
            ).selectinload(
                Section.items,
            ),
        )
        .order_by(Module.order_index.asc())
    )
    result = await session.scalars(stmt)
    return result.all()


async def find_module_by_id(
    session: AsyncSession,
    *,
    module_id: uuid.UUID,
) -> Module | None:
    """Find a module by primary key UUID.

    Args:
        session: Active database session.
        module_id: Module UUID.

    Returns:
        Module entity if found, None otherwise.
    """
    stmt = select(Module).where(Module.id == module_id)
    return await session.scalar(stmt)


async def find_section_by_id(
    session: AsyncSession,
    *,
    section_id: uuid.UUID,
) -> Section | None:
    """Find a section by primary key UUID.

    Args:
        session: Active database session.
        section_id: Section UUID.

    Returns:
        Section entity if found, None otherwise.
    """
    stmt = select(Section).where(Section.id == section_id)
    return await session.scalar(stmt)


async def list_section_items(
    session: AsyncSession,
    *,
    section_id: uuid.UUID,
) -> Sequence[SectionItem]:
    """List all component items within a section ordered by index.

    Args:
        session: Active database session.
        section_id: Section UUID.

    Returns:
        Sequence of SectionItem entities.
    """
    stmt = (
        select(SectionItem)
        .where(SectionItem.section_id == section_id)
        .order_by(SectionItem.order_index.asc())
    )
    result = await session.scalars(stmt)
    return result.all()
