"""HTTP request observability middleware recording latency, status, and correlation IDs."""

import time
import uuid

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.logging import get_logger

logger = get_logger("app.middleware.request_logging")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs incoming HTTP requests, response status, duration, and binds correlation ID."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Process HTTP request through correlation and duration tracking."""
        # 1. Resolve or generate correlation ID
        correlation_id = request.headers.get("X-Correlation-Id") or str(uuid.uuid4())

        # 2. Bind correlation ID and HTTP context into structlog contextvars
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            correlation_id=correlation_id,
            method=request.method,
            path=request.url.path,
        )

        start_time = time.perf_counter()

        try:
            response = await call_next(request)
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

            # Attach correlation ID to response headers
            response.headers["X-Correlation-Id"] = correlation_id

            # Skip noisy logs for health check probes
            if not request.url.path.startswith("/health"):
                logger.info(
                    "http_request_completed",
                    status_code=response.status_code,
                    duration_ms=duration_ms,
                )

            return response
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.exception(
                "http_request_failed",
                duration_ms=duration_ms,
                error=str(exc),
            )
            raise
        finally:
            structlog.contextvars.clear_contextvars()
