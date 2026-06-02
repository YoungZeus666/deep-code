"""Foundational utilities: config, i18n, session persistence."""
from deep_code.core.config import (
    AppConfig,
    load_config,
    get_trusted_workspaces,
    add_trusted_workspace,
)
from deep_code.core.i18n import SUPPORTED_LANGUAGES, set_language, t, TRANSLATIONS
from deep_code.core.session import (
    SessionInfo,
    save_session,
    load_session,
    list_sessions,
    delete_session,
)

__all__ = [
    "AppConfig", "load_config", "get_trusted_workspaces", "add_trusted_workspace",
    "SUPPORTED_LANGUAGES", "set_language", "t", "TRANSLATIONS",
    "SessionInfo", "save_session", "load_session", "list_sessions", "delete_session",
]
