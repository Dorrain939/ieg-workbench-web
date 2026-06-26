import json

from backend.core.paths import STATIC_ROOT


class SkillService:
    def list_frontend_skills(self):
        path = STATIC_ROOT / "skills" / "registry.json"
        if not path.exists():
            return []
        return json.loads(path.read_text(encoding="utf-8"))
