from dataclasses import dataclass


@dataclass
class ProjectSummary:
    id: str
    name: str
    status: str = "active"
