from backend.core.paths import PROJECTS_ROOT


class FileArtifactRepository:
    def list_artifacts(self, project_id: str):
        project_file = PROJECTS_ROOT / project_id / "project.json"
        if not project_file.exists():
            return []
        import json
        data = json.loads(project_file.read_text(encoding="utf-8"))
        return data.get("artifacts") or []
