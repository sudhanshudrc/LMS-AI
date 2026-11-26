"""Domain enumeration types."""

from enum import StrEnum


class UserRole(StrEnum):
    """User access control role."""

    USER = "user"
    ADMIN = "admin"


class ContentComponentType(StrEnum):
    """Section item component type."""

    TEXT = "text"
    VIDEO = "video"


class CompletionStatus(StrEnum):
    """User progress completion status."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
