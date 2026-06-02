"""Structured collaboration contracts for multi-agent orchestration."""

from __future__ import annotations

from pydantic import BaseModel, Field

__all__ = [
    "CommitReport",
    "FixReport",
    "ReviewFinding",
    "ReviewReport",
    "TestReport",
    "render_collaboration_playbook",
]


class ReviewFinding(BaseModel):
    """A single reviewer finding that downstream agents can consume."""

    severity: str = Field(description="CRITICAL, WARNING, or SUGGESTION")
    summary: str
    file_path: str | None = None
    suggested_fix: str | None = None


class ReviewReport(BaseModel):
    """Structured output returned by the reviewer agent."""

    summary: str
    findings: list[ReviewFinding]
    should_fix_before_commit: bool


class FixReport(BaseModel):
    """Structured output returned by the bug-fixer agent."""

    summary: str
    changed_files: list[str]
    unresolved_items: list[str]


class TestReport(BaseModel):
    """Structured output returned by the test-writer agent."""

    summary: str
    tests_added_or_updated: list[str]
    verification_commands: list[str]
    passed: bool


class CommitReport(BaseModel):
    """Structured output returned by the git-committer agent."""

    summary: str
    commit_created: bool
    commit_sha: str | None = None
    commit_message: str | None = None
    blocked_reason: str | None = None


def render_collaboration_playbook() -> str:
    """Render the orchestration rules for multi-agent collaboration."""

    return """--- Collaboration Playbook ---

Use collaboration mode automatically when the request contains independent work
that can run in parallel or when it naturally maps to a delivery pipeline.

Rules:
- Launch independent subagents in parallel whenever possible.
- Coordinate delivery as: generate -> review -> fix -> test -> commit.
- Pass structured results from each stage to the next stage as task context.
- Use bounded retry loops for review/fix and fix/test handoffs.
- Stop after retries are exhausted and summarize the blocking reason.
- Before commit, require passing verification and inspect `git status --porcelain`.
"""
