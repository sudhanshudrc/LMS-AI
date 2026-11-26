"""Curriculum structural models: Module, Section, and SectionItem."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.constants.enums import ContentComponentType
from app.constants.tables import (
    COURSES_TABLE,
    MODULES_TABLE,
    SECTION_ITEMS_TABLE,
    SECTIONS_TABLE,
)
from app.db.models.base import TimestampedModel

if TYPE_CHECKING:
    from app.db.models.content import ItemTextContent, ItemVideoContent
    from app.db.models.course import Course


class Module(TimestampedModel):
    """Module (chapter) within a course."""

    __tablename__ = MODULES_TABLE
    __table_args__ = (
        UniqueConstraint("course_id", "order_index", name="uq_course_module_order"),
        Index("idx_modules_course_order", "course_id", "order_index"),
    )

    course_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(f"{COURSES_TABLE}.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    course: Mapped["Course"] = relationship("Course", back_populates="modules")
    sections: Mapped[list["Section"]] = relationship(
        "Section",
        back_populates="module",
        cascade="all, delete-orphan",
        order_by="Section.order_index",
    )


class Section(TimestampedModel):
    """Section (topic) within a module."""

    __tablename__ = SECTIONS_TABLE
    __table_args__ = (
        UniqueConstraint("module_id", "order_index", name="uq_module_section_order"),
        Index("idx_sections_module_order", "module_id", "order_index"),
    )

    module_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(f"{MODULES_TABLE}.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    module: Mapped["Module"] = relationship("Module", back_populates="sections")
    items: Mapped[list["SectionItem"]] = relationship(
        "SectionItem",
        back_populates="section",
        cascade="all, delete-orphan",
        order_by="SectionItem.order_index",
    )


class SectionItem(TimestampedModel):
    """Ordered learning component item within a section."""

    __tablename__ = SECTION_ITEMS_TABLE
    __table_args__ = (
        UniqueConstraint("section_id", "order_index", name="uq_section_item_order"),
        Index("idx_section_items_section_order", "section_id", "order_index"),
    )

    section_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(f"{SECTIONS_TABLE}.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[ContentComponentType] = mapped_column(
        SQLEnum(
            ContentComponentType,
            name="content_component_type",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)

    section: Mapped["Section"] = relationship("Section", back_populates="items")
    video_content: Mapped["ItemVideoContent | None"] = relationship(
        "ItemVideoContent",
        back_populates="section_item",
        uselist=False,
        cascade="all, delete-orphan",
    )
    text_content: Mapped["ItemTextContent | None"] = relationship(
        "ItemTextContent",
        back_populates="section_item",
        uselist=False,
        cascade="all, delete-orphan",
    )
