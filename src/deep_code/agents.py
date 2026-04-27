"""Agent factory: builds the orchestrator with specialized subagents."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from deepagents import SubAgent, create_deep_agent
from deepagents.backends import LocalShellBackend
from langchain_openai import ChatOpenAI
from langgraph.graph.state import CompiledStateGraph

from deep_code.collaboration import render_collaboration_playbook
from deep_code.config import AppConfig
from deep_code.prompts import (
    ORCHESTRATOR_PROMPT,
)
from deep_code.subagents import (
    build_subagents as build_registered_subagents,
    render_subagent_catalog,
)
from deep_code.tools import get_custom_tools


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
    """Create runtime subagent specifications from the built-in registry."""
    return build_registered_subagents(model)


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


_LANGUAGE_INSTRUCTIONS: dict[str, str] = {
    "zh": (
        "\n\n你必须使用中文（简体中文）回复用户。所有解释、总结和对话都应使用中文。"
        "代码本身保持英文，但代码注释和说明使用中文。"
    ),
    "en": (
        "\n\nYou MUST respond in English. All explanations, summaries, "
        "and conversation should be in English."
    ),
}


def _build_system_prompt(workspace: Path, language: str = "zh") -> str:
    """Build the full system prompt by combining the base prompt with
    AGENTS.md project context and skill definitions from skills/ and
    .agents/skills/.
    """
    parts: list[str] = [
        ORCHESTRATOR_PROMPT,
        render_subagent_catalog(),
        render_collaboration_playbook(),
    ]

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

    # Append language instruction to control the agent's output language
    parts.append(_LANGUAGE_INSTRUCTIONS.get(language, _LANGUAGE_INSTRUCTIONS["zh"]))

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
    system_prompt = _build_system_prompt(config.workspace, config.language)

    return create_deep_agent(
        model=model,
        system_prompt=system_prompt,
        subagents=subagents,
        backend=backend,
        tools=custom_tools if custom_tools else None,
        name="deep-code",
    )
