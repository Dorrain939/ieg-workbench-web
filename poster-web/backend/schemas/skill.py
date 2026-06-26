from dataclasses import dataclass


@dataclass
class SkillManifest:
    id: str
    label: str
    version: str = "1.0.0"
