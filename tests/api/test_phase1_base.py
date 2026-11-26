"""Unit tests for Phase 1 common schemas, security dependencies, and health routes."""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import messages
from app.constants.enums import UserRole
from app.core.exceptions import (
    AuthenticationError,
    PermissionDeniedError,
    UserInactiveError,
)
from app.core.security import Caller, get_current_caller, require_role
from app.db.models.user import User
from app.main import app

client = TestClient(app)


def test_health_check_endpoint() -> None:
    """Verify GET /health returns standard ApiResponse envelope."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "healthy"
    assert data["data"]["service"] == "lms-ai-api"
    assert data["errors"] is None


def test_database_health_check_endpoint() -> None:
    """Verify GET /health/db checks PostgreSQL connection pool."""
    response = client.get("/health/db")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["database"] == "connected"
    assert data["data"]["pool_connected"] is True


@pytest.mark.asyncio
async def test_caller_missing_header(db_session: AsyncSession) -> None:
    """Verify missing X-User-Id raises AuthenticationError (401)."""
    with pytest.raises(AuthenticationError) as exc_info:
        await get_current_caller(session=db_session, x_user_id=None)
    assert exc_info.value.message == messages.UNAUTHORIZED_ACCESS


@pytest.mark.asyncio
async def test_caller_invalid_uuid(db_session: AsyncSession) -> None:
    """Verify malformed UUID string raises AuthenticationError (401)."""
    with pytest.raises(AuthenticationError) as exc_info:
        await get_current_caller(session=db_session, x_user_id="invalid-uuid")
    assert exc_info.value.message == messages.INVALID_SERVICE_TOKEN


@pytest.mark.asyncio
async def test_caller_nonexistent_user(db_session: AsyncSession) -> None:
    """Verify non-existent user UUID raises AuthenticationError (401)."""
    random_uuid = str(uuid.uuid4())
    with pytest.raises(AuthenticationError) as exc_info:
        await get_current_caller(session=db_session, x_user_id=random_uuid)
    assert exc_info.value.message == messages.INVALID_SERVICE_TOKEN


@pytest.mark.asyncio
async def test_caller_inactive_user(db_session: AsyncSession) -> None:
    """Verify inactive user raises UserInactiveError (403)."""
    inactive_user = User(
        id=uuid.uuid4(),
        email="inactive@lms.local",
        password_hash="hash",
        full_name="Inactive Student",
        role=UserRole.USER,
        is_active=False,
    )
    db_session.add(inactive_user)
    await db_session.flush()

    with pytest.raises(UserInactiveError) as exc_info:
        await get_current_caller(session=db_session, x_user_id=str(inactive_user.id))
    assert exc_info.value.message == messages.USER_INACTIVE


def test_require_role_dependency() -> None:
    """Verify require_role allows specified roles and rejects others."""
    admin_caller = Caller(
        user_id=uuid.uuid4(),
        email="admin@lms.local",
        role=UserRole.ADMIN,
        is_active=True,
    )
    student_caller = Caller(
        user_id=uuid.uuid4(),
        email="student@lms.local",
        role=UserRole.USER,
        is_active=True,
    )

    admin_checker = require_role(UserRole.ADMIN)
    assert admin_checker(admin_caller) == admin_caller

    with pytest.raises(PermissionDeniedError) as exc_info:
        admin_checker(student_caller)
    assert exc_info.value.message == messages.PERMISSION_DENIED
