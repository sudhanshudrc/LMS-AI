"""Content models: ItemVideoContent, ItemTextContent, and VideoTranscript."""

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.constants.tables import (
    ITEM_TEXT_CONTENTS_TABLE,
    ITEM_VIDEO_CONTENTS_TABLE,
    SECTION_ITEMS_TABLE,
    VIDEO_TRANSCRIPTS_TABLE,
)
from app.db.models.base import TimestampedModel

if TYPE_CHECKING:
    from app.db.models.curriculum import SectionItem


class ItemVideoContent(TimestampedModel):
    """Video content details for a video-type section item."""

    __tablename__ = ITEM_VIDEO_CONTENTS_TABLE

    section_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(f"{SECTION_ITEMS_TABLE}.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    video_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    youtube_video_id: Mapped[str | None] = mapped_column(
        String(64), index=True, nullable=True
    )
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    thumbnail_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    section_item: Mapped["SectionItem"] = relationship(
        "SectionItem",
        back_populates="video_content",
    )
    transcripts: Mapped[list["VideoTranscript"]] = relationship(
        "VideoTranscript",
        back_populates="video_content",
        cascade="all, delete-orphan",
    )


class VideoTranscript(TimestampedModel):
    """Transcript and timed cues for a video content item."""

    __tablename__ = VIDEO_TRANSCRIPTS_TABLE
    __table_args__ = (
        UniqueConstraint("video_content_id", "language_code", name="uq_video_language"),
        Index("idx_transcripts_video_lang", "video_content_id", "language_code"),
    )

    video_content_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(f"{ITEM_VIDEO_CONTENTS_TABLE}.id", ondelete="CASCADE"),
        nullable=False,
    )
    language_code: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    full_text: Mapped[str] = mapped_column(Text, nullable=False)
    timed_cues: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        default=list,
        server_default=text("'[]'::jsonb"),
        nullable=False,
    )
    vtt_content: Mapped[str | None] = mapped_column(Text, nullable=True)

    video_content: Mapped["ItemVideoContent"] = relationship(
        "ItemVideoContent",
        back_populates="transcripts",
    )


class ItemTextContent(TimestampedModel):
    """Text reading and Markdown study guide for a text-type section item."""

    __tablename__ = ITEM_TEXT_CONTENTS_TABLE

    section_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(f"{SECTION_ITEMS_TABLE}.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    body_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    estimated_read_time_seconds: Mapped[int] = mapped_column(
        Integer, default=180, nullable=False
    )

    section_item: Mapped["SectionItem"] = relationship(
        "SectionItem",
        back_populates="text_content",
    )
