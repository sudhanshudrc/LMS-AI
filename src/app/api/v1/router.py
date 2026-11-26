"""Master API v1 router definition."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1")

# Sub-routers for Phase 2-4 will be mounted here
# e.g., router.include_router(courses.router)
# e.g., router.include_router(content.router)
# e.g., router.include_router(progress.router)
