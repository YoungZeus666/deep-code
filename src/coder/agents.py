"""Agent factory: builds the orchestrator with specialized subagents."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from deepagents import SubAgent, create_deep_agent
from deepagents.backends import LocalShellBackend
from langchain_openai import ChatOpenAI
from langgraph.graph.state import CompiledStateGraph

from coder.config import AppConfig
from coder.prompts import (
    BUG_FIXER_PROMPT,
    CODE_EXPLAINER_PROMPT,
    CODE_GENERATOR_PROMPT,
    CODE_REVIEWER_PROMPT,
    ORCHESTRATOR_PROMPT,
)
from coder.tools import get_custom_tools


def _build_chat_model(config: AppConfig) -> Any:
    """Build a chat model instance from config.

    Three modes:
      - anthropic → "anthropic:<model>" string, resolved by Deep Agents
      - openai    → "openai:<model>" string, resolved by Deep Agents
      - openai-like → ChatOpenAI instance with custom base_url and api_key,
        compatible with any OpenAI-like endpoint (Qwen, MiniMax, Kimi,
        DeepSeek, GLM, Doubao, Ollama, vLLM, LiteLLM, etc.).
    """
    if config.provider == "openai-like":
        return ChatOpenAI(
            model=config.model_name,
            base_url=config.base_url,
            api_key=config.api_key,
        )
    # Native provider — pass "provider:model" string for Deep Agents
    return f"{config.provider}:{config.model_name}"


def build_subagents(model: Any) -> list[SubAgent]:
    """Create the four specialized subagent specifications.

    Each subagent inherits the parent's filesystem and execute tools
    automatically. We only specify name, description, system_prompt,
    and model.
    """
    return [
        SubAgent(
            name="code-generator",
            description=(
                "Generates new code: functions, classes, modules, and full files. "
                "Use for any request to write or create new code."
            ),
            system_prompt=CODE_GENERATOR_PROMPT,
            model=model,
        ),
        SubAgent(
            name="code-reviewer",
            description=(
                "Reviews existing code for bugs, style issues, performance, "
                "and security. Use when user asks for code review or audit."
            ),
            system_prompt=CODE_REVIEWER_PROMPT,
            model=model,
        ),
        SubAgent(
            name="code-explainer",
            description=(
                "Reads and explains code in detail. Use when user asks "
                "'what does this do' or 'explain this code'."
            ),
            system_prompt=CODE_EXPLAINER_PROMPT,
            model=model,
        ),
        SubAgent(
            name="bug-fixer",
            description=(
                "Diagnoses and fixes bugs using a reproduce-diagnose-fix-verify cycle. "
                "Use when user reports a bug, test failure, or error."
            ),
            system_prompt=BUG_FIXER_PROMPT,
            model=model,
        ),
    ]


def _load_agents_md(workspace: Path) -> str | None:
    """Load AGENTS.md from the workspace if it exists."""
    agents_md = workspace / "AGENTS.md"
    if agents_md.is_file():
        try:
            return agents_md.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None
    return None


def _load_skills_from_dir(skills_dir: Path) -> list[tuple[str, str]]:
    """Load skills from a directory. Each skill is a subdirectory containing SKILL.md.

    Layout: skills_dir/skill-name/SKILL.md (+ optional references/*.md)
    Returns a list of (skill_name, content) tuples.
    """
    if not skills_dir.is_dir():
        return []

    skills: list[tuple[str, str]] = []
    for entry in sorted(skills_dir.iterdir()):
        if not entry.is_dir():
            continue
        skill_md = entry / "SKILL.md"
        if not skill_md.is_file():
            continue
        try:
            parts = [skill_md.read_text(encoding="utf-8", errors="replace")]
            refs_dir = entry / "references"
            if refs_dir.is_dir():
                for ref in sorted(refs_dir.iterdir()):
                    if ref.is_file() and ref.suffix == ".md":
                        ref_text = ref.read_text(encoding="utf-8", errors="replace")
                        parts.append(f"\n\n--- Reference: {ref.name} ---\n\n{ref_text}")
            skills.append((entry.name, "\n".join(parts)))
        except OSError:
            continue
    return skills


def _load_all_skills(workspace: Path) -> list[tuple[str, str]]:
    """Load skills from both skills/ and .agents/skills/ directories.

    Root-level skills/ is loaded first, then .agents/skills/.
    Duplicates (same name) are kept — both are included.
    """
    skills: list[tuple[str, str]] = []
    skills.extend(_load_skills_from_dir(workspace / "skills"))
    skills.extend(_load_skills_from_dir(workspace / ".agents" / "skills"))
    return skills


def _build_system_prompt(workspace: Path) -> str:
    """Build the full system prompt by combining the base prompt with
    AGENTS.md project context and skill definitions from skills/ and
    .agents/skills/.
    """
    parts: list[str] = [ORCHESTRATOR_PROMPT]

    # Load AGENTS.md as project context
    agents_md = _load_agents_md(workspace)
    if agents_md:
        parts.append(
            "\n\n--- Project Context (from AGENTS.md) ---\n\n"
            + agents_md
        )

    # Load skills from skills/ and .agents/skills/
    skills = _load_all_skills(workspace)
    if skills:
        parts.append("\n\n--- Available Skills ---\n")
        for name, content in skills:
            parts.append(f"\n### Skill: {name}\n\n{content}")

    return "\n".join(parts)


def create_coding_agent(config: AppConfig) -> CompiledStateGraph:
    """Create the main Deep Code orchestrator agent.

    Automatically loads AGENTS.md and .agents/skills/ from the workspace
    to enrich the system prompt with project context and custom skills.
    """
    backend = LocalShellBackend(
        root_dir=config.workspace,
    )
    model = _build_chat_model(config)
    subagents = build_subagents(model)
    custom_tools = get_custom_tools()
    system_prompt = _build_system_prompt(config.workspace)

    return create_deep_agent(
        model=model,
        system_prompt=system_prompt,
        subagents=subagents,
        backend=backend,
        tools=custom_tools if custom_tools else None,
        name="deep-code",
    )
