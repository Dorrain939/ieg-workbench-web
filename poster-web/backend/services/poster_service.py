from backend.core.paths import POSTER_SKILL_ROOT


class PosterService:
    @property
    def skill_root(self):
        return POSTER_SKILL_ROOT

    def smoke_brief(self):
        return POSTER_SKILL_ROOT / "scripts" / "brief_ai-bootcamp-2026.json"
