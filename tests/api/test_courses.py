"""Integration tests for Phase 2 course catalog and curriculum tree endpoints."""

import uuid

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import messages
from app.db.repositories.course_repository import list_published_courses
from app.db.session import get_db_session
from app.main import app


@pytest.mark.asyncio
async def test_list_published_courses_endpoint(db_session: AsyncSession) -> None:
    """Verify GET /api/v1/courses returns paginated courses wrapped in ApiResponse."""
    app.dependency_overrides[get_db_session] = lambda: db_session
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as async_client:
            response = await async_client.get("/api/v1/courses?limit=10&offset=0")
            assert response.status_code == 200
            body = response.json()
            assert body["success"] is True
            assert body["message"] == "Courses retrieved successfully."
            data = body["data"]
            assert "items" in data
            assert "pagination" in data
            assert len(data["items"]) >= 5
            assert data["pagination"]["limit"] == 10
            assert data["pagination"]["offset"] == 0
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_course_detail_by_code_and_uuid(db_session: AsyncSession) -> None:
    """Verify GET /api/v1/courses/{identifier} by canonical code and UUID."""
    app.dependency_overrides[get_db_session] = lambda: db_session
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as async_client:
            # By canonical code
            resp_code = await async_client.get("/api/v1/courses/CPP-101")
            assert resp_code.status_code == 200
            course = resp_code.json()["data"]
            assert course["course_id"] == "CPP-101"
            assert "Mastering C++" in course["title"]
            assert "prerequisites" in course

            course_uuid = course["id"]

            # By UUID
            resp_uuid = await async_client.get(f"/api/v1/courses/{course_uuid}")
            assert resp_uuid.status_code == 200
            assert resp_uuid.json()["data"]["id"] == course_uuid
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_course_detail_not_found(db_session: AsyncSession) -> None:
    """Verify GET /api/v1/courses/{identifier} returns 404 for non-existent course."""
    app.dependency_overrides[get_db_session] = lambda: db_session
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as async_client:
            response = await async_client.get(f"/api/v1/courses/{uuid.uuid4()}")
            assert response.status_code == 404
            assert response.json()["message"] == messages.COURSE_NOT_FOUND

            response_code = await async_client.get("/api/v1/courses/NON-EXISTENT-999")
            assert response_code.status_code == 404
            assert response_code.json()["message"] == messages.COURSE_NOT_FOUND
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_course_tree_endpoint(db_session: AsyncSession) -> None:
    """Verify GET /api/v1/courses/{course_id}/tree returns complete nested hierarchy."""
    app.dependency_overrides[get_db_session] = lambda: db_session
    try:
        courses = await list_published_courses(db_session, limit=1)
        assert len(courses) > 0
        target_course = courses[0]

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as async_client:
            response = await async_client.get(
                f"/api/v1/courses/{target_course.id}/tree"
            )
            assert response.status_code == 200
            tree = response.json()["data"]
            assert tree["id"] == str(target_course.id)
            assert tree["course_id"] == target_course.course_id
            assert len(tree["modules"]) > 0

            module = tree["modules"][0]
            assert "sections" in module
            assert len(module["sections"]) > 0

            section = module["sections"][0]
            assert "items" in section
            assert len(section["items"]) > 0
            assert section["items"][0]["content_type"] in ["video", "text"]
    finally:
        app.dependency_overrides.clear()
