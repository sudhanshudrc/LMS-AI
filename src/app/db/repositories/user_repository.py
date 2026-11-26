"""Queries for the `users` table."""

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import UserRole
from app.db.models.user import User


async def find_user_by_id(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
) -> User | None:
    """Find a single user by primary key ID.

    Args:
        session: Active database session.
        user_id: User UUID identifier.

    Returns:
        User model instance if found, None otherwise.
    """
    stmt = select(User).where(User.id == user_id)
    return await session.scalar(stmt)


async def find_user_by_email(
    session: AsyncSession,
    *,
    email: str,
) -> User | None:
    """Find a user by unique email address.

    Args:
        session: Active database session.
        email: Email to look up.

    Returns:
        User model instance if found, None otherwise.
    """
    stmt = select(User).where(User.email == email)
    return await session.scalar(stmt)


async def list_users(
    session: AsyncSession,
    *,
    role: UserRole | None = None,
    is_active: bool | None = None,
) -> Sequence[User]:
    """List users filtered optionally by role and active status.

    Args:
        session: Active database session.
        role: Optional role filter.
        is_active: Optional active status filter.

    Returns:
        Sequence of User entities.
    """
    stmt = select(User).order_by(User.created_at.desc())
    if role is not None:
        stmt = stmt.where(User.role == role)
    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)
    result = await session.scalars(stmt)
    return result.all()


def create_user(
    session: AsyncSession,
    *,
    email: str,
    password_hash: str,
    full_name: str,
    role: UserRole = UserRole.USER,
    is_active: bool = True,
) -> User:
    """Stage a new user record in the session without committing.

    Args:
        session: Active database session.
        email: User email.
        password_hash: Hashed password string.
        full_name: Full display name.
        role: User role.
        is_active: Initial account status.

    Returns:
        Staged User entity instance.
    """
    user = User(
        email=email,
        password_hash=password_hash,
        full_name=full_name,
        role=role,
        is_active=is_active,
    )
    session.add(user)
    return user
