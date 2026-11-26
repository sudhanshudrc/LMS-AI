"""FastAPI main application entrypoint."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown lifespan events."""
    yield


app = FastAPI(
    title="LMS-AI Platform API",
    version="0.1.0",
    description="Backend API for LMS-AI course platform and student AI features",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Basic health check endpoint."""
    return {"status": "healthy", "service": "lms-ai-api"}
