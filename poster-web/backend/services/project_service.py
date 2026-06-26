from backend.repositories.file_project_repo import FileProjectRepository


class ProjectService:
    def __init__(self, repo=None):
        self.repo = repo or FileProjectRepository()

    def list_projects(self):
        return [p for p in (self.repo.read(pid) for pid in self.repo.list_ids()) if p]

    def get_project(self, project_id: str):
        return self.repo.read(project_id)
