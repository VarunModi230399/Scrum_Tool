from fastapi import APIRouter

from src.modules.projects.api.projects_router import router as projects_router
from src.modules.projects.api.work_items_router import router as work_items_router

router = APIRouter()
router.include_router(projects_router)
router.include_router(work_items_router)
