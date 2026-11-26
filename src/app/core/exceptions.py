"""Custom domain exceptions and unified FastAPI HTTP exception handlers."""

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.constants import messages
from app.core.logging import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Base Application Error
# ---------------------------------------------------------------------------
class AppError(Exception):
    """Base class for errors carrying a user-safe message and an HTTP status code."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_message: str = messages.INTERNAL_SERVER_ERROR

    def __init__(
        self,
        message: str | None = None,
        *,
        errors: Any = None,
    ) -> None:
        """Initialize the application error.

        Args:
            message: User-safe message; defaults to the class-level default_message.
            errors: Optional structured error details or field errors.
        """
        self.message: str = message or self.default_message
        self.errors: Any = errors
        super().__init__(self.message)


# ---------------------------------------------------------------------------
# Authentication & Authorization Errors
# ---------------------------------------------------------------------------
class AuthenticationError(AppError):
    """Credentials missing, invalid, or expired."""

    status_code = status.HTTP_401_UNAUTHORIZED
    default_message = messages.INVALID_SERVICE_TOKEN


class PermissionDeniedError(AppError):
    """User lacks required permissions or roles to perform the action."""

    status_code = status.HTTP_403_FORBIDDEN
    default_message = messages.PERMISSION_DENIED


class UserInactiveError(AppError):
    """User account is disabled or deactivated."""

    status_code = status.HTTP_403_FORBIDDEN
    default_message = messages.USER_INACTIVE


# ---------------------------------------------------------------------------
# Request & Business Validation Errors
# ---------------------------------------------------------------------------
class InvalidRequestError(AppError):
    """Request is syntactically well-formed but breaks domain validation."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_message = messages.REQUEST_VALIDATION_FAILED


class ConflictError(AppError):
    """Requested operation conflicts with current state (e.g., duplicate entity)."""

    status_code = status.HTTP_409_CONFLICT
    default_message = messages.USER_ALREADY_EXISTS


class RateLimitExceededError(AppError):
    """Client has sent too many requests in the current time window."""

    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_message = messages.RATE_LIMIT_EXCEEDED


class FeatureDisabledError(AppError):
    """The requested feature is turned off by configuration."""

    status_code = status.HTTP_403_FORBIDDEN
    default_message = messages.FEATURE_DISABLED


# ---------------------------------------------------------------------------
# Resource Errors
# ---------------------------------------------------------------------------
class NotFoundError(AppError):
    """Requested resource does not exist."""

    status_code = status.HTTP_404_NOT_FOUND
    default_message = messages.RESOURCE_NOT_FOUND


class CourseNotFoundError(NotFoundError):
    """Course with the specified identifier was not found."""

    default_message = messages.COURSE_NOT_FOUND


class TranscriptNotFoundError(NotFoundError):
    """Transcript for the requested lecture was not found."""

    default_message = messages.TRANSCRIPT_NOT_FOUND


# ---------------------------------------------------------------------------
# AI & LLM Engine Errors
# ---------------------------------------------------------------------------
class LLMTimeoutError(AppError):
    """AI model request timed out after retries."""

    status_code = status.HTTP_504_GATEWAY_TIMEOUT
    default_message = messages.LLM_TIMEOUT


class LLMProviderError(AppError):
    """External LLM provider returned an error or cannot be reached."""

    status_code = status.HTTP_502_BAD_GATEWAY
    default_message = messages.LLM_PROVIDER_ERROR


class LLMOutputError(AppError):
    """The LLM returned malformed, unparseable, or invalid structured output."""

    status_code = status.HTTP_502_BAD_GATEWAY
    default_message = messages.LLM_OUTPUT_INVALID


class LLMQuotaExceededError(AppError):
    """LLM provider rate limit or quota exceeded."""

    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_message = messages.LLM_QUOTA_EXCEEDED


# ---------------------------------------------------------------------------
# Error Response Envelope & Global Handlers
# ---------------------------------------------------------------------------
def build_error_body(message: str, errors: Any = None) -> dict[str, Any]:
    """Construct standard error envelope dictionary."""
    return {
        "success": False,
        "data": None,
        "message": message,
        "errors": errors,
    }


def _handle_app_error(_: Request, error: Exception) -> JSONResponse:
    """Handle custom AppError and its subclasses."""
    assert isinstance(error, AppError)
    return JSONResponse(
        status_code=error.status_code,
        content=build_error_body(error.message, error.errors),
    )


def _handle_validation_error(_: Request, error: Exception) -> JSONResponse:
    """Handle FastAPI / Pydantic RequestValidationError."""
    assert isinstance(error, RequestValidationError)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=build_error_body(messages.REQUEST_VALIDATION_FAILED, error.errors()),
    )


def _handle_http_error(_: Request, error: Exception) -> JSONResponse:
    """Handle framework StarletteHTTPException (404 route, 405 method)."""
    assert isinstance(error, StarletteHTTPException)
    return JSONResponse(
        status_code=error.status_code,
        content=build_error_body(str(error.detail)),
        headers=error.headers,
    )


def _handle_unexpected_error(request: Request, error: Exception) -> JSONResponse:
    """Handle uncaught exceptions with structured server-side logging."""
    logger.exception(
        "unhandled_exception",
        path=request.url.path,
        error=str(error),
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=build_error_body(messages.INTERNAL_SERVER_ERROR),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Attach the global exception handlers to the FastAPI app.

    Args:
        app: The FastAPI application instance.
    """
    app.add_exception_handler(AppError, _handle_app_error)
    app.add_exception_handler(RequestValidationError, _handle_validation_error)
    app.add_exception_handler(StarletteHTTPException, _handle_http_error)
    app.add_exception_handler(Exception, _handle_unexpected_error)
