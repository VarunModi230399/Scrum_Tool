from fastapi import APIRouter

from src.modules.identity.api.auth_router import router as auth_router
from src.modules.identity.api.organizations_router import router as organizations_router
from src.modules.identity.api.workspaces_router import router as workspaces_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(organizations_router)
router.include_router(workspaces_router)
