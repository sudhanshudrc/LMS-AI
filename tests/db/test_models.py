"""Unit tests for SQLAlchemy models and metadata completeness."""

from app.constants.enums import UserRole
from app.db.models import (
    Base,
    Course,
    User,
)


def test_models_metadata_registration() -> None:
    """Verify that all ORM entities are registered on Base.metadata."""
    tables = Base.metadata.tables
    expected_tables = {
        "users",
        "courses",
        "course_prerequisites",
        "modules",
        "sections",
        "section_items",
        "item_video_contents",
        "item_text_contents",
        "video_transcripts",
        "user_module_completions",
        "user_item_completions",
    }
    for table_name in expected_tables:
        assert table_name in tables, f"Table {table_name} missing from Base.metadata"


def test_user_model_instantiation() -> None:
    """Verify User model attributes and enum defaults."""
    user = User(
        email="test@lms.local",
        password_hash="hashed_pw",
        full_name="Test User",
        role=UserRole.USER,
        is_active=True,
    )
    assert user.email == "test@lms.local"
    assert user.role == UserRole.USER
    assert user.is_active is True


def test_course_model_instantiation() -> None:
    """Verify Course model attributes and defaults."""
    course = Course(
        org="Neso Academy",
        course_id="TEST-101",
        title="Test Course",
        language="en",
        is_published=True,
    )
    assert course.org == "Neso Academy"
    assert course.course_id == "TEST-101"
    assert course.is_published is True
