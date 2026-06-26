import json
from pathlib import Path

from backend.core.paths import PROJECTS_ROOT


class FileProjectRepository:
    def __init__(self, root: Path = PROJECTS_ROOT):
        self.root = root

    def list_ids(self):
        if not self.root.exists():
            return []
        return sorted([p.name for p in self.root.iterdir() if p.is_dir()])

    def read(self, project_id: str):
        path = self.root / project_id / "project.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def write(self, project_id: str, data: dict):
        target = self.root / project_id / "project.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return data
