"""Pydantic V2 request and response contracts for learner progress tracking."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.constants.enums import CompletionStatus


class PlaybackUpdateRequest(BaseModel):
    """Payload to update video playback progress."""

    position_seconds: int = Field(
        ..., ge=0, description="Current video playback position in seconds."
    )
    mark_completed: bool = Field(
        default=False,
        description="Whether this update also marks the video as completed.",
    )

    model_config = {
        "str_strip_whitespace": True,
        "json_schema_extra": {
            "examples": [
                {
                    "position_seconds": 345,
                    "mark_completed": False,
                }
            ]
        },
    }


class ItemProgressResponse(BaseModel):
    """Learner progress state for a specific section item."""

    section_item_id: uuid.UUID = Field(..., description="Section item UUID.")
    status: CompletionStatus = Field(
        ..., description="Completion status (not_started, in_progress, completed)."
    )
    last_playback_position_seconds: int = Field(
        default=0, ge=0, description="Video playback resume timestamp in seconds."
    )
    is_completed: bool = Field(..., description="Whether the item has been completed.")
    completed_at: datetime | None = Field(
        None, description="Completion timestamp (UTC)."
    )
    last_activity_at: datetime | None = Field(
        None, description="Last activity timestamp (UTC)."
    )


class ModuleProgressResponse(BaseModel):
    """Learner progress state for a module."""

    module_id: uuid.UUID = Field(..., description="Module UUID.")
    status: CompletionStatus = Field(..., description="Module completion status.")
    progress_percentage: Decimal = Field(
        ..., ge=0, le=100, description="Progress from 0.00 to 100.00."
    )
    completed_at: datetime | None = Field(
        None, description="Completion timestamp (UTC)."
    )


class CourseProgressResponse(BaseModel):
    """Aggregated course completion metrics for a learner."""

    course_id: uuid.UUID = Field(..., description="Course UUID.")
    total_items: int = Field(
        ..., ge=0, description="Total number of learning items in the course."
    )
    completed_items: int = Field(
        ..., ge=0, description="Number of items completed by the learner."
    )
    overall_percentage: Decimal = Field(
        ..., ge=0, le=100, description="Overall course progress percentage."
    )
    modules: list[ModuleProgressResponse] = Field(
        default_factory=list, description="Per-module breakdown of learner progress."
    )
