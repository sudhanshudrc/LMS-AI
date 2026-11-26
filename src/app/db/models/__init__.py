"""ORM models registry.

Importing this package registers every table on `Base.metadata`.
"""

from app.db.models.base import Base, TimestampedModel
from app.db.models.content import ItemTextContent, ItemVideoContent, VideoTranscript
from app.db.models.course import Course, CoursePrerequisite
from app.db.models.curriculum import Module, Section, SectionItem
from app.db.models.progress import UserItemCompletion, UserModuleCompletion
from app.db.models.user import User

__all__ = [
    "Base",
    "Course",
    "CoursePrerequisite",
    "ItemTextContent",
    "ItemVideoContent",
    "Module",
    "Section",
    "SectionItem",
    "TimestampedModel",
    "User",
    "UserItemCompletion",
    "UserModuleCompletion",
    "VideoTranscript",
]
