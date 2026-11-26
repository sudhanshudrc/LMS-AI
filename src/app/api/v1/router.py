"""Master API v1 router definition."""

from fastapi import APIRouter

from app.api.v1.routes.courses import router as courses_router

router = APIRouter(prefix="/api/v1")

# Mount course catalog and curriculum endpoints
router.include_router(courses_router)
