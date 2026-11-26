"""Application core module."""

from app.core.config import Settings, get_settings
from app.core.exceptions import (
    AppError,
    AuthenticationError,
    ConflictError,
    CourseNotFoundError,
    FeatureDisabledError,
    InvalidRequestError,
    LLMOutputError,
    LLMProviderError,
    LLMQuotaExceededError,
    LLMTimeoutError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitExceededError,
    TranscriptNotFoundError,
    UserInactiveError,
    build_error_body,
    register_exception_handlers,
)
from app.core.logging import get_logger, setup_logging

__all__ = [
    "AppError",
    "AuthenticationError",
    "ConflictError",
    "CourseNotFoundError",
    "FeatureDisabledError",
    "InvalidRequestError",
    "LLMOutputError",
    "LLMProviderError",
    "LLMQuotaExceededError",
    "LLMTimeoutError",
    "NotFoundError",
    "PermissionDeniedError",
    "RateLimitExceededError",
    "Settings",
    "TranscriptNotFoundError",
    "UserInactiveError",
    "build_error_body",
    "get_logger",
    "get_settings",
    "register_exception_handlers",
    "setup_logging",
]
