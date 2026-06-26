from fastapi import APIRouter, HTTPException

from backend.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["platform-projects"])
service = ProjectService()


@router.get("")
def list_projects():
    return service.list_projects()


@router.get("/{project_id}")
def get_project(project_id: str):
    data = service.get_project(project_id)
    if not data:
        raise HTTPException(404, "project not found")
    return data
