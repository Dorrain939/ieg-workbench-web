from fastapi import APIRouter

from backend.services.artifact_service import ArtifactService

router = APIRouter(prefix="/projects/{project_id}/artifacts", tags=["platform-artifacts"])
service = ArtifactService()


@router.get("")
def list_artifacts(project_id: str):
    return service.list_artifacts(project_id)
