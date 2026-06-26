class FunctionProjectService:
    def list_for_project(self, project: dict, function_id: str):
        items = project.get("function_projects") or {}
        if isinstance(items, dict):
            return items.get(function_id) or []
        return []
