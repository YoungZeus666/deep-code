"""Agent factory: builds the orchestrator with specialized subagents."""

from __future__ import annotations

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


def create_coding_agent(config: AppConfig) -> CompiledStateGraph:
    """Create the main AI Deep Coder orchestrator agent.

    Supports native providers (anthropic, openai) and any OpenAI-compatible
    provider via the openai-like mode.
    """
    backend = LocalShellBackend(
        root_dir=config.workspace,
    )
    model = _build_chat_model(config)
    subagents = build_subagents(model)
    custom_tools = get_custom_tools()

    return create_deep_agent(
        model=model,
        system_prompt=ORCHESTRATOR_PROMPT,
        subagents=subagents,
        backend=backend,
        tools=custom_tools if custom_tools else None,
        name="ai-deep-coder",
    )
