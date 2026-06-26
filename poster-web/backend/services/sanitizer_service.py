from projects_api import sanitize_rich_payload, sanitize_editor_json, sanitize_rich_html


class SanitizerService:
    sanitize_rich_payload = staticmethod(sanitize_rich_payload)
    sanitize_editor_json = staticmethod(sanitize_editor_json)
    sanitize_rich_html = staticmethod(sanitize_rich_html)
