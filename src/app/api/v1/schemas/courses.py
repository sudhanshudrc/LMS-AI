"""Pydantic V2 request and response contracts for courses and curriculum."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.constants.enums import ContentComponentType


class PrerequisiteResponse(BaseModel):
    """Course prerequisite summary reference."""

    course_id: uuid.UUID = Field(..., description="Unique prerequisite course UUID.")
    code: str = Field(..., description="Canonical course code (e.g. CPP-101).")
    title: str = Field(..., description="Course title.")


class CourseSummaryResponse(BaseModel):
    """Course summary response for catalog listings."""

    id: uuid.UUID = Field(..., description="Unique course UUID.")
    org: str = Field(..., description="Organization or department offering the course.")
    course_id: str = Field(..., description="Canonical course code (e.g. DSA-201).")
    title: str = Field(..., description="Course title.")
    subtitle: str | None = Field(None, description="Course subtitle or tagline.")
    duration: str | None = Field(None, description="Estimated total course duration.")
    effort: str | None = Field(None, description="Weekly recommended effort.")
    language: str = Field("en", description="Course instruction language.")
    short_description: str | None = Field(
        None, description="Short summary of course objectives."
    )
    is_published: bool = Field(True, description="Whether course is published.")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "e69509e4-d4b3-4c89-a15c-c42cf12ea84d",
                    "org": "Self",
                    "course_id": "CPP-101",
                    "title": "Mastering C++ Programming: From Syntax to Memory Mastery",
                    "subtitle": "Complete guide to modern C++20",
                    "duration": "8 weeks",
                    "effort": "6 hours/week",
                    "language": "en",
                    "short_description": "Comprehensive journey into high-performance C++.",
                    "is_published": True,
                }
            ]
        }
    }


class CourseDetailResponse(CourseSummaryResponse):
    """Full course details including overview, description, and prerequisites."""

    description: str | None = Field(None, description="Detailed course description.")
    overview: str | None = Field(None, description="Curriculum and outcome overview.")
    start_date: datetime | None = Field(
        None, description="Course start date if scheduled."
    )
    end_date: datetime | None = Field(None, description="Course end date if scheduled.")
    prerequisites: list[PrerequisiteResponse] = Field(
        default_factory=list, description="List of prerequisite courses required."
    )


class SectionItemSummaryResponse(BaseModel):
    """Leaf learning item in a curriculum section."""

    id: uuid.UUID = Field(..., description="Unique section item UUID.")
    title: str = Field(..., description="Item title.")
    content_type: ContentComponentType = Field(
        ..., description="Component type (video or text)."
    )
    order_index: int = Field(..., ge=0, description="Display order within section.")


class SectionTreeResponse(BaseModel):
    """Section within a module containing learning items."""

    id: uuid.UUID = Field(..., description="Unique section UUID.")
    title: str = Field(..., description="Section title.")
    description: str | None = Field(None, description="Section description.")
    order_index: int = Field(..., ge=0, description="Display order within module.")
    items: list[SectionItemSummaryResponse] = Field(
        default_factory=list, description="Ordered learning items."
    )


class ModuleTreeResponse(BaseModel):
    """Module containing sections."""

    id: uuid.UUID = Field(..., description="Unique module UUID.")
    title: str = Field(..., description="Module title.")
    description: str | None = Field(None, description="Module description.")
    order_index: int = Field(..., ge=0, description="Display order within course.")
    sections: list[SectionTreeResponse] = Field(
        default_factory=list, description="Ordered sections."
    )


class CourseTreeResponse(BaseModel):
    """Complete recursive course curriculum tree."""

    id: uuid.UUID = Field(..., description="Unique course UUID.")
    course_id: str = Field(..., description="Canonical course code.")
    title: str = Field(..., description="Course title.")
    modules: list[ModuleTreeResponse] = Field(
        default_factory=list, description="Ordered curriculum modules."
    )
