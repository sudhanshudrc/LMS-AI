"""Learner progress models: UserModuleCompletion and UserItemCompletion."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Computed,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    UniqueConstraint,
    func,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.constants.enums import CompletionStatus
from app.constants.tables import (
    MODULES_TABLE,
    SECTION_ITEMS_TABLE,
    USER_ITEM_COMPLETIONS_TABLE,
    USER_MODULE_COMPLETIONS_TABLE,
    USERS_TABLE,
)
from app.db.models.base import TimestampedModel


class UserModuleCompletion(TimestampedModel):
    """User-wise module completion record."""

    __tablename__ = USER_MODULE_COMPLETIONS_TABLE
    __table_args__ = (
        UniqueConstraint("user_id", "module_id", name="uq_user_module"),
        Index("idx_user_module_lookup", "user_id", "module_id"),
        Index("idx_user_module_status", "user_id", "status"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(f"{USERS_TABLE}.id", ondelete="CASCADE"),
        nullable=False,
    )
    module_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(f"{MODULES_TABLE}.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[CompletionStatus] = mapped_column(
        SQLEnum(
            CompletionStatus,
            name="completion_status",
            values_callable=lambda x: [e.value for e in x],
        ),
        default=CompletionStatus.NOT_STARTED,
        nullable=False,
    )
    progress_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class UserItemCompletion(TimestampedModel):
    """User-wise granular item completion and playback tracking."""

    __tablename__ = USER_ITEM_COMPLETIONS_TABLE
    __table_args__ = (
        UniqueConstraint("user_id", "section_item_id", name="uq_user_section_item"),
        Index("idx_user_item_comp_lookup", "user_id", "section_item_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(f"{USERS_TABLE}.id", ondelete="CASCADE"),
        nullable=False,
    )
    section_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(f"{SECTION_ITEMS_TABLE}.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[CompletionStatus] = mapped_column(
        SQLEnum(
            CompletionStatus,
            name="completion_status",
            values_callable=lambda x: [e.value for e in x],
        ),
        default=CompletionStatus.NOT_STARTED,
        nullable=False,
    )
    last_playback_position_seconds: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    is_completed: Mapped[bool] = mapped_column(
        Computed("status = 'completed'", persisted=True),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
