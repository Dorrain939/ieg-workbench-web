from fastapi import APIRouter

from backend.services.poster_service import PosterService

router = APIRouter(prefix="/poster", tags=["platform-poster"])
service = PosterService()


@router.get("/runtime")
def poster_runtime():
    return {"skill_root": str(service.skill_root), "smoke_brief": str(service.smoke_brief())}
