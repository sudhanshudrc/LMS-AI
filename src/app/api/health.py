"""Health check and service status endpoints."""

from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from app.api.v1.schemas.common import ApiResponse
from app.db.session import check_database_connection

router = APIRouter(prefix="/health", tags=["Health"])


class ServiceHealthResponse(BaseModel):
    """Health check status details."""

    status: str = Field(..., description="Service status indicator.")
    service: str = Field("lms-ai-api", description="Service identifier.")
    environment: str = Field(..., description="Application execution environment.")


class DatabaseHealthResponse(BaseModel):
    """Database connectivity status details."""

    database: str = Field(..., description="Database engine status.")
    pool_connected: bool = Field(
        ..., description="Whether database connection pool is operational."
    )


@router.get(
    "",
    summary="Service liveness probe",
    description="Returns basic health status of the API service.",
    status_code=status.HTTP_200_OK,
    response_model=ApiResponse[ServiceHealthResponse],
)
async def health_check() -> ApiResponse[ServiceHealthResponse]:
    """Return application liveness status."""
    return ApiResponse(
        data=ServiceHealthResponse(
            status="healthy",
            service="lms-ai-api",
            environment="production",
        ),
        message="Service is running healthy.",
    )


@router.get(
    "/db",
    summary="Database readiness probe",
    description="Executes a ping query against PostgreSQL connection pool to verify readiness.",
    status_code=status.HTTP_200_OK,
    response_model=ApiResponse[DatabaseHealthResponse],
    responses={
        500: {"description": "Database connection failed."},
    },
)
async def database_health_check() -> ApiResponse[DatabaseHealthResponse]:
    """Verify database connection pool readiness."""
    is_connected = await check_database_connection()
    return ApiResponse(
        data=DatabaseHealthResponse(
            database="connected" if is_connected else "disconnected",
            pool_connected=is_connected,
        ),
        message="Database connection verified successfully.",
    )
