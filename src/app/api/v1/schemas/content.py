"""Pydantic V2 request and response contracts for content and transcripts."""

import uuid
from typing import Any

from pydantic import BaseModel, Field

from app.constants.enums import ContentComponentType


class TimedCue(BaseModel):
    """Timed subtitle cue in a lecture transcript."""

    start: float = Field(..., ge=0.0, description="Start timestamp in seconds.")
    end: float = Field(..., ge=0.0, description="End timestamp in seconds.")
    text: str = Field(..., description="Subtitle or spoken dialogue segment.")


class VideoContentResponse(BaseModel):
    """Video learning item content payload."""

    id: uuid.UUID = Field(..., description="Video content unique UUID.")
    section_item_id: uuid.UUID = Field(..., description="Parent section item UUID.")
    video_url: str = Field(..., description="URL of the lecture video stream.")
    youtube_video_id: str | None = Field(
        None, description="YouTube identifier if applicable."
    )
    duration_seconds: int = Field(..., ge=0, description="Duration in seconds.")
    thumbnail_url: str | None = Field(None, description="Video thumbnail image URL.")


class TextContentResponse(BaseModel):
    """Reading / Markdown learning item content payload."""

    id: uuid.UUID = Field(..., description="Text content unique UUID.")
    section_item_id: uuid.UUID = Field(..., description="Parent section item UUID.")
    body_markdown: str = Field(..., description="Markdown reading text body.")
    estimated_read_time_seconds: int = Field(
        ..., ge=0, description="Estimated read duration."
    )


class ItemContentResponse(BaseModel):
    """Polymorphic container for section item content."""

    item_id: uuid.UUID = Field(..., description="Section item UUID.")
    title: str = Field(..., description="Section item title.")
    content_type: ContentComponentType = Field(
        ..., description="Type of component (video or text)."
    )
    video: VideoContentResponse | None = Field(
        None, description="Video details if video-type item."
    )
    text: TextContentResponse | None = Field(
        None, description="Text reading details if text-type item."
    )


class TranscriptResponse(BaseModel):
    """Complete lecture transcript payload with timed cue dialogue."""

    id: uuid.UUID = Field(..., description="Transcript record UUID.")
    video_content_id: uuid.UUID = Field(
        ..., description="Associated video content UUID."
    )
    language_code: str = Field("en", description="Language ISO code.")
    full_text: str = Field(..., description="Full raw transcript text.")
    timed_cues: list[dict[str, Any]] = Field(
        default_factory=list, description="Array of timed cue entries."
    )
    vtt_content: str | None = Field(
        None, description="Raw WebVTT format content if available."
    )


class TranscriptSearchResult(BaseModel):
    """Result item from full-text search across transcripts."""

    transcript_id: uuid.UUID = Field(
        ..., description="Matching transcript record UUID."
    )
    video_content_id: uuid.UUID = Field(
        ..., description="Associated video content UUID."
    )
    language_code: str = Field(..., description="Language ISO code.")
    snippet: str = Field(..., description="Excerpt showing search keyword context.")
    rank: float = Field(..., description="PostgreSQL full-text search relevance score.")
