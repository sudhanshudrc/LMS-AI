"""Integration tests for repository query functions against database."""

import pytest

from app.db.repositories import (
    find_course_by_code,
    find_user_by_email,
    get_course_tree,
    list_published_courses,
    search_transcripts_fulltext,
)


@pytest.mark.asyncio
async def test_find_course_by_code_and_tree(db_session) -> None:
    """Verify finding a course by canonical code and retrieving its tree."""
    course = await find_course_by_code(db_session, course_code="CPP-101")
    assert course is not None
    assert course.course_id == "CPP-101"
    assert "C++" in course.title

    tree = await get_course_tree(db_session, course_id=course.id)
    assert len(tree) > 0
    assert len(tree[0].sections) > 0
    assert len(tree[0].sections[0].items) > 0


@pytest.mark.asyncio
async def test_list_published_courses(db_session) -> None:
    """Verify listing all published courses."""
    courses = await list_published_courses(db_session)
    assert len(courses) >= 5
    codes = [c.course_id for c in courses]
    assert "CPP-101" in codes
    assert "ML-201" in codes


@pytest.mark.asyncio
async def test_find_user_by_email(db_session) -> None:
    """Verify looking up seeded users by email."""
    admin_user = await find_user_by_email(db_session, email="admin@lms.local")
    assert admin_user is not None
    assert admin_user.role == "admin"


@pytest.mark.asyncio
async def test_search_transcripts_fulltext(db_session) -> None:
    """Verify PostgreSQL GIN full-text search across transcripts."""
    results = await search_transcripts_fulltext(
        db_session,
        query_text="operator",
        limit=5,
    )
    assert len(results) > 0
    transcript, rank = results[0]
    assert "operator" in transcript.full_text.lower()
    assert rank > 0.0
