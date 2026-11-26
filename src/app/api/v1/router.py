"""Master API v1 router definition."""

from fastapi import APIRouter

from app.api.v1.routes.content import router as content_router
from app.api.v1.routes.courses import router as courses_router
from app.api.v1.routes.progress import router as progress_router

router = APIRouter(prefix="/api/v1")

# Mount course catalog, curriculum, content, transcript, and progress endpoints
router.include_router(courses_router)
router.include_router(content_router)
router.include_router(progress_router)
