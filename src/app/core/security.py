"""Caller identity and security dependency models."""

import uuid
from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Header
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import messages
from app.constants.enums import UserRole
from app.core.exceptions import (
    AuthenticationError,
    PermissionDeniedError,
    UserInactiveError,
)
from app.db.repositories.user_repository import find_user_by_id
from app.db.session import get_db_session


class Caller(BaseModel):
    """Represents the authenticated user calling the API."""

    user_id: uuid.UUID = Field(..., description="Unique user identifier.")
    email: str = Field(..., description="User email address.")
    role: UserRole = Field(..., description="User role in the LMS platform.")
    is_active: bool = Field(True, description="Whether user account is active.")

    model_config = {
        "frozen": True,
        "json_schema_extra": {
            "examples": [
                {
                    "user_id": "0b6c9f2e-1d3a-4f6b-8a2c-5e7d9f1b3c4a",
                    "email": "student@lms.local",
                    "role": "student",
                    "is_active": True,
                }
            ]
        },
    }


async def get_current_caller(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    x_user_id: Annotated[
        str | None,
        Header(
            description="Authenticated User UUID (passed by gateway or dev environment).",
            alias="X-User-Id",
        ),
    ] = None,
) -> Caller:
    """Resolve caller identity from request context.

    Args:
        session: Database session.
        x_user_id: User identifier header.

    Returns:
        Validated Caller model.

    Raises:
        AuthenticationError: If header is missing or not a valid UUID, or user not found.
        UserInactiveError: If user account is inactive.
    """
    if not x_user_id:
        raise AuthenticationError(messages.UNAUTHORIZED_ACCESS)

    try:
        user_uuid = uuid.UUID(x_user_id)
    except ValueError as exc:
        raise AuthenticationError(messages.INVALID_SERVICE_TOKEN) from exc

    user = await find_user_by_id(session, user_id=user_uuid)
    if not user:
        raise AuthenticationError(messages.INVALID_SERVICE_TOKEN)

    if not user.is_active:
        raise UserInactiveError(messages.USER_INACTIVE)

    return Caller(
        user_id=user.id,
        email=user.email,
        role=UserRole(user.role),
        is_active=user.is_active,
    )


def require_role(*allowed_roles: UserRole) -> Callable[[Caller], Caller]:
    """Dependency factory restricting endpoint access to specific roles.

    Args:
        allowed_roles: Roles allowed to execute the endpoint.

    Returns:
        Dependency checker function.
    """

    def role_checker(caller: Annotated[Caller, Depends(get_current_caller)]) -> Caller:
        if caller.role not in allowed_roles:
            raise PermissionDeniedError(messages.PERMISSION_DENIED)
        return caller

    return role_checker
