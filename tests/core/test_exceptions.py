"""Unit tests for custom exception handlers and error response envelopes."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.constants import messages
from app.core.exceptions import (
    AuthenticationError,
    CourseNotFoundError,
    InvalidRequestError,
    LLMTimeoutError,
    PermissionDeniedError,
    RateLimitExceededError,
    register_exception_handlers,
)


@pytest.fixture
def app_with_exceptions() -> FastAPI:
    """Create test FastAPI instance with registered exception handlers."""
    test_app = FastAPI()
    register_exception_handlers(test_app)

    @test_app.get("/test/auth-error")
    async def trigger_auth_error() -> None:
        raise AuthenticationError()

    @test_app.get("/test/course-not-found")
    async def trigger_course_not_found() -> None:
        raise CourseNotFoundError()

    @test_app.get("/test/custom-not-found")
    async def trigger_custom_not_found() -> None:
        raise CourseNotFoundError("Course CS-500 does not exist")

    @test_app.get("/test/invalid-request")
    async def trigger_invalid_request() -> None:
        raise InvalidRequestError(
            "Invalid parameters provided",
            errors=[{"field": "limit", "issue": "must be > 0"}],
        )

    @test_app.get("/test/permission-denied")
    async def trigger_permission_denied() -> None:
        raise PermissionDeniedError()

    @test_app.get("/test/rate-limit")
    async def trigger_rate_limit() -> None:
        raise RateLimitExceededError()

    @test_app.get("/test/llm-timeout")
    async def trigger_llm_timeout() -> None:
        raise LLMTimeoutError()

    @test_app.get("/test/unexpected")
    async def trigger_unexpected() -> None:
        raise RuntimeError("Something exploded behind the scenes")

    return test_app


def test_authentication_error_handler(app_with_exceptions: FastAPI) -> None:
    """Verify 401 response and envelope for AuthenticationError."""
    client = TestClient(app_with_exceptions)
    response = client.get("/test/auth-error")
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["data"] is None
    assert data["message"] == messages.INVALID_SERVICE_TOKEN


def test_not_found_error_handler_default_and_custom(
    app_with_exceptions: FastAPI,
) -> None:
    """Verify 404 response for CourseNotFoundError with default and custom messages."""
    client = TestClient(app_with_exceptions)

    resp1 = client.get("/test/course-not-found")
    assert resp1.status_code == 404
    assert resp1.json()["message"] == messages.COURSE_NOT_FOUND

    resp2 = client.get("/test/custom-not-found")
    assert resp2.status_code == 404
    assert resp2.json()["message"] == "Course CS-500 does not exist"


def test_invalid_request_with_errors(app_with_exceptions: FastAPI) -> None:
    """Verify 400 response with structured field error payload."""
    client = TestClient(app_with_exceptions)
    response = client.get("/test/invalid-request")
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["message"] == "Invalid parameters provided"
    assert data["errors"] == [{"field": "limit", "issue": "must be > 0"}]


def test_llm_timeout_handler(app_with_exceptions: FastAPI) -> None:
    """Verify 504 response for LLMTimeoutError."""
    client = TestClient(app_with_exceptions)
    response = client.get("/test/llm-timeout")
    assert response.status_code == 504
    assert response.json()["message"] == messages.LLM_TIMEOUT


def test_unexpected_error_handler(app_with_exceptions: FastAPI) -> None:
    """Verify 500 response masks internal error with safe user message."""
    client = TestClient(app_with_exceptions, raise_server_exceptions=False)
    response = client.get("/test/unexpected")
    assert response.status_code == 500
    data = response.json()
    assert data["success"] is False
    assert data["message"] == messages.INTERNAL_SERVER_ERROR
