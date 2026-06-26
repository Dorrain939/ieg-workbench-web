from backend.repositories.file_artifact_repo import FileArtifactRepository


class ArtifactService:
    def __init__(self, repo=None):
        self.repo = repo or FileArtifactRepository()

    def list_artifacts(self, project_id: str):
        return self.repo.list_artifacts(project_id)
