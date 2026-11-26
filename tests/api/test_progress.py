"""Integration tests for Phase 4 learner progress tracking endpoints."""

import uuid

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import CompletionStatus, UserRole
from app.db.models.curriculum import SectionItem
from app.db.models.user import User
from app.db.repositories.course_repository import list_published_courses
from app.db.session import get_db_session
from app.main import app


@pytest.fixture
def mock_learner() -> User:
    """Fixture providing a mock learner user."""
    random_suffix = uuid.uuid4().hex[:8]
    return User(
        id=uuid.uuid4(),
        email=f"learner_{random_suffix}@test.local",
        password_hash="hash",
        full_name="Test Learner",
        role=UserRole.USER,
        is_active=True,
    )


@pytest.mark.asyncio
async def test_update_playback_and_complete_item(
    db_session: AsyncSession, mock_learner: User
) -> None:
    """Verify updating playback seconds and completing a section item."""
    db_session.add(mock_learner)
    await db_session.flush()

    # Find a valid section item
    stmt = select(SectionItem).limit(1)
    item = (await db_session.scalars(stmt)).first()
    assert item is not None
    item_id = item.id

    app.dependency_overrides[get_db_session] = lambda: db_session

    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
            headers={"X-User-Id": str(mock_learner.id)},
        ) as async_client:
            # 1. Update playback
            pb_resp = await async_client.post(
                f"/api/v1/progress/items/{item_id}/playback",
                json={"position_seconds": 120, "mark_completed": False},
            )
            assert pb_resp.status_code == 200
            pb_data = pb_resp.json()["data"]
            assert pb_data["section_item_id"] == str(item_id)
            assert pb_data["last_playback_position_seconds"] == 120
            assert pb_data["status"] == CompletionStatus.IN_PROGRESS.value
            assert pb_data["is_completed"] is False

            # 2. Mark completed
            comp_resp = await async_client.post(
                f"/api/v1/progress/items/{item_id}/complete"
            )
            assert comp_resp.status_code == 200
            comp_data = comp_resp.json()["data"]
            assert comp_data["section_item_id"] == str(item_id)
            assert comp_data["status"] == CompletionStatus.COMPLETED.value
            assert comp_data["is_completed"] is True
            assert comp_data["completed_at"] is not None
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_course_progress(
    db_session: AsyncSession, mock_learner: User
) -> None:
    """Verify calculating overall course progress and per-module breakdown."""
    db_session.add(mock_learner)
    await db_session.flush()

    courses = await list_published_courses(db_session, limit=1)
    assert len(courses) > 0
    course_id = courses[0].id

    app.dependency_overrides[get_db_session] = lambda: db_session

    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
            headers={"X-User-Id": str(mock_learner.id)},
        ) as async_client:
            resp = await async_client.get(f"/api/v1/progress/courses/{course_id}")
            assert resp.status_code == 200
            data = resp.json()["data"]
            assert data["course_id"] == str(course_id)
            assert data["total_items"] > 0
            assert isinstance(data["completed_items"], int)
            assert "overall_percentage" in data
            assert isinstance(data["modules"], list)
    finally:
        app.dependency_overrides.clear()
