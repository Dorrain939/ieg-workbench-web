from fastapi import APIRouter, HTTPException

from backend.services.function_project_service import FunctionProjectService
from backend.services.project_service import ProjectService

router = APIRouter(prefix="/projects/{project_id}/function-projects", tags=["platform-function-projects"])
project_service = ProjectService()
function_service = FunctionProjectService()


@router.get("/{function_id}")
def list_function_projects(project_id: str, function_id: str):
    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(404, "project not found")
    return function_service.list_for_project(project, function_id)
