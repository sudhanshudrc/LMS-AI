"""FastAPI main application entrypoint."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.v1.router import router as api_v1_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import get_logger, setup_logging
from app.core.middleware import RequestLoggingMiddleware

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown lifespan events."""
    settings = get_settings()
    is_production = settings.app_env == "production"
    setup_logging(log_level="INFO", json_format=is_production)
    logger.info("Starting LMS-AI Platform API...", app_env=settings.app_env)
    yield
    logger.info("Shutting down LMS-AI Platform API...")


app = FastAPI(
    title="LMS-AI Platform API",
    version="0.1.0",
    description="Backend API for LMS-AI course platform and student AI features",
    lifespan=lifespan,
)

# Global Exception Handlers
register_exception_handlers(app)

# Middlewares
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routes
app.include_router(health_router)
app.include_router(api_v1_router)
