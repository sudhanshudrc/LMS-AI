"""User entity model."""

from sqlalchemy import Boolean, String, text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.constants.enums import UserRole
from app.constants.tables import USERS_TABLE
from app.db.models.base import TimestampedModel


class User(TimestampedModel):
    """User account entity representing learners and administrators."""

    __tablename__ = USERS_TABLE

    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(
            UserRole, name="user_role", values_callable=lambda x: [e.value for e in x]
        ),
        default=UserRole.USER,
        index=True,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=text("true"), nullable=False
    )
