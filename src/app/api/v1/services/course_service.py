"""Application service for course catalog and curriculum tree operations."""

import uuid
from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.common import (
    PaginatedResponse,
    PaginationMeta,
    PaginationParams,
)
from app.api.v1.schemas.courses import (
    CourseDetailResponse,
    CourseSummaryResponse,
    CourseTreeResponse,
    ModuleTreeResponse,
    PrerequisiteResponse,
    SectionItemSummaryResponse,
    SectionTreeResponse,
)
from app.core.exceptions import CourseNotFoundError
from app.db.models.course import Course
from app.db.repositories.course_repository import (
    find_course_by_code,
    find_course_by_id,
    list_course_prerequisites,
    list_published_courses,
)
from app.db.repositories.curriculum_repository import get_course_tree


async def list_courses(
    session: AsyncSession,
    *,
    pagination: PaginationParams,
) -> PaginatedResponse[CourseSummaryResponse]:
    """Retrieve paginated published courses.

    Args:
        session: Database session.
        pagination: Offset and limit parameters.

    Returns:
        PaginatedResponse wrapping CourseSummaryResponse items.
    """
    courses = await list_published_courses(
        session, offset=pagination.offset, limit=pagination.limit
    )

    items = [
        CourseSummaryResponse(
            id=c.id,
            org=c.org,
            course_id=c.course_id,
            title=c.title,
            subtitle=c.subtitle,
            duration=c.duration,
            effort=c.effort,
            language=c.language,
            short_description=c.short_description,
            is_published=c.is_published,
        )
        for c in courses
    ]

    has_more = len(items) == pagination.limit

    return PaginatedResponse(
        items=items,
        pagination=PaginationMeta(
            total_count=len(items),
            offset=pagination.offset,
            limit=pagination.limit,
            has_more=has_more,
        ),
    )


async def get_course_detail(
    session: AsyncSession,
    *,
    identifier: str,
) -> CourseDetailResponse:
    """Retrieve detailed course information by UUID or canonical code.

    Args:
        session: Database session.
        identifier: Course UUID string or canonical course_id (e.g. CPP-101).

    Returns:
        CourseDetailResponse with prerequisites.

    Raises:
        CourseNotFoundError: If no matching course exists.
    """
    course = None
    try:
        course_uuid = uuid.UUID(identifier)
        course = await find_course_by_id(session, course_id=course_uuid)
    except ValueError:
        course = await find_course_by_code(session, course_code=identifier)

    if not course:
        raise CourseNotFoundError()

    prereq_courses: Sequence[Course] = await list_course_prerequisites(
        session, course_id=course.id
    )

    prerequisites = [
        PrerequisiteResponse(course_id=p.id, code=p.course_id, title=p.title)
        for p in prereq_courses
    ]

    return CourseDetailResponse(
        id=course.id,
        org=course.org,
        course_id=course.course_id,
        title=course.title,
        subtitle=course.subtitle,
        duration=course.duration,
        effort=course.effort,
        language=course.language,
        short_description=course.short_description,
        description=course.description,
        overview=course.overview,
        start_date=course.start_date,
        end_date=course.end_date,
        is_published=course.is_published,
        prerequisites=prerequisites,
    )


async def get_curriculum_tree(
    session: AsyncSession,
    *,
    course_id: uuid.UUID,
) -> CourseTreeResponse:
    """Retrieve complete recursive curriculum tree for a course.

    Args:
        session: Database session.
        course_id: Course UUID.

    Returns:
        CourseTreeResponse with nested modules, sections, and items.

    Raises:
        CourseNotFoundError: If course does not exist.
    """
    course = await find_course_by_id(session, course_id=course_id)
    if not course:
        raise CourseNotFoundError()

    modules = await get_course_tree(session, course_id=course_id)

    module_responses: list[ModuleTreeResponse] = []
    for m in modules:
        section_responses: list[SectionTreeResponse] = []
        for s in m.sections:
            item_responses = [
                SectionItemSummaryResponse(
                    id=item.id,
                    title=item.title,
                    content_type=item.content_type,
                    order_index=item.order_index,
                )
                for item in s.items
            ]
            section_responses.append(
                SectionTreeResponse(
                    id=s.id,
                    title=s.title,
                    description=s.description,
                    order_index=s.order_index,
                    items=item_responses,
                )
            )
        module_responses.append(
            ModuleTreeResponse(
                id=m.id,
                title=m.title,
                description=m.description,
                order_index=m.order_index,
                sections=section_responses,
            )
        )

    return CourseTreeResponse(
        id=course.id,
        course_id=course.course_id,
        title=course.title,
        modules=module_responses,
    )
