"""HTTP endpoints for course catalog and curriculum tree exploration."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.common import ApiResponse, PaginatedResponse, PaginationParams
from app.api.v1.schemas.courses import (
    CourseDetailResponse,
    CourseSummaryResponse,
    CourseTreeResponse,
)
from app.api.v1.services import course_service
from app.constants import messages
from app.db.session import get_db_session

router = APIRouter(prefix="/courses", tags=["Courses"])

_COURSE_NOT_FOUND_RESPONSES: dict[int | str, dict[str, str]] = {
    404: {"description": messages.COURSE_NOT_FOUND},
}


@router.get(
    "",
    summary="List published courses",
    description="Returns a paginated list of published courses available for enrollment.",
    status_code=status.HTTP_200_OK,
    response_model=ApiResponse[PaginatedResponse[CourseSummaryResponse]],
)
async def list_published_courses_endpoint(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    offset: Annotated[int, Query(ge=0, description="Items to skip.")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Items per page.")] = 20,
) -> ApiResponse[PaginatedResponse[CourseSummaryResponse]]:
    """List published courses with offset pagination."""
    pagination = PaginationParams(offset=offset, limit=limit)
    paginated_courses = await course_service.list_courses(
        session, pagination=pagination
    )
    return ApiResponse(
        data=paginated_courses,
        message="Courses retrieved successfully.",
    )


@router.get(
    "/{identifier}",
    summary="Get course details",
    description="Retrieves single course metadata and prerequisites by UUID or canonical code.",
    status_code=status.HTTP_200_OK,
    response_model=ApiResponse[CourseDetailResponse],
    responses=_COURSE_NOT_FOUND_RESPONSES,
)
async def get_course_detail_endpoint(
    identifier: str,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[CourseDetailResponse]:
    """Retrieve course details by UUID or course code."""
    course_detail = await course_service.get_course_detail(
        session, identifier=identifier
    )
    return ApiResponse(
        data=course_detail,
        message="Course details retrieved successfully.",
    )


@router.get(
    "/{course_id}/tree",
    summary="Get course curriculum tree",
    description="Retrieves recursive hierarchical curriculum tree (Course -> Modules -> Sections -> Items).",
    status_code=status.HTTP_200_OK,
    response_model=ApiResponse[CourseTreeResponse],
    responses=_COURSE_NOT_FOUND_RESPONSES,
)
async def get_course_tree_endpoint(
    course_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[CourseTreeResponse]:
    """Retrieve complete nested curriculum tree for a course."""
    tree = await course_service.get_curriculum_tree(session, course_id=course_id)
    return ApiResponse(
        data=tree,
        message="Curriculum tree retrieved successfully.",
    )
