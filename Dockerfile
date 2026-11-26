# syntax=docker/dockerfile:1

# ----------------------------------------------------------------------------
# Stage 1: Build & install dependencies with uv
# ----------------------------------------------------------------------------
FROM ghcr.io/astral-sh/uv:0.5.21-python3.12-bookworm-slim AS builder

WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Copy dependency definition files first for layer caching
COPY pyproject.toml uv.lock ./

# Install production dependencies into a virtual environment
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# ----------------------------------------------------------------------------
# Stage 2: Minimal runtime image
# ----------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS runtime

WORKDIR /app

# Create a non-root application user
RUN groupadd -r -g 1001 appgroup && \
    useradd -r -u 1001 -g appgroup -s /sbin/nologin appuser

# Copy virtual environment from builder
COPY --from=builder --chown=appuser:appgroup /app/.venv /app/.venv

# Set environment paths so virtual environment binaries take precedence
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src:$PYTHONPATH"
ENV PYTHONUNBUFFERED=1

# Copy application source code
COPY --chown=appuser:appgroup src/ /app/src/

# Run as non-root user
USER appuser

EXPOSE 8000

# Health check
HEALTHCHECK --interval=10s --timeout=5s --start-period=5s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Start FastAPI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
