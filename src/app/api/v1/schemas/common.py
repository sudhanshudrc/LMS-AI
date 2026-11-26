"""Common Pydantic request and response schemas."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Standard unified API response envelope."""

    data: T = Field(..., description="Payload data returned by the operation.")
    success: bool = Field(default=True, description="Whether the request succeeded.")
    message: str = Field(
        default="Success", description="Human-readable response message."
    )
    errors: list[Any] | None = Field(
        default=None, description="Detailed validation or business errors."
    )

    def __init__(
        self,
        data: T,
        *,
        success: bool = True,
        message: str = "Success",
        errors: list[Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the API response envelope."""
        super().__init__(
            data=data,
            success=success,
            message=message,
            errors=errors,
            **kwargs,
        )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "data": {"status": "healthy"},
                    "message": "Operation completed successfully.",
                    "errors": None,
                }
            ]
        }
    }


class PaginationParams(BaseModel):
    """Standard offset pagination query parameters."""

    offset: int = Field(0, ge=0, description="Number of items to skip.")
    limit: int = Field(
        20, ge=1, le=100, description="Maximum number of items to return."
    )

    model_config = {
        "str_strip_whitespace": True,
        "json_schema_extra": {
            "examples": [
                {
                    "offset": 0,
                    "limit": 20,
                }
            ]
        },
    }


class PaginationMeta(BaseModel):
    """Pagination metadata included in paginated collection responses."""

    total_count: int = Field(..., ge=0, description="Total number of items available.")
    offset: int = Field(..., ge=0, description="Current offset in pagination.")
    limit: int = Field(..., ge=1, description="Current page size limit.")
    has_more: bool = Field(
        ..., description="Whether more items exist beyond this page."
    )


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated collection payload wrapper."""

    items: list[T] = Field(
        default_factory=list, description="List of items for the page."
    )
    pagination: PaginationMeta = Field(..., description="Pagination metadata.")
