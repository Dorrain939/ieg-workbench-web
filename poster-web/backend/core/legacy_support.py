"""Compatibility helpers for the pre-refactor application.

This module makes the migration explicit: old routes are still the source of
truth for established endpoints, while new code can depend on services under
backend/services.
"""

LEGACY_PROJECTS_ROUTER = "projects_api.router"
LEGACY_POSTER_ROUTER = "api.router"
LEGACY_CONFIG_ROUTER = "config_api.router"
LEGACY_KB_ROUTER = "kb_api.router"
