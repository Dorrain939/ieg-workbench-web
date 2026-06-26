from fastapi import APIRouter

from .projects import router as projects_router
from .function_projects import router as function_projects_router
from .uploads import router as uploads_router
from .artifacts import router as artifacts_router
from .skills import router as skills_router
from .poster import router as poster_router
from .config import router as config_router
from .knowledge import router as knowledge_router

platform_router = APIRouter(prefix="/api/platform", tags=["platform"])
platform_router.include_router(projects_router)
platform_router.include_router(function_projects_router)
platform_router.include_router(uploads_router)
platform_router.include_router(artifacts_router)
platform_router.include_router(skills_router)
platform_router.include_router(poster_router)
platform_router.include_router(config_router)
platform_router.include_router(knowledge_router)
