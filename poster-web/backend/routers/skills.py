from fastapi import APIRouter

from backend.services.skill_service import SkillService

router = APIRouter(prefix="/skills", tags=["platform-skills"])
service = SkillService()


@router.get("")
def list_skills():
    return service.list_frontend_skills()
