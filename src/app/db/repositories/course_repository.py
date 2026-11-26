"""Queries for the `courses` and `course_prerequisites` tables."""

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.course import Course, CoursePrerequisite


async def find_course_by_id(
    session: AsyncSession,
    *,
    course_id: uuid.UUID,
) -> Course | None:
    """Find a course by its primary key UUID.

    Args:
        session: Active database session.
        course_id: Course UUID.

    Returns:
        Course entity if found, None otherwise.
    """
    stmt = select(Course).where(Course.id == course_id)
    return await session.scalar(stmt)


async def find_course_by_code(
    session: AsyncSession,
    *,
    course_code: str,
) -> Course | None:
    """Find a course by its unique canonical course_id (e.g. 'CPP-101').

    Args:
        session: Active database session.
        course_code: Canonical course code string.

    Returns:
        Course entity if found, None otherwise.
    """
    stmt = select(Course).where(Course.course_id == course_code)
    return await session.scalar(stmt)


async def list_published_courses(
    session: AsyncSession,
    *,
    org: str | None = None,
    offset: int = 0,
    limit: int | None = None,
) -> Sequence[Course]:
    """List all published courses sorted by title.

    Args:
        session: Active database session.
        org: Optional organization filter.
        offset: Number of items to skip.
        limit: Optional maximum number of courses to return.

    Returns:
        Sequence of published Course entities.
    """
    stmt = (
        select(Course)
        .where(Course.is_published.is_(True))
        .order_by(Course.title.asc())
        .offset(offset)
    )
    if org is not None:
        stmt = stmt.where(Course.org == org)
    if limit is not None:
        stmt = stmt.limit(limit)
    result = await session.scalars(stmt)
    return result.all()


async def list_course_prerequisites(
    session: AsyncSession,
    *,
    course_id: uuid.UUID,
) -> Sequence[Course]:
    """Retrieve all prerequisite courses required for a given course.

    Args:
        session: Active database session.
        course_id: ID of the course requiring prerequisites.

    Returns:
        Sequence of prerequisite Course entities.
    """
    stmt = (
        select(Course)
        .join(
            CoursePrerequisite,
            Course.id == CoursePrerequisite.prerequisite_course_id,
        )
        .where(CoursePrerequisite.course_id == course_id)
        .order_by(Course.title.asc())
    )
    result = await session.scalars(stmt)
    return result.all()
