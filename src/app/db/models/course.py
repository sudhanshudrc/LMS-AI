"""Course and CoursePrerequisite entity models."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.constants.tables import COURSE_PREREQUISITES_TABLE, COURSES_TABLE
from app.db.models.base import Base, TimestampedModel

if TYPE_CHECKING:
    from app.db.models.curriculum import Module


class Course(TimestampedModel):
    """Educational course entity."""

    __tablename__ = COURSES_TABLE

    org: Mapped[str] = mapped_column(
        String(100), default="Self", index=True, nullable=False
    )
    course_id: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    subtitle: Mapped[str | None] = mapped_column(String(500), nullable=True)
    start_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    end_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    duration: Mapped[str | None] = mapped_column(String(100), nullable=True)
    effort: Mapped[str | None] = mapped_column(String(100), nullable=True)
    language: Mapped[str] = mapped_column(String(50), default="en", nullable=False)
    short_description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    overview: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_published: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=text("true"), nullable=False
    )

    modules: Mapped[list["Module"]] = relationship(
        "Module",
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="Module.order_index",
    )


class CoursePrerequisite(Base):
    """Normalized self-referencing prerequisite junction entity."""

    __tablename__ = COURSE_PREREQUISITES_TABLE
    __table_args__ = (
        UniqueConstraint(
            "course_id", "prerequisite_course_id", name="uq_course_prerequisite"
        ),
        CheckConstraint(
            "course_id <> prerequisite_course_id", name="chk_no_self_prerequisite"
        ),
        Index("idx_course_prereq_course", "course_id"),
        Index("idx_course_prereq_target", "prerequisite_course_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    course_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(f"{COURSES_TABLE}.id", ondelete="CASCADE"),
        nullable=False,
    )
    prerequisite_course_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(f"{COURSES_TABLE}.id", ondelete="RESTRICT"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
