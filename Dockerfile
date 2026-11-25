# syntax=docker/dockerfile:1
FROM postgres:16-alpine

LABEL maintainer="LMS-AI Project"
LABEL description="Clean PostgreSQL 16 container for LMS-AI"

# Standard PostgreSQL port
EXPOSE 5432

# Health check using pg_isready
HEALTHCHECK --interval=10s --timeout=5s --start-period=5s --retries=5 \
    CMD pg_isready -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-lms_db}" || exit 1
