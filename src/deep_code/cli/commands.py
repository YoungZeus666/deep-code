"""Helpers for explicit `/agent` command parsing."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ExplicitAgentRequest:
    """A parsed explicit agent request from the CLI."""

    agent_name: str
    task: str


class AgentCommandError(ValueError):
    """Raised when an `/agent` command cannot be parsed."""

    def __init__(self, code: str, detail: str | None = None) -> None:
        super().__init__(code)
        self.code = code
        self.detail = detail


def parse_agent_command(raw: str, available_names: list[str]) -> ExplicitAgentRequest:
    """Parse `/agent <name> <task>` into a structured request."""
    parts = raw.strip().split(maxsplit=2)
    if len(parts) < 2:
        raise AgentCommandError("missing_agent")

    agent_name = parts[1].strip().lower()
    if not agent_name:
        raise AgentCommandError("missing_agent")

    normalized_names = {name.lower() for name in available_names}
    if agent_name not in normalized_names:
        raise AgentCommandError("unknown_agent", agent_name)

    if len(parts) < 3 or not parts[2].strip():
        raise AgentCommandError("missing_task", agent_name)

    return ExplicitAgentRequest(agent_name=agent_name, task=parts[2].strip())


def build_agent_routing_message(agent_name: str, task: str) -> str:
    """Build a user message that strongly biases routing to one subagent."""
    return (
        "Use the specified subagent for this task unless it is clearly incapable of "
        "solving it.\n\n"
        f"Target subagent: {agent_name}\n"
        f"User task: {task}\n\n"
        "Prefer delegating via the task tool to the target subagent before handling "
        "the request directly or choosing a different subagent."
    )
