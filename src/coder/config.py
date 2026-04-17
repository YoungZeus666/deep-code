"""Configuration loading for AI Deep Coder."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Each provider has its own set of env vars. The system auto-detects
# which provider to use based on which MODEL var is set.
#
#   ANTHROPIC_MODEL + ANTHROPIC_API_KEY
#   OPENAI_MODEL    + OPENAI_API_KEY
#   OPENAI_LIKE_MODEL + OPENAI_LIKE_API_KEY + OPENAI_LIKE_BASE_URL


@dataclass
class AppConfig:
    """Application configuration resolved from environment."""

    provider: str = "anthropic"
    model_name: str = "claude-sonnet-4-20250514"
    workspace: Path = field(default_factory=Path.cwd)
    api_key: str | None = None
    base_url: str | None = None


def _detect_provider() -> tuple[str, str, str | None, str | None]:
    """Auto-detect which provider is configured.

    Checks env vars in order: OPENAI_LIKE_MODEL, OPENAI_MODEL, ANTHROPIC_MODEL.
    Returns (provider, model_name, api_key, base_url).
    """
    # OpenAI-Like (check first — most specific)
    model = os.environ.get("OPENAI_LIKE_MODEL")
    if model:
        api_key = os.environ.get("OPENAI_LIKE_API_KEY")
        base_url = os.environ.get("OPENAI_LIKE_BASE_URL")
        if not api_key:
            print(
                "Error: OPENAI_LIKE_API_KEY is required when OPENAI_LIKE_MODEL is set.\n"
                "Set it in your .env file or as an environment variable."
            )
            sys.exit(1)
        if not base_url:
            print(
                "Error: OPENAI_LIKE_BASE_URL is required when OPENAI_LIKE_MODEL is set.\n"
                "Example: OPENAI_LIKE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1"
            )
            sys.exit(1)
        return ("openai-like", model, api_key, base_url)

    # OpenAI
    model = os.environ.get("OPENAI_MODEL")
    if model:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print(
                "Error: OPENAI_API_KEY is required when OPENAI_MODEL is set.\n"
                "Set it in your .env file or as an environment variable."
            )
            sys.exit(1)
        return ("openai", model, None, None)

    # Anthropic (default)
    model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print(
            "Error: ANTHROPIC_API_KEY is required.\n"
            "Set it in your .env file or as an environment variable."
        )
        sys.exit(1)
    return ("anthropic", model, None, None)


def load_config() -> AppConfig:
    """Load configuration from environment variables and .env file."""
    load_dotenv()

    provider, model_name, api_key, base_url = _detect_provider()

    workspace_str = os.environ.get("AI_DEEP_CODER_WORKSPACE")
    workspace = Path(workspace_str) if workspace_str else Path.cwd()

    return AppConfig(
        provider=provider,
        model_name=model_name,
        workspace=workspace,
        api_key=api_key,
        base_url=base_url,
    )
