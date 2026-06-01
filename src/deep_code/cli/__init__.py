"""CLI surface: interactive REPL, slash commands, plan mode.

Re-exports `main` so the pyproject entry point `deep_code.cli:main`
continues to resolve correctly.
"""
from deep_code.cli.app import main
from deep_code.cli.commands import (
    AgentCommandError,
    ExplicitAgentRequest,
    parse_agent_command,
    build_agent_routing_message,
)
from deep_code.cli.plan_mode import run_plan_mode

__all__ = [
    "main",
    "AgentCommandError", "ExplicitAgentRequest",
    "parse_agent_command", "build_agent_routing_message",
    "run_plan_mode",
]
