"""Registry and helpers for built-in Deep Code subagents."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from deepagents import SubAgent

from deep_code.collaboration import CommitReport, FixReport, ReviewReport, TestReport
from deep_code.prompts import (
    BUG_FIXER_PROMPT,
    CODE_EXPLAINER_PROMPT,
    CODE_GENERATOR_PROMPT,
    CODE_REVIEWER_PROMPT,
    GIT_COMMITTER_PROMPT,
    TEST_WRITER_PROMPT,
)


@dataclass(frozen=True, slots=True)
class SubAgentSpec:
    """Declarative definition for a built-in subagent."""

    name: str
    description: str
    routing_hint: str
    system_prompt: str
    aliases: tuple[str, ...] = field(default_factory=tuple)
    response_format: Any | None = None

    def matches(self, candidate: str) -> bool:
        """Return True when candidate refers to this subagent."""
        normalized = candidate.strip().lower()
        return normalized == self.name or normalized in self.aliases


_SUBAGENT_SPECS: tuple[SubAgentSpec, ...] = (
    SubAgentSpec(
        name="code-generator",
        description=(
            "Generates new code: functions, classes, modules, and full files. "
            "Use for any request to write or create new code."
        ),
        routing_hint="Write or generate new implementation code.",
        system_prompt=CODE_GENERATOR_PROMPT,
        aliases=("generator",),
    ),
    SubAgentSpec(
        name="code-reviewer",
        description=(
            "Reviews existing code for bugs, style issues, performance, "
            "and security. Use when user asks for code review or audit."
        ),
        routing_hint="Review existing code for bugs, security, style, or performance.",
        system_prompt=CODE_REVIEWER_PROMPT,
        aliases=("reviewer",),
        response_format=ReviewReport,
    ),
    SubAgentSpec(
        name="code-explainer",
        description=(
            "Reads and explains code in detail. Use when user asks "
            "'what does this do' or 'explain this code'."
        ),
        routing_hint="Explain how existing code works.",
        system_prompt=CODE_EXPLAINER_PROMPT,
        aliases=("explainer",),
    ),
    SubAgentSpec(
        name="bug-fixer",
        description=(
            "Diagnoses and fixes bugs using a reproduce-diagnose-fix-verify cycle. "
            "Use when user reports a bug, test failure, or error."
        ),
        routing_hint="Diagnose and fix failing behavior, errors, or test failures.",
        system_prompt=BUG_FIXER_PROMPT,
        aliases=("fixer",),
        response_format=FixReport,
    ),
    SubAgentSpec(
        name="test-writer",
        description=(
            "Writes or updates automated tests for existing code. "
            "Use when the user asks for unit tests, regression tests, or coverage."
        ),
        routing_hint="Write or extend automated tests for existing code.",
        system_prompt=TEST_WRITER_PROMPT,
        aliases=("tester", "testwriter"),
        response_format=TestReport,
    ),
    SubAgentSpec(
        name="git-committer",
        description=(
            "Creates a git commit for verified task-related changes. "
            "Use after implementation and verification succeed."
        ),
        routing_hint="Create a git commit only after verification passes.",
        system_prompt=GIT_COMMITTER_PROMPT,
        aliases=("committer", "git-commit"),
        response_format=CommitReport,
    ),
)


def get_subagent_specs() -> list[SubAgentSpec]:
    """Return built-in subagent specs in display and routing order."""
    return list(_SUBAGENT_SPECS)


def get_subagent_names() -> list[str]:
    """Return the canonical names for all built-in subagents."""
    return [spec.name for spec in _SUBAGENT_SPECS]


def get_subagent_spec(name: str) -> SubAgentSpec | None:
    """Look up a built-in subagent spec by canonical name or alias."""
    for spec in _SUBAGENT_SPECS:
        if spec.matches(name):
            return spec
    return None


def build_subagents(model: Any) -> list[SubAgent]:
    """Build runtime SubAgent instances from the registry."""
    return [
        SubAgent(
            name=spec.name,
            description=spec.description,
            system_prompt=spec.system_prompt,
            model=model,
            response_format=spec.response_format,
        )
        for spec in _SUBAGENT_SPECS
    ]


def render_subagent_catalog() -> str:
    """Render the built-in subagent catalog for prompt injection."""
    lines = ["--- Available Built-in Subagents ---", ""]
    for spec in _SUBAGENT_SPECS:
        lines.append(f"- **{spec.name}**: {spec.routing_hint}")
    return "\n".join(lines)
